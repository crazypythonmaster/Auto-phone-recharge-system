import logging
import itertools
import traceback
from ppars.apps.core.check_customer_approve import CheckCustomerApprove
from ppars.apps.core.check_payment import CheckPayments
from ppars.apps.core.get_pin import GetPin
from ppars.apps.core import dealer_red_pocket
from ppars.apps.core.models import Transaction, UserProfile, CompanyProfile, \
    CarrierAdmin
from ppars.apps.core.recharge_phone import RechargePhone
from ppars.apps.core.send_notifications import SendNotifications, \
    failed_prerefill_company_notification, \
    successful_prerefill_customer_notification, \
    notification_about_wrong_transaction_pin


logger = logging.getLogger('ppars')


class PreRefill:
    def __init__(self, id):
        self.transaction = Transaction.objects.get(id=id)
        self.company = UserProfile.objects.get(user=self.transaction.user).company
        self.processes = ['check_payment', 'get_pin']
        # checking confirmation from customer
        self.transaction = CheckCustomerApprove(self.transaction.id).main()

    def main(self, **kwargs):
        content = ''
        try:
            if not self.transaction.locked and self.transaction.state != Transaction.COMPLETED:
                steps = itertools.chain(self.processes)
                if self.transaction.state == Transaction.RETRY:
                    steps_list = self.processes
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
                    'message': u'PreRefill transaction %s succeeded.' % self.transaction.id,
                }
                if self.transaction.state != Transaction.COMPLETED:
                    self.transaction.status = Transaction.SUCCESS
                    self.transaction.state = Transaction.INTERMEDIATE
                    self.transaction.adv_status = "PreRefill transaction ended successfully"
                    self.transaction.retry_count = 0
                    self.transaction.save()
                    if self.company.use_sellercloud and self.transaction.pin:
                        SendNotifications(self.transaction).send_sc_report()
                    successful_prerefill_customer_notification(self.transaction)
            else:
                content = {
                    'status': 'Error',
                    'message': u'PreRefill transaction %s already running or complete.' % self.transaction.id,
                }
        except Exception, msg:
            self.transaction.log_error_in_asana(msg)
            self.transaction.status = Transaction.ERROR
            content = {
                'status': 'Error',
                'message': u'PreRefill Error, cause is: "%s".' % msg,
            }
            self.transaction.adv_status = content['message']
            try:
                # Does transaction replays before?
                if self.transaction.retry_count:
                    # Does transaction has retries?
                    if self.transaction.retry_count >= (self.company.short_retry_limit):
                        # No retry, transaction close
                        self.transaction.state = Transaction.COMPLETED
                        self.transaction.retry_count = 0
                        self.transaction.save(update_fields=['status', 'adv_status', 'state', 'retry_count'])
                        self.transaction.add_transaction_step(self.transaction.current_step, 'retry_check', 'S', 'Transaction exceeded max retries, closing transaction')
                        if 'RedPocket' in self.transaction.plan_str \
                                and self.transaction.pin:
                            if not check_transaction_pin_of_redpokcet(self.transaction,
                                                                      self.transaction.company,
                                                                      self.transaction.pin):
                                failed_prerefill_company_notification(self.transaction)
                        else:
                            failed_prerefill_company_notification(
                                self.transaction)

                    else:
                        # Has retries
                        self.transaction.state = Transaction.RETRY
                        self.transaction.retry_count = self.transaction.retry_count + 1
                else:
                    # Transaction never replays before
                    self.transaction.state = Transaction.RETRY
                    self.transaction.retry_count = 1
                # retry current transaction
                if self.transaction.state == Transaction.RETRY:
                    retry_interval = self.company.short_retry_interval
                    if 'Please login to the Dollarphone and enter digit token.' in self.transaction.adv_status:
                        retry_interval = 30
                    from tasks import queue_prerefill
                    queue_prerefill.apply_async(args=[self.transaction.id], countdown=60*retry_interval)
                    self.transaction.retry_interval = retry_interval * 60
                    self.transaction.add_transaction_step(self.transaction.current_step, 'retry_check', 'S', 'Transaction erred out, will be retried in %s minutes.' % retry_interval)
            except Exception, msg:
                self.transaction.add_transaction_step(self.transaction.current_step, 'retry_check', 'E', u'Retry Check failed, cause is: "%s".' % msg)
        finally:
            self.transaction.locked = False
            self.transaction.save(update_fields=['locked', 'status', 'adv_status', 'retry_count', 'state'])
            return content

    def check_payment(self):
        self.transaction = CheckPayments(self.transaction.id).main()

    def get_pin(self):
        self.transaction = GetPin(self.transaction.id).main()


def check_transaction_pin_of_redpokcet(transaction, company, pin):
    status = False
    try:
        carrier_admin = CarrierAdmin.objects.filter(company=company,
                                                    carrier__name__icontains='RED POCKET')
        answer = dealer_red_pocket.log_in_red_pocket(carrier_admin)
        result = dealer_red_pocket.get_pin_status(pin, answer['session'])
        if result['status']:
            notification_about_wrong_transaction_pin(transaction,
                                                     company.company_name,
                                                     company.email_id,
                                                     result['status_pin'])
            status = True
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
    finally:
        return status