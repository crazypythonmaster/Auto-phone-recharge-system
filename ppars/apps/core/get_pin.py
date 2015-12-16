import logging
import traceback
from ppars.apps.core.models import Transaction, UserProfile, Plan, SUCCESS, ERROR
from django.core.urlresolvers import reverse
from ppars.apps.dollarphone import api,  site

logger = logging.getLogger('ppars')


class GetPin:

    def __init__(self, pk):
        self.transaction = Transaction.objects.get(id=pk)
        self.company = UserProfile.objects.get(user=self.transaction.user).company
        self.customer = self.transaction.customer
        self.transaction.current_step = 'get_pin'

    def main(self):
        try:
            if not self.transaction.pin and not self.check_is_not_top_up_plan_use_for_get_pin_operations():
                self.transaction.add_transaction_step('get pin', 'begin', SUCCESS, '')
                plan = self.is_plan_available()
                if not self.transaction.autorefill.need_buy_pins:
                    self.search_unused_pin(plan)
                if not self.transaction.pin:
                    if not self.company.dollar_user or not self.company.dollar_pass:
                        raise Exception("No unused pins found and DollarPhone "
                                        "account is missing in company. Please"
                                        " correct one of these to proceed")
                    # Get unused pin from dollarphonepinless if we don't have unused pin in system
                    self.transaction.add_transaction_step('get pin', 'unused pin', SUCCESS, 'No Unused pins found')
                    if self.company.dollar_type == 'A':
                        response = self.dollarphone_api_request(plan)
                    else:
                        response = self.dollarphone_site_request(plan)
                    logger.debug('DP reciept %s %s' % (self.transaction.id, response['receipt_id']))
                    if response['status']:
                        self.transaction.pin = response['pin']
                    else:
                        raise Exception("%s" % response['adv_status'])
                    self.transaction.add_transaction_step('get pin', 'end', SUCCESS, u'%s' % response['adv_status'])
                    if self.transaction.autorefill.need_buy_pins:
                        self.transaction.add_pin_to_unused(plan, response['pin'])
            # before return function goes to finally
            return self.transaction
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            self.transaction.add_transaction_step('get pin', 'end', ERROR, u'%s' % e)
            raise Exception(u'%s' % e)
        finally:
            self.transaction.save()

    def check_is_not_top_up_plan_use_for_get_pin_operations(self):
        # Top up plan can't be processed only for get pin
        if self.transaction.autorefill.plan.plan_type == Plan.DOMESTIC_TOPUP:
            if self.transaction.autorefill.refill_type == Plan.DOMESTIC_PIN:
                raise Exception("Get pin request created for a top up plan")
            return True
        return False

    def is_plan_available(self):
        # check is plan available
        plan = self.transaction.autorefill.plan
        self.transaction.add_transaction_step('get pin', 'check plan', SUCCESS, 'Check is plan %s available' % plan)
        if not plan.available or self.transaction.retry_count:
            if plan.universal_plan:
                plan = plan.universal_plan
                self.transaction.add_transaction_step('get pin', 'check plan', SUCCESS,
                                      'Plan not available. Used Universal plan %s' %
                                      plan.plan_id)
            elif self.transaction.retry_count:
                plan = plan
                self.transaction.add_transaction_step('get pin', 'check plan', SUCCESS,
                                      'Universal plan not setted. Used standart plan %s' %
                                      plan.plan_id)
            else:
                raise Exception('Plan not available and didn\'t have universal plan')
        return plan

    def search_unused_pin(self, plan):
        # Search unused pins in system
        self.transaction.add_transaction_step('get pin', 'unused pin', SUCCESS, 'Looking for unused pins')
        from tasks import get_unused_pin
        unused_pin = get_unused_pin(plan, self.company)
        if unused_pin:
            unused_pin.transaction = self.transaction
            unused_pin.save()
            self.transaction.pin = unused_pin.pin
            self.transaction.add_transaction_step('get pin',
                                                  'unused pin',
                                                  SUCCESS,
                                                  'Found unused pin <a href="%s">%s</a>' % (reverse('unusedpin_update', args=[unused_pin.id]), unused_pin.pin))

    def dollarphone_api_request(self, plan):
        self.transaction.add_transaction_step('get pin', 'api_begin', SUCCESS, 'Initializing the dollarphone API client')
        if not plan.api_id:
                raise Exception('API Id for this plan has not been updated, '
                                'please request the admin to update the plan with the API ID')
        form_fields = {
                'username': self.company.dollar_user,
                'password': self.company.dollar_pass,
                'OfferingId': plan.api_id,
                'company': self.company,
                'Amount': plan.plan_cost,
                'phone_number': None,
                'ProviderId': 0,
                'transaction': '%s' % self.transaction.id
        }
        return api.dp_api_request(form_fields)

    def dollarphone_site_request(self, plan):
        self.transaction.add_transaction_step('get pin', 'site_begin', SUCCESS, 'Initializing the  dollarphone Site client')
        form_fields = {
                'username': self.company.dollar_user,
                'password': self.company.dollar_pass,
                'Carrier': plan.carrier.name,
                'company': self.company,
                'Plan': plan.plan_name,
                'Amount': '$%s' % plan.plan_cost,
                'transaction': self.transaction,
        }
        return site.purchase_pin_cash(form_fields)
