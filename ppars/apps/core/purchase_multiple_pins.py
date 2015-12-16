import logging
import traceback
from models import AutoRefill, UnusedPin, Customer, SUCCESS, ERROR
from get_pin import GetPin
from dollarphone_mk_charge import MakeDollarPhoneCharge

logger = logging.getLogger('ppars')

STEP_MULTIPLE_PINS = 'multiple_pins'


class MultiplePins:

    def __init__(self, transaction):
        self.transaction = transaction
        self.autorefill = self.transaction.autorefill
        self.company = self.transaction.company
        self.customer = self.transaction.customer
        self.transaction.current_step = STEP_MULTIPLE_PINS

        self.GetPin = GetPin(self.transaction.id)

    def main(self):
        """
        count_pins - quantity of pins which system should buy
        """
        try:
            plan = self.GetPin.is_plan_available()

            if self.transaction.autorefill.trigger == AutoRefill.TRIGGER_SC:
                count_pins = 0
            else:
                count_pins = self.transaction.autorefill.need_buy_pins_count - self.transaction.bought_pins

            if not self.GetPin.check_is_not_top_up_plan_use_for_get_pin_operations() and \
                    (self.autorefill.need_buy_pins or self.check_able_to_purchase_pins()) and count_pins:

                if not self.company.dollar_user or not self.company.dollar_pass:
                    raise Exception('DollarPhone account is missing in company.'
                                    ' Please correct account to proceed')

                self.transaction.add_transaction_step(self.transaction.current_step,
                                                      'begin', SUCCESS,
                                                      'Buying %s pins ' % count_pins)

                for i in range(0, count_pins):
                    if self.customer.charge_getaway == Customer.DOLLARPHONE:
                        dp_charge = MakeDollarPhoneCharge(self.transaction).charging()

                        pin = dp_charge.pin
                    else:
                        pin = self.purchased_pin(plan)

                    if self.autorefill.need_buy_pins:
                        unused_pin = UnusedPin.objects.create(
                            user=self.transaction.user,
                            company=self.transaction.company,
                            plan=plan,
                            pin=str(pin),
                            used=False,
                            notes='Pin bought from transaction %s' % self.transaction.get_full_url())
                        self.transaction.add_transaction_step(
                            self.transaction.current_step,
                            'has bought pin',
                            SUCCESS,
                            'Purchased pin <a href="%s">%s</a> and added to '
                            'unused' % (unused_pin.get_full_url(), str(unused_pin.id))
                        )
                    else:
                        if not self.transaction.pin:
                            self.transaction.pin = pin
                        else:
                            self.transaction.pin = '%s, %s' % (self.transaction.pin, pin)
                    #     msg = 'Purchased pin %s' % pin
                    #
                    # self.transaction.add_transaction_step(self.transaction.current_step,
                    #                                       'purchased', SUCCESS, msg)

                    self.transaction.bought_pins += 1
                    self.transaction.save(update_fields=['bought_pins'])

                self.transaction.add_transaction_step(self.transaction.current_step,
                                                      'end', SUCCESS,
                                                      'Bought %s pins of %s' %
                                                      (self.transaction.bought_pins, count_pins))
                self.transaction.paid = True

        except Exception, e:
            logger.error('Exception: %s. Trace: %s.' % (e, traceback.format_exc(limit=10)))
            self.transaction.add_transaction_step(self.transaction.current_step, 'end', ERROR, '%s' % e)
            raise Exception(e)
        finally:
            self.transaction.save()

        return self.transaction

    def check_able_to_purchase_pins(self):
        if self.autorefill.trigger == AutoRefill.TRIGGER_MN and self.autorefill.refill_type == AutoRefill.REFILL_GP:
            return True
        return False

    def purchased_pin(self, plan):
        if self.company.dollar_type == 'A':
            response = self.GetPin.dollarphone_api_request(plan)
        else:
            response = self.GetPin.dollarphone_site_request(plan)
        logger.debug('DP reciept %s %s' % (self.transaction.id, response['receipt_id']))
        if not response['status']:
            raise Exception('%s' % response['adv_status'])
        self.transaction.add_transaction_step('get pin', 'end', 'S', u'%s' % response['adv_status'])
        return response['pin']
