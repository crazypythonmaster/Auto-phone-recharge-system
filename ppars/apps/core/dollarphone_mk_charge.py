__author__ = 'eugene'

import datetime
import pytz
import decimal

from models import SUCCESS, ERROR
from ppars.apps.charge.models import Charge, TransactionCharge


class MakeDollarPhoneCharge:

    def __init__(self, transaction):
        self.transaction = transaction
        self.company = self.transaction.company
        self.customer = self.transaction.customer

        self.cost, self.tax = self.transaction.cost_calculation()

        self.current_step = 'dp_charge'
        self.pin = ''
        self.charge = None

    def charging(self):

        charge = self.make_charge()

        charge.summ = self.cost
        charge.save()

        charge.add_charge_step(self.current_step, SUCCESS, 'Charge ended successfully')
        charge.add_charge_step(self.current_step,
                               SUCCESS,
                               '$%s from charge used for <a href="%s">%s</a>' %
                               (self.cost, self.transaction.get_full_url(), self.transaction.id))

        TransactionCharge.objects.get_or_create(charge=charge,
                                                transaction=self.transaction,
                                                defaults={'amount': decimal.Decimal(0.0)})
        self.pin = charge.pin
        self.charge = charge

        return self

    def make_charge(self):

        new_charge = self.get_previous_charge()

        if not new_charge:
            new_charge = self.find_unused_charge()

            if new_charge:
                self.transaction.add_transaction_step(self.current_step,
                                                      'found charge', SUCCESS,
                                                      'Found unused charge <a href="%s">%s</a>. Pin %s extracted, '
                                                      'details are at <a target="blank" '
                                                      'href="https://www.dollarphonepinless.com/'
                                                      'ppm_orders/%s/receipt">receipt</a>.' %
                                                      (new_charge.get_full_url(), new_charge.id,
                                                       new_charge.pin, new_charge.atransaction))

                return new_charge
            else:
                new_charge = self.transaction.autorefill.create_charge(self.cost, self.tax)
                TransactionCharge.objects.get_or_create(charge=new_charge, transaction=self.transaction)

        try:
            new_charge.atransaction = new_charge.make_dollar_phone_charge(retry=False)
        except Exception, e:
            new_charge.add_charge_step(self.current_step, ERROR, 'DP Charge ended with error: "%s"' % e)
            new_charge.used = True
            new_charge.status = Charge.ERROR
            new_charge.adv_status = 'CC Charge failed with error: "%s"' % e
            new_charge.save()
            raise Exception(e)

        new_charge.used = True
        new_charge.pin_used = True
        new_charge.status = SUCCESS
        new_charge.save()

        self.transaction.add_transaction_step(self.current_step,
                                              'create charge', SUCCESS,
                                              'Used charge <a href="%s">%s</a>. Pin %s extracted, details are at '
                                              '<a target="blank" '
                                              'href="https://www.dollarphonepinless.com/'
                                              'ppm_orders/%s/receipt">receipt</a>.' %
                                              (new_charge.get_full_url(), new_charge.id,
                                               new_charge.pin, new_charge.atransaction))

        # new_charge.add_charge_step(self.current_step,
        #                            SUCCESS,
        #                            'Pin %s extracted from Dollar Phone, details are at <a target="blank" '
        #                            'href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' %
        #                            (new_charge.pin, new_charge.atransaction))

        return new_charge

    def find_unused_charge(self):
        today = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
        payment_day = today - datetime.timedelta(days=self.company.authorize_precharge_days)

        charge = Charge.objects.filter(
            customer=self.customer,
            used=False,
            status=SUCCESS,
            payment_getaway=Charge.DOLLARPHONE,
            pin_used=False,
            created__lte=payment_day).first()

        return charge

    def get_previous_charge(self):

        charges = Charge.objects.filter(
            customer=self.customer,
            used=True,
            status=ERROR,
            payment_getaway=Charge.DOLLARPHONE,
            pin_used=False).order_by('created')

        for charge in charges:
            if TransactionCharge.objects.filter(transaction=self.transaction, charge=charge).count():
                return charge
