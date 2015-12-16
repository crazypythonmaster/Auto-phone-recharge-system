import decimal
import datetime
import logging
import traceback
import authorize
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
import requests

from ppars.apps.dollarphone import site
from pysimplesoap.client import SoapClient
from ppars.apps.core import fields
from ppars.apps.core.models import CompanyProfile, AutoRefill, Customer, \
    Transaction, Plan, SUCCESS, ERROR, Log

from django.db.models.signals import post_save, pre_save, pre_delete
from django.dispatch import receiver
from gadjo.requestprovider.signals import get_request

logger = logging.getLogger('ppars')


class Charge(models.Model):
    SUCCESS = 'S'
    ERROR = 'E'
    REFUND = 'R'
    VOID = 'V'
    PROCESS = 'P'
    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
        (REFUND, 'Refund'),
        (VOID, 'Void'),
    )
    AUTHORIZE = 'A'
    USAEPAY = 'U'
    USAEPAY2 = 'U2'
    REDFIN = 'RF'
    DOLLARPHONE = 'DP'
    CASH_PREPAYMENT = 'CP'
    CASH = 'CA'
    CHARGE_GETAWAY_CHOICES = (
        (AUTHORIZE, 'Authorize'),
        (USAEPAY, 'USAePay'),
        (USAEPAY2, 'USAePay[2]'),
        (REDFIN, 'RedFinNetwork'),
        (DOLLARPHONE, 'DollarPhone'),
        (CASH_PREPAYMENT, 'Cash(PrePayment)'),
        (CASH, 'Cash'),
    )
    REFUND_STATUS = (
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
    )
    id = fields.BigAutoField(primary_key=True)
    company = fields.BigForeignKey(CompanyProfile, null=True, on_delete=models.SET_NULL)
    autorefill = fields.BigForeignKey(AutoRefill, null=True, on_delete=models.SET_NULL)
    customer = fields.BigForeignKey(Customer, null=True, on_delete=models.SET_NULL)
    company_informed = models.BooleanField(default=False)

    creditcard = models.CharField(max_length=20, blank=True)
    used = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    tax = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    summ = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    atransaction = models.CharField(max_length=30, blank=True)
    payment_getaway = models.CharField(max_length=3, choices=CHARGE_GETAWAY_CHOICES)
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES, blank=True)
    adv_status = models.CharField(max_length=500, blank=True)

    pin = models.CharField(max_length=256, blank=True)
    pin_used = models.BooleanField(default=False)

    refund_id = models.CharField(max_length=30, blank=True)
    refund_status = models.CharField(max_length=1, choices=REFUND_STATUS, blank=True)
    refunded = models.DateTimeField(null=True)

    created = models.DateTimeField("Timestamp", auto_now_add=True)
    note = models.TextField(null=True, blank='')

    def __unicode__(self):
        return u'%s' % self.id

    def get_full_url(self):
        return '%s%s' % (settings.SITE_DOMAIN, reverse('charge_detail', args=[self.pk]))

    def is_refundable(self):
        return self.created.replace(tzinfo=None) + datetime.timedelta(days=3) < datetime.datetime.now()

    def transaction_list(self):
        return TransactionCharge.objects.filter(charge=self)

    @property
    def available_funds(self):
        return self.amount - self.summ

    @property
    def get_last_transaction(self):
        transaction_charge = self.transaction_list().order_by('created').first()
        if transaction_charge:
            return transaction_charge.transaction

    def check_getaway(self):
        charge_gateway = self.customer.get_charge_getaway
        if self.payment_getaway != charge_gateway:
            previous_getaway = self.get_payment_getaway_display()
            self.payment_getaway = charge_gateway
            self.save()
            self.add_charge_step(
                'check payment',
                ChargeStep.SUCCESS,
                'Customer getaway changed from "%s" to "%s"' %
                (previous_getaway, self.get_payment_getaway_display()))
        return self

    def make_charge(self, retry=None):
        try:
            # charge card to USAePAY
            if Charge.USAEPAY == self.payment_getaway:
                if not self.customer.usaepay_customer_id:
                    raise Exception(u'Customer credit card didn\'t added to USAePay')
                token = self.company.usaepay_authorization()
                self.atransaction = self.add_transaction_to_usaepay(token, self.customer.usaepay_customer_id)

            # charge card to USAePAY
            if Charge.USAEPAY2 == self.payment_getaway:
                if not self.customer.usaepay_customer_id_2:
                    raise Exception(u'Customer credit card didn\'t added to USAePay[2]')
                token = self.company.usaepay_authorization_2()
                self.atransaction = self.add_transaction_to_usaepay(token, self.customer.usaepay_customer_id_2)

            # charge card to Authorize
            elif Charge.AUTHORIZE == self.payment_getaway:
                if not self.customer.authorize_id:
                    raise Exception(u'Customer credit card didn\'t added to Authorize')
                self.atransaction = self.add_transaction_to_authorize()

            # charge card to RedFinNetwork
            elif Charge.REDFIN == self.payment_getaway:
                if not self.customer.redfin_cc_info_key:
                    raise Exception(u'Customer credit card didn\'t added to RedFinNetwork')
                self.atransaction = self.sale_redfin()

            elif Charge.DOLLARPHONE == self.payment_getaway:
                if not self.customer.has_local_cards:
                    raise Exception(u'Customer credit card didn\'t added to system')
                self.atransaction = self.make_dollar_phone_charge(retry=retry)
            self.status = Charge.SUCCESS
            self.used = False
            self.adv_status = "Charge ended successfully"
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            self.used = True
            self.status = Charge.ERROR
            self.adv_status = 'CC Charge failed with error: "%s"' % e
            raise Exception(e)
        finally:
            self.save()

    def make_dollar_phone_charge(self, **kwargs):
        if self.atransaction and not ChargeStep.objects.filter(charge=self, adv_status__icontains='DollarPhone transaction failed'):
            pin, adv_status, status = self.check_previous_dp_pin_charge()
            if status:
                if pin:
                    self.pin = pin
                self.add_charge_step('check', Charge.SUCCESS, "%s" % adv_status)
                return self.atransaction
            else:
                if 'Request failed,' not in adv_status:
                    raise Exception(adv_status)
                else:
                    self.add_charge_step('check', Charge.SUCCESS, "%s" % adv_status)

        plan = self.is_plan_available(retry=kwargs['retry'])
        form_fields = {
                'username': self.company.dollar_user,
                'password': self.company.dollar_pass,
                'Carrier': plan.carrier.name,
                'Plan': plan.plan_name,
                'company': self.company,
                'Amount': '$%s' % plan.plan_cost,
                'Customer': self.customer,
                'phone_number': self.autorefill.phone_number,
                'transaction': self
        }

        if self.autorefill.plan.plan_type == Plan.DOMESTIC_TOPUP:
            response = site.purchase_top_up_cc(form_fields)
            logger.debug('DP reciept %s %s' % (self.transaction.id, response['receipt_id']))
        else:
            response = site.purchase_pin_cc(form_fields)
            logger.debug('DP reciept %s %s' % (self.transaction.id, response['receipt_id']))
            if response['status']:
                self.pin = response['pin']
                self.save()
            else:
                if response['receipt_id']:
                    self.atransaction = response['receipt_id']
                    self.save()
                raise Exception("%s" % response['adv_status'])
        self.add_charge_step('charge', Charge.SUCCESS, "%s" % response['adv_status'])
        return response['receipt_id']

    def check_previous_dp_pin_charge(self):
        pin = ''
        try:
            s = site.dollar_phone_site_authorization(self.company.dollar_user, self.company.dollar_pass)
            receipt = site.check_receipt(s, self.atransaction)
            if self.autorefill.plan.plan_type == Plan.DOMESTIC_TOPUP:
                adv_status = 'Phone was refilled, details are at ' \
                             '<a target="blank" href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' % self.atransaction
            else:
                pin = site.get_pin(receipt)
                adv_status = 'Pin %s extracted from Dollar Phone, details are at ' \
                             '<a target="blank" href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' % \
                             (pin, self.atransaction)
            return pin, adv_status, True
        except Exception, e:
            adv_status = '%s' % e
            return pin, adv_status, False

    def is_plan_available(self, **kwargs):
        # check is plan available
        retry = kwargs['retry']
        self.add_charge_step('charge', Charge.SUCCESS, 'Check is plan available')
        plan = self.autorefill.plan
        if not plan.available or retry:
            if plan.universal_plan:
                plan = plan.universal_plan
                self.add_charge_step('charge', Charge.SUCCESS,
                                      'Plan not available. Used Universal plan %s' %
                                      plan.plan_id)
            elif retry:
                plan = plan
                self.add_charge_step('charge', Charge.SUCCESS,
                                      'Universal plan not setted. Used standart plan %s' %
                                      plan.plan_id)
            else:
                raise Exception('Plan not available and didn\'t have universal plan')
        return plan

    def add_transaction_to_authorize(self):
        if settings.TEST_MODE:
            return 123456
        self.company.authorize_authorization()
        aid = self.customer.authorize_id.split("_")
        line_items = []
        if self.autorefill:
            line_items = [{
                'item_id': '%s' % self.autorefill.plan.id,
                'name': '%s' % self.autorefill.plan,
                'description': 'Prepaid Phone recharge for %s' % self.autorefill.phone_number,
                'quantity': 1,
                'unit_price': self.amount,
                'taxable': 'false',
            }]
        d = {
            'amount': self.amount,
            'customer_id': aid[0],
            'payment_id': aid[1],
            'line_items': line_items
        }
        result = authorize.Transaction.sale(d)
        return result.transaction_response.trans_id

    def add_transaction_to_usaepay(self, token, usaepay_customer_id):
        if settings.TEST_MODE:
            return 123456
        client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                            trace=True,
                            ns=False)
        description = ''
        if self.autorefill and not self.company.blank_usaepay_description:
            description = 'Prepaid Phone recharge for %s' % self.autorefill.phone_number
        params = {
            u'Command': 'Sale',
            u'Details': {
                u'Amount': self.amount,
                u'Description': description,
                u'Invoice': '%s' % self.id,
                # u'OrderID': '',
                # u'PONum': '',
            }
        }
        response = client.runCustomerTransaction(Token=token,
                                                 CustNum=usaepay_customer_id,
                                                 PaymentMethodID=0,
                                                 Parameters=params)
        result_code = response['runCustomerTransactionReturn']['ResultCode']
        if 'A' == result_code:
            result = response['runCustomerTransactionReturn']['RefNum']
            return result
        elif 'D' == result_code:
            self.atransaction = response['runCustomerTransactionReturn']['RefNum']
            self.save()
            raise Exception('Transaction Declined: %s' % response['runCustomerTransactionReturn']['Error'])
        else:
            self.atransaction = response['runCustomerTransactionReturn']['RefNum']
            self.save()
            raise Exception('Transaction Error: %s' % response['runCustomerTransactionReturn']['Error'])

    def sale_redfin(self):
        client = SoapClient(wsdl=settings.REDFIN_WSDL)
        response = client.ProcessCreditCard(
            Username='%s' % self.company.redfin_username,
            Password='%s' % self.company.redfin_password,
            Vendor='%s' % self.company.redfin_vendor,
            CcInfoKey='%s' % self.customer.redfin_cc_info_key,
            Amount='%s' % self.amount,
            InvNum='#%s' % self.customer.creditcard[-4:],
            ExtData=''
            )
        logger.error('REDFIN_SALE: %s' % response)
        result = response['ProcessCreditCardResult']
        if result['code'] == 'OK':
            if 'DECLINED' == result['error']:
                self.atransaction = result['PNRef']
                self.save()
                if 'AuthCode' in result:
                    error_message = result['AuthCode']
                elif 'Message' in result:
                    error_message = result['Message']
                else:
                    error_message = 'Undefined response from RedFinNetwork'
                raise Exception('Transaction Declined: %s' % error_message)
            return result['PNRef']
        else:
            raise Exception('%s' % result['error'])

    def make_void(self, user):
        try:
            if Charge.USAEPAY == self.payment_getaway:
                token = self.company.usaepay_authorization()
                response = self.void_transaction_from_usaepay(token)
                self.adv_status = 'CC Charge amount void to customer'
                self.status = Charge.VOID
            elif Charge.USAEPAY2 == self.payment_getaway:
                token = self.company.usaepay_authorization_2()
                response = self.void_transaction_from_usaepay(token)
                self.adv_status = 'CC Charge amount void to customer'
                self.status = Charge.VOID
            elif Charge.AUTHORIZE == self.payment_getaway:
                try:
                    self.adv_status = self.void_transaction_from_authorize()
                    self.status = Charge.VOID
                except authorize.exceptions.AuthorizeResponseError, e:
                    raise Exception(e.full_response['transaction_response']['errors'][0]['error_text'])
            elif Charge.REDFIN == self.payment_getaway:
                self.refund_id, self.adv_status = self.void_redfin()
                self.status = Charge.VOID
            self.used = True
            self.add_charge_step('void', SUCCESS, 'User "%s" started void. Void ended successfully' % user)
        except Exception, e:
            self.adv_status = 'CC Charge void failed with error: "%s"' % e
            self.add_charge_step('void', ERROR, 'User "%s" started void. Void ended with error: "%s"' % (user, e))
            raise Exception(e)
        finally:
            self.save()

    def void_redfin(self):
        client = SoapClient(wsdl=settings.REDFIN_TRANSACTION_WSDL)
        response = client.ProcessCreditCard(
            UserName='%s' % self.company.redfin_username,
            Password='%s' % self.company.redfin_password,
            TransType='Void',
            CardNum='',
            ExpDate='',
            MagData='', #for swiped card
            NameOnCard='',
            Amount='%s' % self.amount,
            InvNum='',
            PNRef='%s' % self.atransaction,
            Zip='',
            Street='',
            CVNum='',
            ExtData=''
            )
        logger.debug('REDFIN_VOID: %s' % response)
        result = response['ProcessCreditCardResult']
        if result['Result'] == 0:
            return result['PNRef'], result['RespMSG']
        else:
            raise Exception('%s' % result['RespMSG'])

    def void_transaction_from_authorize(self):
        if settings.TEST_MODE:
            return 'TEST'
        self.company.authorize_authorization()
        result = authorize.Transaction.void(self.atransaction)
        return result.transaction_response.messages[0]['message']['description']

    def void_transaction_from_usaepay(self, token):
        if settings.TEST_MODE:
            return 'TEST'
        result = ''
        if token:
            client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                                trace=False,
                                ns=False)
            response = client.voidTransaction(Token=token, RefNum=self.atransaction)
            result = response['voidTransactionReturn']
        return result

    def make_refund(self, user):
        try:
            if Charge.USAEPAY == self.payment_getaway:
                token = self.company.usaepay_authorization()
                self.refund_transaction_from_usaepay(token)
                self.adv_status = 'CC Charge amount refunded to customer.' \
                                'Please, check information in %s in 1 day' % \
                                  (self.get_payment_getaway_display())
            elif Charge.USAEPAY2 == self.payment_getaway:
                token = self.company.usaepay_authorization_2()
                self.refund_transaction_from_usaepay(token)
                self.adv_status = 'CC Charge amount refunded to customer.' \
                                'Please, check information in %s in 1 day' % \
                                  (self.get_payment_getaway_display())
            elif Charge.AUTHORIZE == self.payment_getaway:
                try:
                    result = self.refund_transaction_from_authorize()
                    self.refund_id = result.transaction_response.trans_id
                    self.adv_status = result.transaction_response.messages[0]['message']['description']
                except authorize.exceptions.AuthorizeResponseError, e:
                    raise Exception(e.full_response['transaction_response']['errors'][0]['error_text'])
            elif Charge.REDFIN == self.payment_getaway:
                self.refund_id, self.adv_status = self.refund_redfin()
            self.refunded = datetime.datetime.now()
            self.used = True
            self.status = Charge.REFUND
            self.add_charge_step('refund', SUCCESS, 'User "%s" started refund. Refund ended successfully' % user)
        except Exception, e:
            self.add_charge_step('refund', ERROR, 'User "%s" started refund. Refund ended with error: "%s"' % (user, e))
            self.adv_status = 'CC Charge refund failed with error: "%s"' % e
            raise Exception(e)
        finally:
            self.save()

    def refund_redfin(self):
        # if not self.customer.has_local_card:
        #     raise Exception('Refund is not possible. Customer has no full data on a credit card.'
        #                     'You can make manual refund on RedFinNetwork site.')
        client = SoapClient(wsdl=settings.REDFIN_TRANSACTION_WSDL)
        response = client.ProcessCreditCard(
            UserName='%s' % self.company.redfin_username,
            Password='%s' % self.company.redfin_password,
            TransType='Return',
            CardNum='', #'%s' % self.customer.get_local_card().number,
            ExpDate='', #'%s' % self.customer.normalize_exp_data(),
            MagData='', #for swiped card
            NameOnCard='',
            Amount='%s' % self.amount,
            InvNum='',
            PNRef='%s' % self.atransaction,
            Zip='',
            Street='',
            CVNum='',
            ExtData=''
            )
        logger.debug('REDFIN_Refund: %s' % response)
        result = response['ProcessCreditCardResult']
        if result['Result'] == 0:
            return result['PNRef'], result['RespMSG']
        else:
            raise Exception('%s' % result['RespMSG'])

    def refund_transaction_from_authorize(self):
        if settings.TEST_MODE:
            return 'TEST'
        self.company.authorize_authorization()
        result = authorize.Transaction.refund({'amount': self.amount,
                                               'transaction_id': self.atransaction,
                                               'last_four': '%s' % self.creditcard[-4:]})
        return result

    def refund_transaction_from_usaepay(self, token):
        if settings.TEST_MODE:
            return 'TEST'
        client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                            trace=True,
                            ns=False)
        response = client.refundTransaction(Token=token,
                                            RefNum=self.atransaction,
                                            Amount=self.amount)
        return response['refundTransactionReturn']['Result']

    def check_refund(self):
        try:
            if not self.refund_id:
                self.adv_status = 'Charge hasn\'t refund id from payment system.' \
                                  ' Please, check payment system for making manual refund or check it status'
                self.refund_status = self.SUCCESS
                return
            if self.payment_getaway == self.USAEPAY:
                pass
            if self.payment_getaway == self.REDFIN:
                pass
            elif Charge.AUTHORIZE == self.payment_getaway:
                try:
                    result = self.transaction_detail_from_authorize(self.refund_id)
                    if 'refundPendingSettlemen' in result['transaction']['transaction_status']:
                        self.refund_status = self.PROCESS
                        self.adv_status = 'Refund registered and is awaiting the payment system processing'
                    elif 'refundSettledSuccessfully' in result['transaction']['transaction_status']:
                        self.refund_status = self.SUCCESS
                        self.adv_status = 'Refund Settled Successfully'
                    else:
                        self.adv_status = result['transaction']['transaction_status']
                except authorize.exceptions.AuthorizeResponseError, e:
                    raise Exception(e.full_response.messages[0]['message']['text'])
        except Exception, e:
            self.adv_status = 'Check refund failed with error: "%s"' % e
            self.refund_status = self.ERROR
        finally:
            self.save()

    def transaction_detail_from_authorize(self, transaction_id):
        if settings.TEST_MODE:
            return 'TEST'
        self.company.authorize_authorization()
        result = authorize.Transaction.details(transaction_id)
        return result

    def add_charge_step(self, action, status, adv_status):
        ChargeStep.objects.create(
            charge=self,
            action=action,
            status=status,
            adv_status=adv_status
        )

    def retry(self, user):
        action = 'retry charging'
        try:
            if self.payment_getaway in [Charge.AUTHORIZE] and self.atransaction:
                self.status = Charge.SUCCESS
                self.save()
                self.add_charge_step(action,
                                     Charge.SUCCESS,
                                     'User "%s" started retry.Previous charge was successfully. Restart canceled'
                                     % user)
            else:
                self \
                    .check_getaway() \
                    .make_charge(retry=True)
                self.add_charge_step(action,
                                     Charge.SUCCESS,
                                     'User "%s" started retry. Charge retry ended successfully' % user)
                if self.customer.email_success:
                    from ppars.apps.core.send_notifications import successful_precharge_restart_customer_notification
                    successful_precharge_restart_customer_notification(self)

            return self
        except Exception, e:
            self.add_charge_step(action,
                                 Charge.ERROR,
                                 'User "%s" started retry. Charge retry ended with error: "%s"' % (user, e))


class TransactionCharge(models.Model):
    charge = fields.BigForeignKey(Charge)
    transaction = fields.BigForeignKey(Transaction, null=True)
    amount = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    created = models.DateTimeField("Started at", auto_now_add=True)

    def __unicode__(self):
        return u'Ch %s for tr %s' % (self.charge, self.transaction)


class ChargeStep(models.Model):
    SUCCESS = 'S'
    ERROR = 'E'
    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
    )
    charge = fields.BigForeignKey(Charge)
    action = models.CharField(max_length=200)
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES)
    adv_status = models.CharField(max_length=500, null=True)
    created = models.DateTimeField("Timestamp", auto_now=True)

    def __unicode__(self):
        return self.action


class ChargeError(models.Model):
    charge = fields.BigForeignKey(Charge)
    step = models.CharField(max_length=50)
    message = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s [%s]' % (self.step, self.created)

list_of_models = ('Charge')

@receiver(pre_save)
def logging_update(sender, instance, **kwargs):
    if instance.pk and sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"

        if 'company' in dir(instance) and instance.company:
            company = instance.company

        http_request = get_request()
        if http_request:
            request_user = get_request().user
            user_str = 'User %s' % request_user
            if not company:
                if not request_user.is_authenticated():
                    # if 'User AnonymousUser' == user_str:
                    user_str = 'Anonymous User'
                elif request_user.profile.company:
                    company = request_user.profile.company

        new_values = model_to_dict(instance)
        old_values = sender.objects.get(pk=instance.pk).__dict__
        for key in new_values.keys():
            if key not in old_values.keys():  # because there is a things in new_values that we don't need
                new_values.pop(key, None)
        changed = [key for key in new_values.keys() if ((old_values[key] != new_values[key]) and
                                                        not ((old_values[key] is None and new_values[key] == '')
                                                             or (old_values[key] == '' and new_values[key] is None)))]
        if len(changed) > 0:
            update = ''
            for key in changed:
                update += key.replace('_', ' ').upper() + ': from ' + str(old_values[key]) + ' to ' + str(new_values[key]) + '; '
            note = '%s updated %s: %s \n' % (user_str, sender.__name__, str(instance))
            note += update
            Log.objects.create(company=company, note=note)


@receiver(post_save)
def logging_create(sender, instance, created, **kwargs):
    if created and sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"
        obj_attr = ""

        if 'company' in dir(instance) and instance.company:
            company = instance.company

        http_request = get_request()
        if http_request:
            request_user = http_request.user
            user_str = 'User %s' % request_user
            if not company:
                if not request_user.is_authenticated():
                    # if 'User AnonymousUser' == user_str:
                    user_str = 'Anonymous User'
                elif request_user.profile.company:
                    company = request_user.profile.company

        for key in model_to_dict(instance).keys():
            obj_attr += key.replace('_', ' ').upper() + ': ' + str(model_to_dict(instance)[key]) + '; '
        note = '%s created %s: %s \n %s' % (user_str, sender.__name__, str(instance), obj_attr)
        Log.objects.create(company=company, note=note)


@receiver(pre_delete)
def logging_delete(sender, instance, **kwargs):

    if sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"
        obj_attr = ""

        if 'company' in dir(instance) and instance.company:
            company = instance.company

        http_request = get_request()
        if http_request:
            request_user = get_request().user
            user_str = 'User %s' % request_user
            if not company:
                if not request_user.is_authenticated():
                    # if 'User AnonymousUser' == user_str:
                    user_str = 'Anonymous User'
                elif request_user.profile.company:
                    company = request_user.profile.company

        for key in model_to_dict(instance).keys():
            obj_attr += key.replace('_', ' ').upper() + ': ' + str(model_to_dict(instance)[key]) + '; '
        note = 'User %s deleted %s: %s \n %s' % (user_str, sender.__name__, str(instance), obj_attr)
        Log.objects.create(company=company, note=note)


@receiver(post_save, sender=Charge)
def send_precharge_message(instance, created, **kwargs):
    if instance.payment_getaway == Charge.CASH_PREPAYMENT and instance.company.send_prepayment_notification and created:
        from ppars.apps.charge.tasks import send_prepayment_notification
        send_prepayment_notification.delay(instance.customer, instance.amount)
