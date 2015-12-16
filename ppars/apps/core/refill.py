import logging
import itertools
import pytz
from ppars.apps.core.check_customer_approve import CheckCustomerApprove
from ppars.apps.core.check_payment import CheckPayments
from ppars.apps.core.company_notifications import send_pin_error_mail
from ppars.apps.core.get_pin import GetPin
from ppars.apps.core.purchase_multiple_pins import MultiplePins, STEP_MULTIPLE_PINS
from ppars.apps.core.models import Transaction, AutoRefill
from ppars.apps.core.recharge_phone import RechargePhone
from ppars.apps.core.send_notifications import SendNotifications, failed_get_pin_error_token
from datetime import datetime
from pytz import timezone
from pytz import utc


logger = logging.getLogger('ppars')


class Refill:
    def __init__(self, id):
        self.transaction = Transaction.objects.get(id=id)
        self.company = self.transaction.company

        self.processes = {
            AutoRefill.REFILL_GP: ['check_payment', STEP_MULTIPLE_PINS, 'send_notifications'],
            AutoRefill.REFILL_FR: ['check_payment', 'get_pin', STEP_MULTIPLE_PINS, 'recharge_phone', 'send_notifications']
        }
        # checking confirmation from customer
        if not self.transaction.locked and self.transaction.state != Transaction.COMPLETED:
            self.transaction = CheckCustomerApprove(self.transaction.id).main()

    def main(self):
        content = ''
        try:
            if not self.transaction.locked and self.transaction.state != Transaction.COMPLETED:
                autorefill = self.transaction.autorefill
                if self.transaction.get_pin_now:
                    steps = itertools.chain(['check_payment', 'get_pin', STEP_MULTIPLE_PINS])
                else:
                    steps = itertools.chain(self.processes[autorefill.refill_type])
                if self.transaction.state == Transaction.RETRY:
                    steps_list = self.processes[autorefill.refill_type]
                    if not self.transaction.current_step:
                        self.transaction.current_step = 'check_payment'
                    for step in steps_list:
                        if step == self.transaction.current_step:
                            break
                        else:
                            next(steps)

                self.transaction.state = Transaction.PROCESS
                self.transaction.locked = True
                self.transaction.save()
                for step in steps:
                    if self.transaction.state == Transaction.COMPLETED:
                        break
                    self.transaction.current_step = step
                    getattr(self, step)()
                content = {
                    'status': 'Success',
                    'message': u'Autorefill transaction %s succeeded.' % self.transaction.id,
                }
                if autorefill.schedule == autorefill.AM_AND_ONE_MINUET_PM:
                    from ppars.apps.core.tasks import schedule_time_add_on
                    eastern_time_today = timezone('US/Eastern').localize(datetime.utcnow())
                    eastern_time = eastern_time_today.replace(hour=00, minute=01)
                    utc_datetime = eastern_time.astimezone(utc)
                    schedule_time_add_on.apply_async(args=[self.transaction.id], eta=utc_datetime)
                if self.transaction.state != Transaction.COMPLETED and not self.transaction.get_pin_now:
                    self.transaction.status = Transaction.SUCCESS
                    self.transaction.state = Transaction.COMPLETED
                    self.transaction.adv_status = "Autorefill transaction ended successfully"
                    self.transaction.save()
                    SendNotifications(self.transaction).send_statusmail()

                if self.transaction.autorefill.trigger == AutoRefill.TRIGGER_MN and \
                        self.transaction.autorefill.refill_type == AutoRefill.REFILL_GP and \
                        self.transaction.autorefill.send_bought_pins and \
                        not self.transaction.autorefill.need_buy_pins:
                    from send_notifications import send_pins_to_customer
                    send_pins_to_customer(self.transaction)

                if self.transaction.get_pin_now:
                    self.transaction.get_pin_now = False
                    self.transaction.current_step = 'recharge_phone'
                    self.transaction.state = Transaction.QUEUED

                    self.transaction.save(update_fields=['get_pin_now', 'current_step', 'state'])
                    self.transaction.add_transaction_step('get pin now',
                                                          'get pin',
                                                          Transaction.SUCCESS,
                                                          'Option "get pin now" is activated. Pin was got.'
                                                          ' Waiting to next execute.')

                    from tasks import queue_refill
                    queue_refill.apply_async(args=[self.transaction.id], eta=self.transaction.execution_time)

                today = datetime.now(pytz.timezone('US/Eastern')).date()
                # setting next renewal_date if date didn't set before
                if self.transaction.autorefill.trigger == AutoRefill.TRIGGER_SC and int(self.transaction.autorefill.renewal_date.strftime('%j')) - int(today.strftime('%j')) <= 1:
                    self.transaction.autorefill.set_renewal_date_to_next(today=self.transaction.autorefill.renewal_date)
            else:
                content = {
                    'status': 'Error',
                    'message': u'Autorefill transaction %s already running or complete.' % self.transaction.id,
                }
        except Exception, e:
            if 'used' in str(e).lower():
                self.transaction.retry_count = self.company.short_retry_limit + self.company.long_retry_limit
            self.transaction.log_error_in_asana(e)
            self.transaction.status = Transaction.ERROR
            content = {
                'status': 'Error',
                'message': u'Autorefill Error, cause is: "%s".' % e,
            }
            self.transaction.adv_status = content['message']
            try:
                if self.transaction.current_step != STEP_MULTIPLE_PINS:
                    # Have replays transactions before?
                    if self.transaction.retry_count:
                        if self.transaction.retry_count == self.company.short_retry_limit and \
                                        'used' in str(e).lower():
                            send_pin_error_mail(self.transaction, e)
                        # Does transaction has retries?
                        if self.transaction.retry_count >= (self.company.short_retry_limit + self.company.long_retry_limit):
                            # No retry, transaction close
                            self.transaction.state = Transaction.COMPLETED
                            self.transaction.save(update_fields=['status', 'adv_status', 'state'])
                            if self.company.use_sellercloud and self.transaction.pin:
                                SendNotifications(self.transaction).send_sc_report()
                            self.transaction.add_transaction_step(self.transaction.current_step, 'retry_check', 'S', 'Transaction exceeded max retries, closing transaction')
                            SendNotifications(self.transaction).send_statusmail()
                        else:
                            # Has retries
                            self.transaction.state = Transaction.RETRY
                            self.transaction.retry_count = self.transaction.retry_count + 1
                    else:
                        # Transaction never replays before
                        self.transaction.state = Transaction.RETRY
                        self.transaction.retry_count = 1
                else:
                    if 'Please login to the Dollarphone and enter digit token.' in str(e):
                        self.transaction.bought_pins_retry_count_err_token += 1
                    else:
                        self.transaction.bought_pins_retry_count += 1

                    if self.transaction.bought_pins_retry_count_err_token < 4 and \
                            self.transaction.bought_pins_retry_count <= 1:

                        self.transaction.state = Transaction.RETRY
                        self.transaction.save(update_fields=['state',
                                                             'status',
                                                             'bought_pins_retry_count_err_token',
                                                             'bought_pins_retry_count'])
                    else:
                        if 'Please login to the Dollarphone and enter digit token.' in str(e):
                            failed_get_pin_error_token(self.transaction)
                        else:
                            SendNotifications(self.transaction).send_statusmail()

                        self.transaction.state = Transaction.COMPLETED
                        self.transaction.status = Transaction.ERROR
                        self.transaction.save(update_fields=['state', 'status'])

                # retry current transaction
                if self.transaction.state == Transaction.RETRY:
                    retry_interval = self.company.short_retry_interval

                    if self.transaction.retry_count > self.company.short_retry_limit:
                        retry_interval = self.company.long_retry_interval
                    if 'Please login to the Dollarphone and enter digit token.' in self.transaction.adv_status:
                        retry_interval = 30
                    from .tasks import queue_refill
                    queue_refill.apply_async(args=[self.transaction.id], countdown=60*retry_interval)
                    self.transaction.retry_interval = retry_interval * 60
                    self.transaction.add_transaction_step(self.transaction.current_step,
                                                          'retry_check',
                                                          Transaction.SUCCESS,
                                                          'Transaction erred out, '
                                                          'will be retried in %s minutes.' % retry_interval)
            except Exception, msg:
                self.transaction.add_transaction_step(self.transaction.current_step, 'retry_check', 'E', u'Retry Check failed, cause is: "%s".' % msg)
        finally:
            logger.debug('transaction finally obj %s', self.transaction)
            self.transaction.locked = False
            self.transaction.save(update_fields=['locked', 'status', 'adv_status', 'retry_count', 'state', 'retry_interval'])
            if self.transaction.autorefill.trigger == 'SC':
                self.transaction.autorefill.last_renewal_status = self.transaction.get_status_display()
                self.transaction.autorefill.save()
            return content

    def check_payment(self):
        p = CheckPayments(self.transaction.id)
        self.transaction = p.main()
        # record payment type and getaway for transaction
        if self.transaction.autorefill and self.transaction.autorefill.customer:
            self.transaction.charge_type_name = self.transaction.autorefill.customer.get_charge_type_display()
            self.transaction.charge_getaway_name = self.transaction.autorefill.customer.get_charge_getaway_display()
            self.transaction.save()

    def get_pin(self):
        gp = GetPin(self.transaction.id)
        self.transaction = gp.main()

    def recharge_phone(self):
        r = RechargePhone(self.transaction.id)
        self.transaction = r.main()

    def send_notifications(self):
        n = SendNotifications(self.transaction)
        self.transaction = n.main()

    def multiple_pins(self):
        mp = MultiplePins(self.transaction)
        self.transaction = mp.main()
