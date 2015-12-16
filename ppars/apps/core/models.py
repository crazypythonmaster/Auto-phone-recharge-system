import decimal
import datetime
import hashlib
import time
import logging
import traceback
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save, pre_save, pre_delete
from django.db.models import signals
from django.dispatch import receiver
from django.utils.safestring import mark_safe
import pytz
from twilio.rest import TwilioRestClient

import authorize
from asana import asana
from pytz import timezone
from datetime import timedelta
from ext_lib import url_with_querystring
from pysimplesoap.simplexml import SimpleXMLElement
from pysimplesoap.client import SoapClient
from gadjo.requestprovider.signals import get_request

import fields

logger = logging.getLogger('ppars')

SUCCESS = 'S'
ERROR = 'E'
WAITING = 'W'
NO_FONDS = 'F'



def _get_user_profile(user):
    profile = user.profile
    return profile


def _get_company_profile(user):
    company = user.profile.company
    return company

User.get_company_profile = _get_company_profile
User.get_user_profile = _get_user_profile


class NotAdminProfile(Exception):
    pass


class NoAdminCompanyProfileSettings(Exception):
    pass


class CompanyProfile(models.Model):
    """
    This model is a company profile model.
    It's using for all user in one company
    """

    # Exceptions
    NotAdminProfile = NotAdminProfile
    NoAdminCompanyProfileSettings = NoAdminCompanyProfileSettings

    DONT_SEND = 'NO'
    MAIL = 'EM'
    SMS = 'SM'
    SMS_EMAIL = 'SE'
    GV_SMS = 'GV'
    SEND_STATUS_CHOICES = (
        (DONT_SEND, "Don't Send"),
        (SMS_EMAIL, 'SMS via Email'),
        (SMS, 'via Twilio SMS'),
        (MAIL, 'via Email'),
        (GV_SMS, 'Sms via Google Voice'),
    )
    DOLLAR_TYPE_CHOICES = (
        ('A', 'API'),
        ('S', 'Web Site'),
    )
    DOLLARPHONE = 'DP'
    AUTHORIZE = 'A'
    USAEPAY = 'U'
    USAEPAY2 = 'U2'
    REDFIN = 'RF'
    CASH_PREPAYMENT = 'CP'
    CASH = 'CA'
    CCCHARGE_TYPE_CHOICES = (
        (AUTHORIZE, 'Authorize'),
        (USAEPAY, 'USAePay'),
        (USAEPAY2, 'USAePay[2]'),
        (REDFIN, 'RedFinNetwork'),
        (DOLLARPHONE, 'DollarPhone'),
        # (CASH_PREPAYMENT, 'Cash(PrePayment)'),
        # (CASH, 'Cash'),
    )

    TWILIO = 'TW'
    CAPTCHA = 'CP'
    PPR_TYPE_CHOICES = (
        (TWILIO, 'Phone(Twilio)'),
        (CAPTCHA, 'Website'),
    )
    id = fields.BigAutoField(primary_key=True)
    # Link to the user model
    # user = models.ForeignKey(User, related_name='profile', unique=False, blank=True, null=True)

    updated = models.BooleanField(default=False)
    superuser_profile = models.BooleanField(default=False)

    # General
    company_name = models.CharField(max_length=40, null=True, blank=True)
    email_id = models.EmailField(null=True, blank=True)
    email_success = models.BooleanField(default=False)
    precharge_failed_email = models.BooleanField(default=True)
    block_duplicate_schedule = models.BooleanField(default=True)
    block_duplicate_phone_number = models.BooleanField(default=True)
    pin_error = models.BooleanField(default=True)
    short_retry_limit = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(9)], null=True, blank=True)
    short_retry_interval = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1200)], null=True, blank=True)
    long_retry_limit = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(9)], null=True, blank=True)
    long_retry_interval = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(1200)], null=True, blank=True)
    schedule_limit = models.IntegerField(validators=[MinValueValidator(0)], blank=True, default=0)
    send_pin_prerefill = models.CharField(max_length=2, choices=SEND_STATUS_CHOICES, default=DONT_SEND)
    send_status = models.CharField(max_length=2, choices=SEND_STATUS_CHOICES, default=DONT_SEND)
    able_change_send_pin_prerefill = models.BooleanField(default=False)
    insufficient_funds_notification = models.BooleanField(default=False)
    show_updates = models.BooleanField(default=False, editable=False)
    default_zip = models.CharField(max_length=10, blank=True, default='')
    can_swipe_card_in_customer = models.BooleanField(default=False)
    can_swipe_card_in_search = models.BooleanField(default=False)
    verify_carrier = models.BooleanField(default=False)
    verify_pin = models.BooleanField(default=False)
    card_expiration_date_info = models.BooleanField(default=False)
    manual_cash_already_paid = models.BooleanField(default=False)
    default_cash_prepayment_for_walk_in = models.BooleanField(default=False)
    send_prepayment_notification = models.BooleanField(default=True)

    #date_limit_company
    license_expiries = models.BooleanField(default=True)
    date_limit_license_expiries = models.DateField(null=True, blank=True)

    #Tax
    tax = models.DecimalField(max_digits=7, decimal_places=4, default=decimal.Decimal(0.0))

    # Google Voice
    gvoice_email = models.EmailField(null=True, blank=True)
    gvoice_pass = models.CharField(max_length=500, null=True,blank=True)
    gvoice_enabled = models.BooleanField(default=False)

    # Twilio
    twilio_number = models.CharField(max_length=10, null=True, blank=True)
    twilio_sid = models.CharField(max_length=500, null=True, blank=True)
    twilio_auth_token = models.CharField(max_length=500, null=True, blank=True)

    # Death By Captcha
    deathbycaptcha_user = models.CharField(max_length=100, blank=True, null=True)
    deathbycaptcha_pass = models.CharField(max_length=100, blank=True, null=True)
    deathbycaptcha_email_balance = models.IntegerField(max_length=10, null=True, blank=True, default=70)
    deathbycaptcha_count = models.IntegerField(max_length=10, null=True, blank=True, default=5000)
    deathbycaptcha_current_count = models.IntegerField(max_length=10, null=True, blank=True, default=0)
    deathbycaptcha_emailed = models.BooleanField(default=True)

    # Page Plus Recharge
    pageplus_refillmethod = models.CharField(max_length=3, choices=PPR_TYPE_CHOICES, default='TW', blank=True, null=True)

    # Dollar Phone
    dollar_type = models.CharField(max_length=3, choices=DOLLAR_TYPE_CHOICES, blank=True, null=True)
    dollar_user = models.CharField(max_length=100, blank=True, null=True)
    dollar_pass = models.CharField(max_length=100, blank=True, null=True)

    #Mandrill
    mandrill_key = models.CharField(max_length=500, null=True, blank=True)
    mandrill_email = models.EmailField(null=True, blank=True)

    #authorize.net
    authorize_api_login_id = models.CharField(max_length=100, null=True, blank=True)
    authorize_transaction_key = models.CharField(max_length=100, null=True, blank=True)

    # Credit Card Charging getaway type
    cccharge_type = models.CharField(max_length=3, choices=CCCHARGE_TYPE_CHOICES, blank=True, null=True)
    unused_charge_notification = models.BooleanField(default=True)
    authorize_precharge_days = models.IntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)], null=True, blank=True)
    precharge_notification_type = models.CharField(max_length=2, choices=SEND_STATUS_CHOICES, default=SMS_EMAIL, blank=True)

    # USAePay
    # first account
    usaepay_source_key = models.CharField(max_length=100, null=True, blank=True)
    usaepay_pin = models.CharField(max_length=100, null=True, blank=True)
    usaepay_username = models.CharField(max_length=100, blank=True, null=True)
    usaepay_password = models.CharField(max_length=100, blank=True, null=True)
    # second account
    use_usaepay_2 = models.BooleanField(default=False)
    usaepay_source_key_2 = models.CharField(max_length=100, blank=True)
    usaepay_pin_2 = models.CharField(max_length=100, blank=True)
    usaepay_username_2 = models.CharField(max_length=100, blank=True)
    usaepay_password_2 = models.CharField(max_length=100, blank=True)

    blank_usaepay_description = models.BooleanField(default=False)

    # RedFinNetwork
    use_redfin = models.BooleanField(default=False)
    redfin_username = models.CharField(max_length=100, blank=True)
    redfin_password = models.CharField(max_length=100, blank=True)
    redfin_vendor = models.CharField(max_length=100, blank=True)

    #sellercloud
    use_sellercloud = models.BooleanField(default=False)
    sc_company_id = models.CharField(max_length=100, null=True, blank=True)
    sc_password = models.CharField(max_length=100, blank=True, null=True)
    sc_email = models.EmailField(null=True, blank=True)

    #asana
    use_asana = models.BooleanField(default=False)
    asana_api_key = models.CharField(max_length=100, null=True, blank=True)
    asana_workspace = models.CharField(max_length=100, null=True, blank=True)
    asana_project_name = models.CharField(max_length=100, null=True, blank=True)
    asana_user = models.CharField(max_length=100, null=True, blank=True)
    deposit_amount_notification = models.BooleanField(default=False)

    #email for date limit user
    sales_agent_email = models.EmailField(blank=True)
    admin_email = models.EmailField(blank=True)

    #welcome emails
    can_send_welcome_emails = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s:[%s]' % (self.company_name, self.id)

    def get_absolute_url(self):
        return reverse('profile')

    def authorize_authorization(self):
        authorize.Configuration.configure(
            settings.AUTHORIZE_ENVIRONMENT,
            self.authorize_api_login_id,
            self.authorize_transaction_key
        )

    def check_available_schedule_create(self):
        if self.schedule_limit == 0:
            return True
        if AutoRefill.objects.filter(trigger='SC', company=self).count() >= self.schedule_limit:
            return False
        else:
            return True

    def usaepay_authorization(self):
        seed = time.time()
        clear = '%s%s%s' % (self.usaepay_source_key, seed, self.usaepay_pin)
        m = hashlib.sha1()
        m.update(clear)
        token = {
            u'ClientIP':'192.168.0.1',
            u'PinHash': {
                u'HashValue': m.hexdigest(),
                u'Seed': seed,
                u'Type': 'sha1'
            },
            u'SourceKey': self.usaepay_source_key
        }
        return token

    def usaepay_authorization_2(self):
        seed = time.time()
        clear = '%s%s%s' % (self.usaepay_source_key_2, seed, self.usaepay_pin_2)
        m = hashlib.sha1()
        m.update(clear)
        token = {
            u'ClientIP':'192.168.0.1',
            u'PinHash': {
                u'HashValue': m.hexdigest(),
                u'Seed': seed,
                u'Type': 'sha1'
            },
            u'SourceKey': self.usaepay_source_key_2
        }
        return token

    def sellingprices_amount_for_week(self):
        '''
        :return: selling prices amount for dashboard
        '''
        result = [0, 0, 0, 0, 0, 0, 0]  # week list
        from datetime import timedelta
        today = datetime.datetime.now(timezone('US/Eastern')).date()
        for plan in Plan.objects.all():
            unused_pins_amount = UnusedPin.objects.filter(company=self, plan=plan, used=False).count()
            for autorefill in AutoRefill.objects.filter(renewal_date__range=(today, today+timedelta(days=6)), plan=plan,
                                                        company=self, enabled=True, trigger=AutoRefill.TRIGGER_SC):
                appeared = 0  # counting how many times scheduled refill will be triggered this week
                autorefill_week = [0, 0, 0, 0, 0, 0, 0]
                if autorefill.renewal_date:
                    for i in range(7):
                        if autorefill.renewal_interval:
                            if today+timedelta(days=i) \
                                    == autorefill.renewal_date+timedelta(days=autorefill.renewal_interval*appeared) \
                                    <= today+timedelta(days=6):
                                appeared += 1
                                if unused_pins_amount < 1:
                                    autorefill_week[i] = autorefill.calculate_cost_and_tax()[0]
                                else:
                                    unused_pins_amount -= 1
                                continue
                        if autorefill.plan.carrier.renew_days:
                            if today+timedelta(days=i) \
                                    == autorefill.renewal_date+timedelta(days=autorefill.plan.carrier.renew_days *
                                            appeared) <= today+timedelta(days=6):
                                appeared += 1
                                if unused_pins_amount < 1:
                                    autorefill_week[i] = autorefill.calculate_cost_and_tax()[0]
                                else:
                                    unused_pins_amount -= 1
                                continue
                        if autorefill.plan.carrier.renew_months:
                            if today+timedelta(days=i) == autorefill.renewal_date:
                                if unused_pins_amount < 1:
                                    autorefill_week[i] = autorefill.calculate_cost_and_tax()[0]
                                break  # in that case it can only appear once per week
                    price = 0
                    for i in range(7):
                        if autorefill_week[i]:
                            price += autorefill_week[i]
                        result[i] += price
        return result

    def set_selling_prices(self):
        from ppars.apps.price.models import SellingPriceLevel, PlanSellingPrice
        for plan in Plan.objects.all():
            for price_level in SellingPriceLevel.objects.all():
                PlanSellingPrice.objects.create(carrier=plan.carrier,
                                                plan=plan,
                                                company=self,
                                                price_level=price_level,
                                                selling_price=plan.plan_cost)

    def set_customers_send_pin_prerefill(self, state):
        self.send_pin_prerefill = state
        for customer in Customer.objects.filter(company=self):
            customer.send_pin_prerefill = self.send_pin_prerefill
            customer.save()
        self.save()

    def set_default_notification(self):
        for customer in Customer.objects.filter(company=self):
            customer.email_success_charge = False
            customer.email_success_refill = False
            customer.precharge_sms = False
            customer.save()
        self.save()

    def set_default_license_expiries(self):
        if not self.date_limit_license_expiries:
            self.date_limit_license_expiries = \
                datetime.datetime.now(pytz.timezone('US/Eastern')).date() + relativedelta(months=12)

    @property
    def admin_company_settings(self):
        if self.superuser_profile:
            if AdminCompanyProfileSettings.objects.filter(company=self).exists():
                return AdminCompanyProfileSettings.objects.get(company=self)
            else:
                raise NoAdminCompanyProfileSettings('No admin company profile settings.')
        else:
            raise NotAdminProfile('Company you\'re in is not admin company.')



class AdminCompanyProfileSettings(models.Model):
    """
    Let's start separate new additional data, not always required in main model, to additional model with reference to
    main one. At least where we can, to not make thing even worse.
    We'll use it mainly via manager's method get_or_create,
    so when you adding new field try to always set default value for it
    """
    company = fields.BigForeignKey(CompanyProfile, blank=False, null=False)

    # Twilio Bulk Promotion Settings
    bulk_promotion_twilio_number = models.CharField(max_length=10, blank=True, default='')
    bulk_promotion_twilio_sid = models.CharField(max_length=500, blank=True, default='')
    bulk_promotion_twilio_auth_token = models.CharField(max_length=500, blank=True, default='')

    @property
    def has_twilio_bulk_promotion_settings(self):
        if self.bulk_promotion_twilio_auth_token and self.bulk_promotion_twilio_number and\
                self.bulk_promotion_twilio_sid:
            return True
        return False

    def __unicode__(self):
        return u'Admin %s:[%s] settings' % (self.company.company_name, self.company.id)


class UserProfile(models.Model):
    """
    This model use as related model for User and CompanyProfile
    """
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigOneToOneField(User, related_name='profile', unique=False, blank=True, null=True)
    company = fields.BigForeignKey(CompanyProfile, related_name='user_profile', blank=True, null=True)
    updates_email = models.TextField(null=True, blank=True)
    superuser_profile = models.NullBooleanField()
    profit_restriction = models.BooleanField(default=True)
    show_urgent = models.BooleanField(default=True)

    def __unicode__(self):
        username = None
        if self.user:
            username = self.user.username
        return u'profile %s' % username

    def is_license_expiries(self):
        if self.company.license_expiries and self.company.date_limit_license_expiries and datetime.datetime.now(pytz.timezone('US/Eastern')).date() > self.company.date_limit_license_expiries:
            return False
        else:
            return True

    def get_company_users(self):
        users = []
        comps = UserProfile.objects.filter(company=self.user.profile.company)
        for comp in comps:
            users.append(comp.user)
        return users

    def get_company_logs(self):
        logs = Log.objects.filter(company=self.user.profile.company)
        for log in logs:
            log.note = log.note.split('\n')
        return logs

    def get_company_customers(self):
        customers = Customer.objects.filter(company=self.user.profile.company)
        return customers

    def get_company_autorefills(self):
        autorefills = AutoRefill.objects.filter(trigger="SC", company=self.user.profile.company)
        return autorefills


class Log(models.Model):
    id = fields.BigAutoField(primary_key=True)
    company = fields.BigForeignKey(CompanyProfile, null=True, blank=True)
    note = models.TextField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    # created = models.DateTimeField()

    def get_created_est(self):
        return self.created

    class Meta:
        ordering = ["-created"]

    def __unicode__(self):
        return self.note

    def get_absolute_url(self):
        return reverse('log_list')


class Carrier(models.Model):
    SCHEDULE_TYPE_CHOICES = (
        ('MD', 'Mid-Day'),
        ('MN', '11:59 PM.'),
        ('1201AM', '12:01 AM.'),
        ('1AM', '1 AM.'),
        ('130AM', '1:30 AM.'),
        ('2AM', '2 AM.'),
        ('12pm&1201am', '12PM & 12:01AM'),
    )

    id = fields.BigAutoField(primary_key=True)
    name = models.CharField(max_length=100)
    recharge_number = models.CharField(max_length=10, blank=True)
    admin_site = models.CharField(max_length=500, blank=True)
    renew_days = models.IntegerField(max_length=3, blank=True, null=True)
    renew_months = models.IntegerField(max_length=3, blank=True, null=True)
    created = models.DateTimeField("Created at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated at", auto_now=True)

    default_time = models.CharField(max_length=11, choices=SCHEDULE_TYPE_CHOICES, blank=True)

    # created = models.DateTimeField("Created at")
    # updated = models.DateTimeField(verbose_name="Updated at")

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('carrier_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated


class Plan(models.Model):
    DOMESTIC_PIN = 'PI'
    DOMESTIC_TOPUP = 'TP'
    PLAN_TYPE_CHOICES = (
        (DOMESTIC_TOPUP, 'Domestic Top-Up'),
        (DOMESTIC_PIN, 'Domestic Pin'),
    )
    id = fields.BigAutoField(primary_key=True)

    plan_id = models.CharField(max_length=100)
    api_id = models.CharField(max_length=30, blank=True)
    sc_sku = models.CharField(max_length=30, blank=True)
    carrier = fields.BigForeignKey(Carrier)
    plan_name = models.CharField(max_length=100)
    rate_plan = models.CharField(max_length=100, blank=True)
    plan_cost = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    plan_type = models.CharField(max_length=2, choices=PLAN_TYPE_CHOICES, default=DOMESTIC_PIN)

    universal_plan = fields.BigForeignKey('self', blank=True, null=True, related_name='plan')
    universal = models.BooleanField(default=False)
    available = models.BooleanField(default=True)

    enabled = models.BooleanField(default=True)

    created = models.DateTimeField("Created at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated at", auto_now=True)

    # created = models.DateTimeField(("Created at"))
    # updated = models.DateTimeField(verbose_name=("Updated at"))

    def __unicode__(self):
        return self.plan_id

    def get_absolute_url(self):
        return reverse('plan_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated

    def get_plansellingprice(self, company, selling_price_level):
        from ppars.apps.price.models import PlanSellingPrice
        plansellingprice = PlanSellingPrice.objects.get(plan=self,
                                                        company=company,
                                                        price_level=selling_price_level)
        return plansellingprice.selling_price

    def set_selling_prices(self):
        from ppars.apps.price.models import SellingPriceLevel, PlanSellingPrice
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            for price_level in SellingPriceLevel.objects.all():
                PlanSellingPrice.objects.create(carrier=self.carrier,
                                                plan=self,
                                                company=company,
                                                price_level=price_level,
                                                selling_price=self.plan_cost)


class PlanDiscount(models.Model):
    id = fields.BigAutoField(primary_key=True)
    company = fields.BigForeignKey(CompanyProfile, null=True)
    carrier = fields.BigForeignKey(Carrier)
    plan = fields.BigForeignKey(Plan, null=True, blank=True)
    discount = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    created = models.DateTimeField("Created at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated at", auto_now=True)

    # created = models.DateTimeField(("Created at"))
    # updated = models.DateTimeField(verbose_name=("Updated at"))

    def __unicode__(self):
        plan = self.plan or "default"
        return "%s_%s" % (self.carrier, plan)

    def get_absolute_url(self):
        return reverse('plan_discount_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated


class Customer(models.Model):
    from ppars.apps.price.models import level_price_default
    # Must be the same as in Notification model!!!
    DONT_SEND = 'NO'
    MAIL = 'EM'
    SMS = 'SM'
    SMS_EMAIL = 'SE'
    GV_SMS = 'GV'
    SEND_STATUS_CHOICES = (
        (DONT_SEND, "Don't Send"),
        (SMS_EMAIL, 'SMS via Email'),
        (SMS, 'via Twilio SMS'),
        (MAIL, 'via Email'),
        (GV_SMS, 'Sms via Google Voice'),
    )
    CASH = 'CA'
    CREDITCARD = 'CC'
    CHARGE_TYPE_CHOICES = (
        (CASH, 'Cash'),
        (CREDITCARD, 'Credit Card'),
    )
    DOLLARPHONE = 'DP'
    AUTHORIZE = 'A'
    USAEPAY = 'U'
    USAEPAY2 = 'U2'
    REDFIN = 'RF'
    CASH_PREPAYMENT = 'CP'
    CHARGE_GETAWAY_CHOICES = (
        (AUTHORIZE, 'Authorize'),
        (USAEPAY, 'USAePay'),
        (USAEPAY2, 'USAePay[2]'),
        (REDFIN, 'RedFinNetwork'),
        (DOLLARPHONE, 'DollarPhone'),
        (CASH, 'Cash'),
        (CASH_PREPAYMENT, 'Cash(PrePayment)'),
    )
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigForeignKey(User, null=True, on_delete=models.SET_NULL)
    company = fields.BigForeignKey(CompanyProfile, blank=True, null=True)

    first_name = models.CharField(max_length=30, blank=True)
    middle_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True)

    primary_email = models.EmailField(blank=True)
    primary_email_lowercase = models.EmailField(blank=True)

    sc_account = models.CharField(max_length=30, blank=True, null=True)

    address = models.CharField(max_length=500, blank=True, null=True)
    city = models.CharField(max_length=30, blank=True, null=True)
    state = models.CharField(max_length=30, blank=True, null=True)
    zip = models.CharField(max_length=10, blank=True)

    charge_type = models.CharField(max_length=2, choices=CHARGE_TYPE_CHOICES, default='CA')
    charge_getaway = models.CharField(max_length=3, choices=CHARGE_GETAWAY_CHOICES, blank=True)
    creditcard = models.CharField(max_length=20, blank=True, null=True)

    authorize_id = models.CharField(max_length=30, blank=True, null=True)

    usaepay_customer_id = models.CharField(max_length=30, blank=True, null=True)
    usaepay_custid = models.CharField(max_length=100, blank=True)

    usaepay_customer_id_2 = models.CharField(max_length=30, blank=True)
    usaepay_custid_2 = models.CharField(max_length=100, blank=True)

    redfin_customer_key = models.CharField(max_length=100, blank=True)
    redfin_cc_info_key = models.CharField(max_length=100, blank=True)

    selling_price_level = models.ForeignKey('price.SellingPriceLevel', default=level_price_default)
    customer_discount = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0), blank=True)
    taxable = models.BooleanField(default=True)

    precharge_sms = models.BooleanField(default=False)
    email_success_charge = models.BooleanField(default=False)
    email_success_refill = models.BooleanField(default=False)

    send_status = models.CharField(max_length=2, choices=SEND_STATUS_CHOICES, default=DONT_SEND)
    send_pin_prerefill = models.CharField(max_length=2, choices=SEND_STATUS_CHOICES, default=DONT_SEND)

    notes = models.TextField(null=True, blank=True)

    group_sms = models.BooleanField(default=True)
    enabled = models.BooleanField(default=True)

    created = models.DateTimeField("Created at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Updated at", auto_now=True)

    welcomed = models.BooleanField(default=False)
    # # for import
    # created = models.DateTimeField("Created at" )
    # updated = models.DateTimeField(verbose_name="Updated at")

    def __unicode__(self):
        return " ".join([self.first_name, self.middle_name or '', self.last_name])

    @property
    def full_name(self):
        return " ".join([self.first_name, self.middle_name or '', self.last_name])

    @property
    def notification_method(self):
        if self.send_status != Customer.DONT_SEND:
            return self.send_status
        else:
            if self.primary_email:
                return Customer.MAIL
            else:
                return Customer.SMS_EMAIL

    def phone_numbers_list(self):
        numbers = PhoneNumber.objects.filter(customer=self)
        if numbers:
            result = list()
            for number in numbers:
                result.append('%s:%s:%s' %
                              (number,
                               url_with_querystring(reverse('manualrefill'), ph=number, cid=self.id),
                               url_with_querystring(reverse('autorefill_create'), ph=number, cid=self.id)))
            return result

    def get_full_url(self):
        return '%s%s' % (settings.SITE_DOMAIN, reverse('customer_update', args=[self.pk]))

    def get_absolute_url(self):
        return reverse('customer_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated

    def set_primary_email_to_lowercase(self):
        if self.primary_email:
            self.primary_email_lowercase = self.primary_email.lower()

    def check_duplicate_number(self, phone_numbers):
        if not phone_numbers:
            return
        pns = []
        msg = []
        numbers = phone_numbers.split(',')
        for number in numbers:
            if self.id:
                phone_numbers = PhoneNumber.objects.filter(number=number, company=self.company).exclude(customer=None).exclude(customer_id=self.id)
            else:
                phone_numbers = PhoneNumber.objects.filter(number=number, company=self.company).exclude(customer=None)
            if phone_numbers.exists():
                pns.append(phone_numbers)

        if len(pns) > 0 and self.company.block_duplicate_phone_number:
            for phone_numbers in pns:
                for phonenumber in phone_numbers:
                    msg.append(mark_safe("Number '%s' already exist at <a href=\"%s\">%s</a>" % (phonenumber.number, reverse('customer_update', args=[phonenumber.customer.id]), phonenumber.customer)))
            return msg

        if self.id:
            phones = PhoneNumber.objects.filter(customer=self)
            deleted_phones = map(str, phones.exclude(number__in=numbers).values_list('number', flat=True))
            if deleted_phones:
                prerefiled_days = self.company.authorize_precharge_days or 0 #0 if company.authorize_precharge_days is Blank
                prerefiled = AutoRefill.objects.exclude(enabled=False).filter(phone_number__in=deleted_phones, renewal_date__gt=datetime.datetime.now() - timedelta(days=prerefiled_days))
                if prerefiled:
                    for phone in prerefiled:
                        msg.append("Cannot delete number %s because it can has precharge before top up" % phone.phone_number)
                    return msg
        self.set_phone_numbers(numbers)
        return 'Phone numbers added successfully'

    def set_phone_numbers(self, phone_numbers, phone_titles=None, sms_gateways=None, sms_emails=None):
        if phone_numbers:
            for pn in PhoneNumber.objects.filter(customer=self):
                if phone_titles:
                    if pn.number not in phone_numbers or pn.title not in phone_titles or pn.sms_gateway not in sms_gateways or pn.use_for_sms_email not in sms_emails:
                        pn.customer = None
                        pn.save()
                    if pn.number not in phone_numbers:
                        for ar in AutoRefill.objects.filter(phone_number=pn.number):
                            ar.enabled = False
                            ar.save()
                else:
                    if pn.number not in phone_numbers:
                        pn.customer = None
                        pn.save()
                        for ar in AutoRefill.objects.filter(phone_number=pn.number):
                            ar.enabled = False
                            ar.save()
            if phone_titles and sms_gateways and sms_emails:
                i = 1
                for number, title, gateway, use_for in zip(phone_numbers, phone_titles, sms_gateways, sms_emails):
                    use = False
                    if use_for == 'on' or (i == 1 and 'on' not in sms_emails):
                        use = True
                    PhoneNumber.objects.get_or_create(number=number,
                                                      company=self.company,
                                                      customer=self,
                                                      title=title,
                                                      sms_gateway_id=int(gateway),
                                                      use_for_sms_email=use)
                    i += 1
            else:
                for number in phone_numbers:
                    PhoneNumber.objects.get_or_create(number=number,
                                                      company=self.company,
                                                      customer=self)


    def create_card_to_usaepay(self, data):
        token = self.company.usaepay_authorization()
        client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                            trace=False,
                            ns=False)
        response = client.addCustomer(Token=token, CustomerData=data)
        return response['addCustomerReturn']

    def update_card_to_usaepay(self, data):
        token = self.company.usaepay_authorization()
        result = False
        if token:
            client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                                trace=True,
                                ns=False)
            response = client.quickUpdateCustomer(CustNum=self.usaepay_customer_id,
                                                  Token=token,
                                                  UpdateData=data)
            result = response
        return result

    def update_card_to_usaepay_2(self, data):
        token = self.company.usaepay_authorization_2()
        result = False
        if token:
            client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                                trace=True,
                                ns=False)
            response = client.quickUpdateCustomer(CustNum=self.usaepay_customer_id_2,
                                                  Token=token,
                                                  UpdateData=data)
            result = response
        return result

    @property
    def has_local_cards(self):
        # from ppars.apps.card.models import Card
        return bool(self.cards.exists())
        # return True

    def get_local_card(self):
        if self.has_local_cards:
            return self.cards.all()[0]
        return None

    @property
    def get_local_card_expiration_month(self):
        if self.has_local_cards:
            card = self.cards.all()[0]
            return card.expiration_month
        return None

    @property
    def get_local_card_expiration_year(self):
        if self.has_local_cards:
            card = self.cards.all()[0]
            return card.expiration_year
        return None

    def normalize_exp_data(self):
        if self.has_local_cards:
            year = self.get_local_card_expiration_year
            month = self.get_local_card_expiration_month
            if len(str(month)) == 1:
                month = '0%s' % month
            return '%s%s' % (month, str(year)[-2:])
        return ''

    def save_local_card(self, first_name, last_name, number, cvv, year, month):
        from ppars.apps.card.models import Card
        obj = self.get_local_card()
        if not obj:
            obj = Card()
            # obj.customer = self
        if first_name:
            obj.first_name = first_name
        if last_name:
            obj.last_name = last_name
        if number:
            obj.number = number
        if cvv:
            obj.cvv = cvv
        if year:
            obj.expiration_year = year
        if month:
            obj.expiration_month = month
        obj.save()
        return obj

    def card_last_updated(self):
        if self.has_local_cards:
            return self.cards.all()[0].updated.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p")
        return ''

    def last_succ_charge_time(self):
        from ppars.apps.charge.models import Charge
        charge = Charge.objects.filter(customer=self.id,status='S').exclude(payment_getaway='CP')\
            .exclude(payment_getaway='CA').last()
        if not charge:
            return 'No charges were made'
        return charge.created.astimezone(timezone('US/Eastern')).strftime("%m/%d/%y %I:%M:%S%p")

    @property
    def get_charge_getaway(self):
        if self.charge_getaway:
            getaway = self.charge_getaway
        else:
            getaway = self.company.cccharge_type
        return getaway


class NoPhoneNumberSettings(Exception):
    pass


class PhoneNumber(models.Model):
    NoPhoneNumberSettings = NoPhoneNumberSettings

    company = fields.BigForeignKey(CompanyProfile)
    customer = fields.BigForeignKey(Customer, null=True)
    number = models.CharField(max_length=12)
    title = models.CharField(max_length=128, default='')
    use_for_sms_email = models.BooleanField(default=False)
    sms_gateway = models.ForeignKey('notification.SmsEmailGateway', default=1)

    @property
    def phone_number_settings(self):
        if PhoneNumberSettings.objects.filter(phone_number=self).exists():
            return PhoneNumberSettings.objects.get(phone_number=self)
        else:
            raise NoPhoneNumberSettings('No phone number settings.')

    def __unicode__(self):
        return u'%s' % self.number


class PhoneNumberSettings(models.Model):
    """
    Let's start separate new additional data, not always required in main model, to additional model with reference to
    main one. At least where we can, to not make thing even worse.
    We'll use it mainly via manager's method get_or_create,
    so when you adding new field try to always set default value for it
    """
    phone_number = models.ForeignKey(PhoneNumber, null=False, blank=False)
    bulk_promotion_subscription = models.BooleanField(default=True)

    def __unicode__(self):
        return u'%s settings' % self.number


class CarrierAdmin(models.Model):
    id = fields.BigAutoField(primary_key=True)
    company = fields.BigForeignKey(CompanyProfile, blank=True, null=True)
    carrier = fields.BigForeignKey(Carrier)
    username = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    created = models.DateTimeField(("Created at"), auto_now_add=True)
    updated = models.DateTimeField(verbose_name=("Updated at"), auto_now=True)
    # created = models.DateTimeField(("Created at"))
    # updated = models.DateTimeField(verbose_name=("Updated at"))

    def __unicode__(self):
        return u'%s' % self.carrier

    def get_absolute_url(self):
        return reverse('carrier_admin_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated


class AutoRefill(models.Model):
    MD = 'MD'
    MN = 'MN'
    AFTER_MID_NIGHT = '1201AM'
    ONE_AM = '1AM'
    ONE_HALF_HOUR_AM = '130AM'
    TWO_AM = '2AM'
    AM_AND_ONE_MINUET_PM = '12pm&1201am'

    SCHEDULE_TYPE_CHOICES = (
        (MD, 'Mid-Day'),
        (MN, '11:59 PM.'),
        (AFTER_MID_NIGHT, '12:01 AM.'),
        (ONE_AM, '1 AM.'),
        (ONE_HALF_HOUR_AM, '1:30 AM.'),
        (TWO_AM, '2 AM.'),
        (AM_AND_ONE_MINUET_PM, '12PM & 12:01AM'),
    )
    REFILL_FR = 'FR'
    REFILL_GP = 'GP'
    REFILL_TYPE_CHOICES = (
        (REFILL_FR, 'Full Refill/Topup'),
        (REFILL_GP, 'Get Pin'),
    )
    TRIGGER_MN = 'MN'
    TRIGGER_SC = 'SC'
    TRIGGER_AP = 'AP'
    TRIGGER_TYPE_CHOICES = (
        (TRIGGER_MN, 'Manual Refill'),
        (TRIGGER_SC, 'Scheduled Refill'),
        (TRIGGER_AP, 'API Refill'),
    )
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigForeignKey(User, null=True, on_delete=models.SET_NULL)
    company = fields.BigForeignKey(CompanyProfile, blank=True, null=True)
    customer = fields.BigForeignKey(Customer, related_name='autorefill')
    phone_number = models.CharField(max_length=12)
    plan = fields.BigForeignKey(Plan)
    refill_type = models.CharField(max_length=2, default=REFILL_FR, choices=REFILL_TYPE_CHOICES)
    renewal_date = models.DateField(blank=True, null=True)
    renewal_end_date = models.DateField(blank=True, null=True)
    renewal_interval = models.IntegerField(max_length=3, blank=True, null=True)
    last_renewal_status = models.CharField(max_length=50, null=True, blank=True)
    last_renewal_date = models.DateField(blank=True, null=True)
    schedule = models.CharField(max_length=11, choices=SCHEDULE_TYPE_CHOICES, default=MN, null=True, blank=True)
    notes = models.CharField(max_length=500, blank=True, null=True)
    trigger = models.CharField(max_length=2, choices=TRIGGER_TYPE_CHOICES, blank=True)
    pin = models.CharField(max_length=256, null=True, blank=True)
    enabled = models.BooleanField(default=True)
    created = models.DateTimeField(("Created at"), auto_now_add=True)
    updated = models.DateTimeField(verbose_name=("Updated at"), auto_now=True)
    pre_refill_sms = models.BooleanField(default=False)
    pre_refill_sms_number = models.CharField(max_length=12, null=True, blank=True)

    need_buy_pins = models.BooleanField(default=False)
    need_buy_pins_count = models.PositiveSmallIntegerField(default=0)
    send_bought_pins = models.BooleanField(default=False)

    # created = models.DateTimeField(("Created at"))
    # updated = models.DateTimeField(verbose_name=("Updated at"))

    def set_prerefill_phone_number_to_phone_number(self):
        if not self.pre_refill_sms_number:
            self.pre_refill_sms_number = self.phone_number

    def __unicode__(self):
        return u"%s" % self.id

    def get_absolute_url(self):
        return reverse('autorefill_list')

    def get_full_url(self):
        return '%s%s' % (settings.SITE_DOMAIN, reverse('autorefill_update', args=[self.pk]))

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated

    def check_twilio_confirm_sms(self):
        '''
        :param autorefill:
        :return: check if customer confirmed scheduled transaction
        '''
        if self.company.twilio_sid and \
                self.company.twilio_auth_token and \
                self.company.twilio_number:
            today = datetime.datetime.now(timezone('US/Eastern')).date()
            client = TwilioRestClient(self.company.twilio_sid, self.company.twilio_auth_token)
            # list of messages for last six days
            list_of_messages = client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=6)) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=5)) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=4)) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=3)) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=2)) + \
                               client.messages.list(to="+1%s" % self.company.twilio_number, from_=self.phone_number,
                                                    date_sent=today-timedelta(days=1))
            for sms in list_of_messages:  # if there were any messages with text 'yes' return True
                if sms.body.upper() == 'yes'.upper():
                    return True, str(sms.date_sent) + ' with message id: %s.' % str(sms.sid)
        return False, 'Transaction wasn\'t via SMS.'

    def create_charge(self, amount, tax):
        from ppars.apps.charge.models import Charge
        if self.customer.charge_getaway:
            getaway = self.customer.charge_getaway
        else:
            getaway = self.company.cccharge_type
        cc_charge = Charge.objects.create(
            company=self.company,
            autorefill=self,
            customer=self.customer,
            creditcard=self.customer.creditcard,
            payment_getaway=getaway,
            amount=amount,
            tax=tax
        )
        return cc_charge

    def check_renewal_end_date(self, today=None, commit=True):
        if not today:
            today = datetime.datetime.now(timezone('US/Eastern')).date()
        if self.renewal_end_date and self.renewal_end_date < today:
            self.enabled = False
            if commit:
                self.save()
        return self.enabled

    def set_renewal_date_to_next(self, today=None, commit=True):
        if not today:
            today = datetime.datetime.now(timezone('US/Eastern')).date()

        logger.debug('autorefill %s today %s' % (self, today))
        self.last_renewal_date = today
        if self.plan.carrier.renew_days:
            logger.debug('plan.carrier.renew_days %s' % self.plan.carrier.renew_days)
            self.renewal_date = today + timedelta(days=self.plan.carrier.renew_days)
        elif self.plan.carrier.renew_months:
            logger.debug('plan.carrier.renew_months %s' % self.plan.carrier.renew_months)
            self.renewal_date = today + relativedelta(months=self.plan.carrier.renew_months)
        if self.renewal_interval:
            logger.debug('self.renewal_interval %s' % self.renewal_interval)
            self.renewal_date = today + relativedelta(days=self.renewal_interval)
        if commit:
            self.save()

    def calculate_cost_and_tax(self):
        tax = decimal.Decimal(0.0)
        if self.customer.charge_getaway == Customer.DOLLARPHONE:
            return self.plan.plan_cost, tax

        selling_price = self.plan.get_plansellingprice(self.company, self.customer.selling_price_level)

        if self.need_buy_pins or (self.trigger == AutoRefill.TRIGGER_MN and self.refill_type == AutoRefill.REFILL_GP):
            count_pins = 1 if self.trigger == AutoRefill.TRIGGER_SC else self.need_buy_pins_count
            selling_price *= count_pins

        cost = selling_price - self.customer.customer_discount
        if self.customer.taxable:
            tax = self.company.tax
            cost = cost + cost * tax/decimal.Decimal(100)
        cost = cost.quantize(decimal.Decimal('.01'), rounding=decimal.ROUND_HALF_UP)
        return cost, tax

    def get_formated_charge_refill_date(self):
        charge_date = (self.renewal_date - timedelta(days=3)).strftime("%m/%d/%y").lstrip('0')
        refill_date = self.renewal_date.strftime("%m/%d/%y").lstrip('0')
        return charge_date, refill_date


class Transaction(models.Model):
    QUEUED = 'Q'
    PROCESS = 'P'
    RETRY = 'R'
    COMPLETED = 'C'
    INTERMEDIATE = 'I'

    SUCCESS = 'S'
    NO_FONDS = 'F'
    WAITING = 'W'
    ERROR = 'E'
    CR_NEW = 'N'

    MANUAL = 'MN'
    SCEDULED = 'SC'
    API = 'API'

    RESOLVED = 'R'
    NOT_RESOLVED = 'NR'
    NOT_AVAILABLE = 'NA'

    STATE_TYPE_CHOICES = (
        (QUEUED, 'Queued'),
        (PROCESS, 'In Process'),
        (RETRY, 'Retry'),
        (COMPLETED, 'Completed'),
        (INTERMEDIATE, 'Intermediate'),
    )
    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (NO_FONDS, 'No Fonds'),
        (WAITING, 'Waiting'),
        (ERROR, 'Error'),
        (CR_NEW, 'Created new transaction')
    )
    TRIGGER_TYPE_CHOICES = (
        (MANUAL, 'Manual Refill'),
        (SCEDULED, 'Scheduled Refill'),
        (API, 'API Refill'),
    )
    RESOLVED_TYPE_CHOICES = (
        (RESOLVED, 'Resolved'),
        (NOT_RESOLVED, 'Not resolved'),
        (NOT_AVAILABLE, 'N/a')
    )
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigForeignKey(User, null=True, on_delete=models.SET_NULL)
    company = fields.BigForeignKey(CompanyProfile, blank=True, null=True)
    plan_str = models.CharField(max_length=256, null=True)
    phone_number_str = models.CharField(max_length=12, null=True)
    customer_str = models.CharField(max_length=256, null=True)
    refill_type_str = models.CharField(max_length=256, null=True)
    autorefill = fields.BigForeignKey(AutoRefill, on_delete=models.SET_NULL, null=True)
    locked = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    completed = models.CharField(max_length=3, choices=RESOLVED_TYPE_CHOICES, blank=True, default='NA')
    pin_error = models.BooleanField(default=False)
    state = models.CharField(max_length=3, choices=STATE_TYPE_CHOICES, blank=True)
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES, null=True, blank=True)
    current_step = models.CharField(max_length=30, null=True, blank=True)
    adv_status = models.CharField(max_length=500, null=True, blank=True)
    cost = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    need_paid = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    create_asana_ticket = models.BooleanField(default=False)
    profit = models.DecimalField(max_digits=5, decimal_places=2, default=decimal.Decimal(0.0))
    pin = models.CharField(max_length=256, blank=True)
    sellercloud_order_id = models.CharField(max_length=200, blank=True, null=True)
    sellercloud_note_id = models.CharField(max_length=200, blank=True, null=True)
    sellercloud_payment_id = models.CharField(max_length=200, blank=True, null=True)
    retry_count = models.IntegerField(null=True, blank=True)
    customer_confirmation = models.BooleanField(default=False)
    transaction_note = models.TextField(null=True, blank=True)
    # We stored date in GMT but needs to use in US/Eastern
    started = models.DateTimeField("Started at", auto_now_add=True)
    # todo ftf? need to set default=None
    ended = models.DateTimeField(verbose_name="Ended at", auto_now=True)
    triggered_by = models.CharField(editable=False, max_length=128, default='System')
    trigger = models.CharField(max_length=50, editable=False, choices=TRIGGER_TYPE_CHOICES, blank=True, default='')

    charge_type_name = models.CharField(max_length=50, editable=False, blank=True, default='')
    charge_getaway_name = models.CharField(max_length=50, editable=False, blank=True, default='')

    bought_pins = models.PositiveSmallIntegerField(default=0)

    # general retry count for 'purchasing pins and add to unused'
    bought_pins_retry_count = models.PositiveSmallIntegerField(default=0)

    # retry count for special error from 'purchasing pins and add to unused'
    bought_pins_retry_count_err_token = models.PositiveSmallIntegerField(default=0)

    # this for autoupdate transaction details (value in seconds)
    retry_interval = models.PositiveIntegerField(null=True)

    # get pin now in manual refill
    get_pin_now = models.BooleanField(default=False)
    execution_time = models.DateTimeField(null=True)

    was_retried_on_step = models.BooleanField(default=False)

    # started = models.DateTimeField(("Started at"))
    # ended = models.DateTimeField(verbose_name=("Ended at"))

    def __unicode__(self):
        return u'%s' % self.id

    @property
    def customer(self):
        return self.autorefill.customer

    def save(self, *args, **kwargs):
        self.plan_str = self.autorefill.plan.plan_id
        self.phone_number_str = self.autorefill.phone_number
        self.customer_str = " ".join([self.autorefill.customer.first_name, self.autorefill.customer.middle_name or '', self.autorefill.customer.last_name])
        self.refill_type_str = self.autorefill.get_refill_type_display()
        # if self.cost == u'':
        #     self.cost = 0.0
        # if self.profit == u'':
        #     self.profit = 0.0
        super(Transaction, self).save(*args, **kwargs)

    def get_started_est(self):
        return self.started

    def get_ended_est(self):
        return self.ended

    def get_full_url(self):
        return '%s%s' % (settings.SITE_DOMAIN, reverse('transaction_detail', args=[self.pk]))

    def get_pin_url(self):
        if self.pin:
            data_pins = []
            # split multiple pins
            pins = self.pin.split(', ')

            for pin in pins:
                unused_pins = UnusedPin.objects.filter(pin=pin, company=self.company)
                if unused_pins:
                    for unused_pin in unused_pins:
                        data_pins.append('<a href="%s">%s</a>' % (unused_pin.get_full_url(), unused_pin))
                else:
                    data_pins.append('%s' % pin)
            return ', '.join(set(data_pins))

        return ''

    @property
    def get_last_used_charge(self):
        transaction_charge = self.charge_list().order_by('created').first()
        if transaction_charge:
            return transaction_charge.charge

    def charge_list(self):
        from ppars.apps.charge.models import TransactionCharge
        return TransactionCharge.objects.filter(transaction=self)

    def add_transaction_step(self, current_step, action, status, adv_status):
        TransactionStep.objects.create(
            operation=current_step,
            transaction=self,
            action=action,
            status=status,
            adv_status=adv_status
        )

    def cost_calculation(self):
        cost, tax = self.autorefill.calculate_cost_and_tax()
        self.cost = cost
        discount = 0
        if PlanDiscount.objects.filter(carrier=self.autorefill.plan.carrier,
                                       plan=self.autorefill.plan, company=self.company).exists():
            discount = PlanDiscount.objects.get(carrier=self.autorefill.plan.carrier,
                                                plan=self.autorefill.plan, company=self.company).discount
        elif PlanDiscount.objects.filter(carrier=self.autorefill.plan.carrier, plan=None,
                                         company=self.company).exists():
            discount = PlanDiscount.objects.get(carrier=self.autorefill.plan.carrier, plan=None,
                                                company=self.company).discount
        self.profit = self.cost * (discount/100)
        self.save()
        return cost, tax

    def check_sms_confirmation(self):
        check_twilio_confirm_sms, confirm_log = self.autorefill.check_twilio_confirm_sms()
        if check_twilio_confirm_sms:
            TransactionStep.objects.create(operation='Checking for sms confirmation',
                                           transaction=self,
                                           action='Check sms confirmation',
                                           status='S',
                                           adv_status='Transaction confirmed via SMS on %s' % confirm_log)
            return True
        else:
            TransactionStep.objects.create(operation='Checking for sms confirmation',
                                           transaction=self,
                                           action='Check sms confirmation',
                                           status='S',
                                           adv_status='Canceled. Transaction wasn`t confirmed via SMS')
            return False

    def send_payment_to_sellercloud_order(self):
        if settings.TEST_MODE:
            TransactionStep.objects.create(operation='Create send_payment_to_sellercloud_order in TEST MODE',
                                           transaction=self,
                                           action='Begin',
                                           status='S',
                                           adv_status='Begin send_payment_to_sellercloud_order in TEST MODE')
            return
        if self.sellercloud_payment_id:
            TransactionStep.objects.create(operation='send payments to SellerCloud',
                                           transaction=self,
                                           action='Check',
                                           status='S',
                                           adv_status='Payments for order %s already exist' % self.sellercloud_order_id)
            return
        if self.paid:
            client = SoapClient(wsdl="http://kc.ws.sellercloud.com/OrderCreationService.asmx?WSDL", trace=True,
                                ns=False)
            xmlns="http://api.sellercloud.com/"
            header = SimpleXMLElement('<Headers/>', )
            security = header.add_child("AuthHeader")
            security['xmlns'] = xmlns
            security.marshall('UserName', self.user.get_company_profile().sc_email)
            security.marshall('Password', self.user.get_company_profile().sc_password)
            client['AuthHeader'] = security
            if self.customer.charge_type == 'CC':
                payment_method = 'CreditCard'
            else:
                payment_method = 'Cash'
            response = client.Orders_AddPaymentToOrder(
                OrderID=u'%s' % self.sellercloud_order_id,
                amount=self.cost,
                paymentMethod=payment_method,
            )
            result = response['Orders_AddPaymentToOrderResult']
            TransactionStep.objects.create(operation='send payments to SellerCloud',
                                           transaction=self,
                                           action='send payments',
                                           status='S',
                                           adv_status='Order payments <a href="http://kc.cwa.sellercloud.com/'
                                                      'Orders/Orders_Details.aspx?Id=%s" target="_blank" >'
                                                      '%s</a> created successfully' %
                                                      (self.sellercloud_order_id, self.sellercloud_order_id),)
            self.sellercloud_payment_id = result
            self.save()

    def send_note_to_sellercloud_order(self):
        if settings.TEST_MODE:
            TransactionStep.objects.create(operation='Create send_note_to_sellercloud_order in TEST MODE',
                                           transaction=self,
                                           action='Begin',
                                           status='S',
                                           adv_status='Begin send_note_to_sellercloud_order in TEST MODE')
            return
        if self.sellercloud_note_id:
            return
        client = SoapClient(wsdl="http://kc.ws.sellercloud.com/OrderCreationService.asmx?WSDL", trace=True,
                            ns=False)
        xmlns = "http://api.sellercloud.com/"
        header = SimpleXMLElement('<Headers/>', )
        security = header.add_child("AuthHeader")
        security['xmlns'] = xmlns
        security.marshall('UserName', self.user.get_company_profile().sc_email)
        security.marshall('Password', self.user.get_company_profile().sc_password)
        client['AuthHeader'] = security
        note = u'transaction:  %s  transaction status: %s' % (self.get_full_url(), self.adv_status)
        order = u'%s' % self.sellercloud_order_id
        response = client.CreateOrderNote(OrderId=order, note=note)
        self.sellercloud_note_id = response['CreateOrderNoteResult']
        self.save()

    def send_tratsaction_to_sellercloud(self):
        if settings.TEST_MODE:
            TransactionStep.objects.create(operation='Create SellerCloud order in TEST MODE',
                                           transaction=self,
                                           action='Begin',
                                           status='S',
                                           adv_status='Begin create SellerCloud order in TEST MODE')
            return
        if not (self.company.sc_company_id and self.company.sc_email
                and self.company.sc_password):
            TransactionStep.objects.create(operation='send_to_sc',
                                           transaction=self,
                                           action='get authorization token',
                                           status='E',
                                           adv_status='Please check SellerCloud authorization tokens')
            return
        if self.sellercloud_order_id:
            TransactionStep.objects.create(operation='Create SellerCloud order',
                                           transaction=self,
                                           action='Check',
                                           status='S',
                                           adv_status='SellerCloud order already exist')
            return
        TransactionStep.objects.create(operation='Create SellerCloud order',
                                       transaction=self,
                                       action='Begin',
                                       status='S',
                                       adv_status='Begin create SellerCloud order')
        client = SoapClient(wsdl="http://kc.ws.sellercloud.com/OrderCreationService.asmx?WSDL", trace=False,
                            ns=False)
        xmlns = "http://api.sellercloud.com/"
        header = SimpleXMLElement('<Headers/>', )
        security = header.add_child("AuthHeader")
        security['xmlns'] = xmlns
        security.marshall('UserName', self.user.get_company_profile().sc_email)
        security.marshall('Password', self.user.get_company_profile().sc_password)
        client['AuthHeader'] = security
        as_first_name = self.customer.first_name
        as_last_name = self.customer.last_name
        phone_title = PhoneNumber.objects.get(customer=self.customer, number=self.phone_number_str).title
        if phone_title and len(phone_title.split(' ')) > 1:
            as_first_name = phone_title.split(' ')[0]
            as_last_name = phone_title.split(' ')[1]
        elif phone_title:
            as_first_name = phone_title
        email = ''
        if self.customer.primary_email:
            email = self.customer.primary_email
        elif PhoneNumber.objects.filter(customer=self.customer, use_for_sms_email=True).exists():
            email = '%s@%s' % (PhoneNumber.objects.filter(customer=self.customer,
                                                          use_for_sms_email=True)[0].number,
                               PhoneNumber.objects.filter(customer=self.customer,
                                                          use_for_sms_email=True)[0].sms_gateway.gateway)
        new_order = {
            u'LockShippingMethod': True,
            u'OrderCreationSourceApplication': 'Default',
            # u'Customer_TaxID': <type 'str'>,
            # u'Customer_TaxExempt': <type 'bool'>,
            # u'CouponCode': <type 'str'>,
            # u'TaxRate': <class 'decimal.Decimal'>,
            # u'ParentOrderID': <type 'int'>,
            # u'ShipFromWarehouseId': <type 'int'>,
            # u'SalesRepId': <type 'int'>,
            u'DiscountTotal':  self.profit,
            # u'RushOrder': <type 'bool'>,
            # u'Payments': [
            #         {u'OrderPaymentDetails':
            #            {
            #             # u'StoreCouponOrGiftCertificateID': <type 'int'>,
            #             u'Amount':  self.cost,
            #             u'PaymentMethod': payment_method,
            #             u'CreditCardType': None,
            #             # u'CreditCardNumber': <type 'str'>,
            #             # u'CreditCardSecurityCode': <type 'str'>,
            #             # u'CreditCardCVV2Response': <type 'str'>,
            #             # u'CreditCardCardExpirationMonth': <type 'int'>,
            #             # u'CreditCardCardExpirationYear': <type 'int'>,
            #             u'PaymentFirstName': self.customer.first_name,
            #             u'PaymentLastName': self.customer.last_name,
            #             u'PaymentTransactionID': self.id,
            #             u'PaymentStatus': 'Cleared',
            #             u'PaymentClearanceDate': self.ended,
            #             u'PaymentEmailAddress': self.customer.primary_email
            # }}
            # ],
            u'Items': [
                {u'OrderItemDetails': {
                    # u'ShipType': <type 'str'>,
                    # u'ReturnReason': <type 'str'>,
                    # u'ShipFromWarehouseID': <type 'int'>,
                    # u'ExportedProductID': <type 'str'>,
                    # u'VariantID': <type 'long'>,
                    # u'SalesOutlet': <type 'str'>,
                    u'SerialNumbers': [{u'string': u'%s' % self.pin}],
                    # u'DiscountTotal': <class 'decimal.Decimal'>,
                    u'DiscountAmount':  self.profit,
                    # u'DiscountType': <type 'str'>,
                    # u'QtyReturned': <type 'int'>,
                    # u'QtyShipped': <type 'int'>,
                    # u'OrderItemUniqueIDInDB': <type 'int'>,
                    u'SKU': self.autorefill.plan.sc_sku,
                    u'ItemName': self.autorefill.plan.plan_name,
                    u'Qty': 1,
                    # u'OrderSourceItemID': <type 'str'>,
                    # u'OrderSourceTransactionID': <type 'str'>,
                    u'UnitPrice': self.cost,
                    u'ShippingPrice': 0.0,
                    u'SubTotal':  self.cost,
                    u'Notes': u''
                }}
            ],
            # u'Packages': [
            #    {u'OrderPackageDetails': {
            #        u'Carrier': <type 'str'>,
            #        u'ShipMethod': <type 'str'>,
            #        u'TrackingNumber': <type 'str'>,
            #        u'ShipDate': <type 'datetime.datetime'>,
            #        u'FinalShippingCost': <class 'decimal.Decimal'>,
            #        u'ShippingWeight': <class 'decimal.Decimal'>,
            #        u'ShippingWidth': <class 'decimal.Decimal'>,
            #        u'ShippingLength': <class 'decimal.Decimal'>,
            #        u'ShippingHeight': <class 'decimal.Decimal'>
            #    }}
            # ],
            u'CompanyID': self.user.get_company_profile().sc_company_id,
            u'OrderSource': 'Local_Store',
            u'OrderSourceOrderID': self.id,
            u'OrderDate': datetime.datetime.now(timezone('US/Eastern')),
            u'CustomerFirstName': self.customer.first_name,
            u'CustomerLastName': self.customer.last_name,
            u'CustomerEmail': email,
            u'BillingAddressFirstName': as_first_name,
            u'BillingAddressLastName': as_last_name,
            # u'BillingAddressCompany': <type 'str'>,
            u'BillingAddressStreet1': self.customer.address,
            # u'BillingAddressStreet2': <type 'str'>,
            u'BillingAddressCity': self.customer.city,
            u'BillingAddressState': self.customer.state,
            u'BillingAddressZipCode': self.customer.zip,
            u'BillingAddressCountry': "United States",
            # u'BillingAddressPhone': <type 'str'>,
            u'ShippingAddressFirstName': as_first_name,
            u'ShippingAddressLastName': as_last_name,
            # u'ShippingAddressCompany': <type 'str'>,
            u'ShippingAddressStreet1': self.customer.address,
            # u'ShippingAddressStreet2': <type 'str'>,
            u'ShippingAddressCity': self.customer.city,
            u'ShippingAddressState': self.customer.state,
            u'ShippingAddressZipCode': self.customer.zip,
            u'ShippingAddressCountry': "United States",
            u'ShippingAddressPhone': u'%s' % self.phone_number_str,
            # u'ShippingMethod': <type 'str'>,
            # u'ShippingCarrier': <type 'str'>,
            # u'CustomerComments': <type 'str'>,
            u'ShippingStatus': 'FullyShipped',
            u'PaymentStatus': 'NoPayment',
            u'SubTotal':  self.cost,
            # u'TaxTotal': <class 'decimal.Decimal'>,
            # u'ShippingTotal': <class 'decimal.Decimal'>,
            # u'GiftWrapTotal': <class 'decimal.Decimal'>,
            # u'AdjustmentTotal': <class 'decimal.Decimal'>,
            u'GrandTotal':  self.cost,
            }
        response = client.CreateNewOrder(order=new_order)
        result = response['CreateNewOrderResult']
        TransactionStep.objects.create(operation='send transaction to SellerCloud',
                                       transaction=self,
                                       action='create order',
                                       status='S',
                                       adv_status='SC order <a href="http://kc.cwa.sellercloud.com/Orders/Orders_Details.aspx?Id=%s"'
                                                  ' target="_blank" >%s</a> created successfully' % (result, result),)
        self.sellercloud_order_id = result
        self.save()

    def send_asana(self):
        if settings.TEST_MODE:
            self.add_transaction_step('notification',
                                      'Asana',
                                      SUCCESS,
                                      'TEST MODE')
            return

        if not (self.company.asana_api_key and self.company.asana_workspace
                and self.company.asana_project_name
                and self.company.asana_user):
            self.add_transaction_step('notification',
                                      'Asana',
                                      ERROR,
                                      'Please check asana authorization tokens')
            return

        if self.paid:
            self.add_transaction_step('notification',
                                      'Asana',
                                      SUCCESS,
                                      'Refill was paid. Order wasn`t created')
            return

        if self.create_asana_ticket:
            self.add_transaction_step('notification',
                                      'Asana',
                                      SUCCESS,
                                      'Order already exists')
            return

        project_name = self.company.asana_project_name
        workspace = int(self.company.asana_workspace)
        user = self.company.asana_user
        tag_name = ''
        title = '%s-%s' % (self.customer.sc_account, self.customer_str)
        note = '%s \nphone number %s\nrefill type: %s\ncost %s$\ncharge type: %s \n' \
               'http://kc.cwa.sellercloud.com/Orders/Orders_Details.aspx?Id=%s\n' \
               'http://kc.cwa.sellercloud.com/Users/User_Orders.aspx?ID=%s' \
               % (self.customer_str, self.phone_number_str, self.autorefill.get_refill_type_display(),
                  self.cost, self.customer.get_charge_type_display(), self.customer.sc_account,
                  self.customer.sc_account)

        asana_api = asana.AsanaAPI(self.company.asana_api_key, debug=True)
        projects = asana_api.list_projects(workspace=workspace, include_archived=False)
        # print 'projects %s' %projects

        project_id = None
        for pr in projects:
            # print 'project %s' % pr
            if project_name == pr['name']:
                project_id = pr['id']
                break
        else:
            project = asana_api.create_project(project_name, workspace)
            project_id = project['id']
        # print 'project_id %s' % project_id

        data = []
        data.append(project_id)
        # print 'dictionary %s' %data

        tasks = asana_api.get_project_tasks(project_id, include_archived=False)
        # print 'tasks %s' %tasks

        task_id = None
        for ts in tasks:
            # print 'task %s' % ts
            if title == ts['name']:
                task_id = ts['id']
                task = asana_api.get_task(task_id)
                if not task['completed']:
                    notes = '%s \n%s' % (task['notes'], note)
                    asana_api.update_task(task_id, notes=notes, assignee=user)
                    break
        else:
            task = asana_api.create_task(
                title,
                workspace,
                assignee=user,
                assignee_status='later',
                # completed=False,
                # due_on=None,
                # followers=None,
                notes=note,
                projects=data,
            )
            task_id = task['id']
        # print 'task_id %s' %task_id

        # tags = asana_api.get_tags(workspace)
        # tag_id = None
        # for tg in tags:
        #     # print 'tag %s' % tg
        #     if tag_name == tg['name']:
        #         tag_id = tg['id']
        #         break
        # else:
        #     try:
        #         tag = asana_api.create_tag(tag_name, workspace)
        #         tag_id = tag['id']
        #     except asana.AsanaException, msg:
        #         print msg
        #
        # # print 'tag_id %s' %tag_id
        # try:
        #     asana_api.add_tag_task(task_id, tag_id)
        # except asana.AsanaException, msg:
        #         print msg
        self.create_asana_ticket = True
        self.save()
        self.add_transaction_step('notification',
                                  'Asana',
                                  SUCCESS,
                                  'Asana order created successfully')

    def log_error_in_asana(self, error):
        if settings.TEST_MODE:
            return

        try:
            admin_company = CompanyProfile.objects.get(superuser_profile=True)
            if not admin_company.use_asana:
                return
            project_name = admin_company.asana_project_name
            workspace = int(admin_company.asana_workspace)
            current_time = datetime.datetime.now(pytz.timezone('US/Eastern')).strftime("%m/%d/%y %H:%M:%S")
            title = 'Transaction %s' % self
            note = '[%s] step: %s\n %s' % (current_time, self.current_step, error)
            asana_api = asana.AsanaAPI(admin_company.asana_api_key, debug=False)
            #[{u'id': 16428561128039, u'name': u'PY3PI INC'}, {u'id': 6456132996391, u'name': u'e-zoffer.com'}, {u'id': 498346170860, u'name': u'Personal Projects'}]
            projects = asana_api.list_projects(workspace=workspace, include_archived=False)
            for pr in projects:
                # print 'project %s' % pr
                if project_name == pr['name']:
                    project_id = pr['id']
                    break
            else:
                project = asana_api.create_project(project_name, workspace)
                project_id = project['id']
            data = []
            data.append(project_id)
            tasks = asana_api.get_project_tasks(project_id, include_archived=False)
            for ts in tasks:
                # print 'task %s' % ts
                if title == ts['name']:
                    task_id = ts['id']
                    task = asana_api.get_task(task_id)
                    if not task['completed']:
                        notes = '%s \n%s' % (task['notes'], note)
                        asana_api.update_task(task_id, notes=notes)
                        break
            else:
                asana_api.create_task(
                    title,
                    workspace,
                    assignee_status='later',
                    followers=[12955112053049],
                    notes=u'%s\n%s' % (self.get_full_url(), note),
                    projects=data,
                )
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))

    @property
    def get_parent_transaction(self):
        return TransactionCreatedFromTo.objects.get(transaction_to=self)

    @property
    def get_child_transactions(self):
        return TransactionCreatedFromTo.objects.filter(transaction_from=self)

    def add_pin_to_unused(self, plan, pin):
        unused_pin = UnusedPin.objects.create(
            company=self.company,
            plan=plan,
            pin=str(pin),
            used=False,
            notes='Pin bought from transaction %s' % self.get_full_url())
        self.add_transaction_step(
            'get pin',
            'end',
            SUCCESS,
            u'Purchased pin <a href="%s">%s</a> and added to unused' %
            (unused_pin.get_full_url(), pin)
        )



class TransactionStep(models.Model):
    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (NO_FONDS, 'No Fonds'),
        (WAITING, 'Waiting'),
        (ERROR, 'Error'),
    )
    id = fields.BigAutoField(primary_key=True)
    transaction = fields.BigForeignKey(Transaction, related_name='step')
    operation = models.CharField(max_length=200)
    action = models.CharField(max_length=200)
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES)
    adv_status = models.CharField(max_length=500, null=True)
    created = models.DateTimeField("Timestamp", auto_now=True)

    # created = models.DateTimeField(("Timestamp"))

    def __unicode__(self):
        return self.operation

    def get_created_est(self):
        return self.created


class TransactionError(models.Model):
    transaction = fields.BigForeignKey(Transaction)
    step = models.CharField(max_length=50)
    message = models.CharField(max_length=500)
    created = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return u'%s [%s]' % (self.step, self.created)


class TransactionCreatedFromTo(models.Model):
    transaction_from = fields.BigForeignKey(Transaction, related_name='original_transaction')
    transaction_to = fields.BigForeignKey(Transaction, related_name='similar_transaction')

    created = models.DateTimeField("Started at", auto_now_add=True)


class UnusedPin(models.Model):
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigForeignKey(User, null=True, on_delete=models.SET_NULL)
    company = fields.BigForeignKey(CompanyProfile, blank=True, null=True)
    plan = fields.BigForeignKey(Plan)
    transaction = fields.BigForeignKey(Transaction, null=True, blank=True)
    pin = models.CharField(max_length=256)
    used = models.BooleanField()
    notes = models.CharField(max_length=500, blank=True)
    created = models.DateTimeField("Started at", auto_now_add=True)
    updated = models.DateTimeField(verbose_name="Ended at", auto_now=True)

    # created = models.DateTimeField(("Started at"))
    # updated = models.DateTimeField(verbose_name=("Ended at"))

    def get_full_url(self):
        return '%s%s' % (settings.SITE_DOMAIN, reverse('unusedpin_update', args=[self.pk]))

    def __unicode__(self):
        return self.pin

    def get_absolute_url(self):
        return reverse('unusedpin_list')

    def get_created_est(self):
        return self.created

    def get_updated_est(self):
        return self.updated


class CaptchaLogs(models.Model):
    id = fields.BigAutoField(primary_key=True)
    user = fields.BigForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    user_name = models.CharField(max_length=200, blank=True, null=True)
    customer = fields.BigForeignKey(Customer, null=True, blank=True, on_delete=models.SET_NULL)
    customer_name = models.CharField(max_length=200, blank=True, null=True)
    carrier = fields.BigForeignKey(Carrier, null=True, blank=True)
    carrier_name = models.CharField(max_length=200, blank=True, null=True)
    plan = fields.BigForeignKey(Plan, null=True, blank=True)
    plan_name = models.CharField(max_length=200, blank=True, null=True)
    refill_type = models.CharField(max_length=200, blank=True, null=True)
    transaction = fields.BigForeignKey(Transaction, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)

    # created = models.DateTimeField()

    def __unicode__(self):
        return u'%s' % self.id

    def get_created_est(self):
        return self.created

    def get_string(self):
        return 'User %s used %s: %s for customer %s. It was %s. <a href="%s">See transaction</a><br/>' % \
               (self.user, self.carrier, self.plan, self.customer, self.created, self.transaction.get_full_url())


class CommandLog(models.Model):
    id = fields.BigAutoField(primary_key=True)
    command = models.CharField(max_length=256)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    # created = models.DateTimeField()

    def __unicode__(self):
        return u'%s' % self.command


class ImportLog(models.Model):
    id = fields.BigAutoField(primary_key=True)
    company = fields.BigForeignKey(CompanyProfile, null=True)
    command = models.CharField(max_length=256)
    message = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.command


class ConfirmDP(models.Model):
    id = fields.BigAutoField(primary_key=True)
    login = models.CharField(max_length=256)
    password = models.CharField(max_length=256)
    confirm = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True)

    # created = models.DateTimeField()

    def __unicode__(self):
        return u'%s' % self.created


class PinReport(models.Model):
    SUCCESS = 'S'
    ERROR = 'E'
    STATUS_TYPE_CHOICES = (
        (SUCCESS, 'Success'),
        (ERROR, 'Error'),
    )
    company = fields.BigForeignKey(CompanyProfile, null=True)
    subject = models.CharField(max_length=100, blank=True)
    report = models.TextField()
    status = models.CharField(max_length=3, choices=STATUS_TYPE_CHOICES, default=SUCCESS)
    created = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return u'%s' % self.id


class PinField(models.Model):
    pin_report = models.ForeignKey(PinReport)
    pin = models.CharField(max_length=30)
    plan = models.CharField(max_length=100, blank=True)
    cost = models.DecimalField(max_digits=5, decimal_places=2, null=True)
    note = models.CharField(max_length=200, blank=True)
    used = models.BooleanField(default=False)

    def __unicode__(self):
        return u'%s' % self.pin


class News(models.Model):
    CATEGORIES = (
        ('BF', 'Bug Fix'),
        ('NF', 'New Features'),
        ('IN', 'Instructions/FAQ'),
        ('OP', 'Optional Paid Futures'),
        ('EZ', 'E-Z Cloud News'),
        ('UU', 'Urgent Update')
    )
    title = models.CharField(max_length=150, blank=True)
    category = models.CharField(max_length=2, choices=CATEGORIES)
    message = models.TextField(blank=True)
    created = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            company.show_updates = True
            company.save()
        super(News, self).save(*args, **kwargs)

    def __unicode__(self):
        return '[' + self.get_category_display() + '] ' + self.title

    class Meta:
        verbose_name_plural = "News"


class WrongResultRedFin(models.Model):
    user_profile = fields.BigForeignKey(UserProfile, null=True)
    customer = fields.BigForeignKey(Customer, null=True)
    phone_number = models.ForeignKey(PhoneNumber, null=True)
    contract_amount = models.CharField(max_length=10, blank=True)


def notify_admin(sender, instance, created, **kwargs):
    if created:
        instance.set_selling_prices()


signals.post_save.connect(notify_admin, sender=CompanyProfile)


@receiver(post_save, sender=Plan)
def set_selling_prices(instance, created, **kwargs):
    if created:
        instance.set_selling_prices()


@receiver(pre_save, sender=AutoRefill)
def set_prerefill_phone_number_to_phone_number(instance, **kwargs):
    instance.set_prerefill_phone_number_to_phone_number()


@receiver(pre_save, sender=Customer)
def pre_save_customer(instance, sender, **kwargs):
    instance.set_primary_email_to_lowercase()
    if instance.pk:
        new_company = instance.company.id
        old_company = sender.objects.get(pk=instance.pk).company.id
        if new_company != old_company:
            from ppars.apps.charge.models import Charge
            for transaction in Transaction.objects.filter(autorefill__customer=instance):
                if transaction.company.id != instance.company.id:
                    transaction.company = instance.company
                    transaction.save()
            for autorefill in AutoRefill.objects.filter(customer=instance):
                if autorefill.company.id != instance.company.id:
                    autorefill.company = instance.company
                    autorefill.save()
            for charge in Charge.objects.filter(customer=instance):
                if charge.company.id != instance.company.id:
                    charge.company = instance.company
                    charge.save()


@receiver(post_save, sender=PhoneNumber)
def post_phone_number(instance, **kwargs):
    PhoneNumberSettings.objects.get_or_create(phone_number=instance)



@receiver(post_save, sender=Customer)
def post_save_customer(instance, **kwargs):
    if not instance.zip:
        instance.zip = instance.company.default_zip
    # Sets first name and last name 'unknown' to customer if those are blank or null:
    if not instance.first_name:
        instance.first_name = 'unknown'
    if not instance.last_name:
        instance.last_name = 'unknown'
    if instance.company.can_send_welcome_emails and instance.send_status != 'NO' and not instance.welcomed:
        from ppars.apps.notification.tasks import send_welcome_email
        send_welcome_email.apply_async(args=[instance], countdown=15*60)
        instance.welcomed = True



@receiver(post_save, sender=News)
def post_save_news(instance, created, **kwargs):
    if instance.category == 'UU' and created:
        from ppars.apps.core.tasks import send_urgent_updates
        send_urgent_updates.delay(instance.id)
        for user_profile in UserProfile.objects.filter(show_urgent=False):
            user_profile.show_urgent = True
            user_profile.save()


@receiver(pre_save, sender=CompanyProfile)
def set_default_license_expiries(instance, **kwargs):
    instance.set_default_license_expiries()


# @receiver(post_save, sender=Customer)
# def set_sms_email_to_first_phone_number(instance, created, **kwargs):
#     instance.set_sms_email_to_first_phone_number()


@receiver(pre_delete, sender=AutoRefill)
def set_trigger_of_all_related_transactions(instance, **kwargs):
    for transaction in Transaction.objects.filter(autorefill=instance):
        transaction.trigger = instance.get_trigger_display() + ' ' + str(instance.id)
        transaction.save()


@receiver(post_save, sender=TransactionStep)
def update_transaction_resolved(instance, **kwargs):
    if instance.status == 'E':
        instance.transaction.completed = 'NR'
        instance.transaction.save()


list_of_models = (
    'CompanyProfile', 'Customer', 'Carrier', 'CarrierAdmin', 'Plan', 'PhoneNumber',
    'PlanDiscount', 'AutoRefill', 'CreditCardCharge', 'UnusedPin', 'User', 'Transaction'
)

@receiver(pre_save)
def logging_update(sender, instance, **kwargs):
    if instance.pk and sender.__name__ in list_of_models:
        from django.forms.models import model_to_dict

        company = None
        user_str = "System"

        if 'company' in dir(instance) and instance.company and type(instance.company) == CompanyProfile:
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

        if 'company' in dir(instance) and instance.company and type(instance.company) == CompanyProfile:
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

        if 'company' in dir(instance) and instance.company and type(instance.company) == CompanyProfile:
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


# DO NOT DELETE. IT IS FOR SIGNALS
from . import receivers
