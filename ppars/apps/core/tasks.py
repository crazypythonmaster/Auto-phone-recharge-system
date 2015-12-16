import functools
import logging
from datetime import datetime, timedelta, time
import traceback
import decimal
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
import pytz
from ppars.apps.core import dealer_red_pocket, dealer_page_plus, dealer_airvoice, dealer_h2o, dealer_pvc_approvedlink
from ppars.apps.core.company_notifications import send_customer_import_status, send_autorefill_import_status
from ppars.apps.core.redfin import enter_contract_list_page, get_cc_data, \
    get_customer_data, deactivate_contract, log_in_redfin
from ppars.apps.core.redfin import get_tokens
from ppars.apps.notification.models import SmsEmailGateway, NewsMessage
from ppars.apps.price.models import SellingPriceLevel
from ppars.apps.tzones.functions import crontab_with_correct_tz
import requests
from BeautifulSoup import BeautifulSoup
from ppars.apps.core.prerefill import PreRefill
from ppars.apps.core.send_notifications import \
    failed_check_refunds_customer_notification, notification_about_verify_schedules
from pysimplesoap.client import SoapClient
from requests.auth import HTTPBasicAuth
from celery import task
from celery.task import periodic_task
from django_redis import get_redis_connection
from refill import Refill
from models import Customer, AutoRefill, Transaction, UnusedPin, \
    ImportLog, CompanyProfile, PhoneNumber, PinReport, Plan, Log, News,\
    PinField, CarrierAdmin, CommandLog, WrongResultRedFin

logger = logging.getLogger(__name__)


# US/Eastern is -4 h from GMT
# cron:
#
# - description: Scheduled Refill Midnight Job
#   url: /cron/scheduled-refill?schedule=MN
#   schedule: every day 23:59
#   timezone: America/New_York
#
# - description: Scheduled Refill Midday Job
#   url: /cron/scheduled-refill?schedule=MD
#   schedule: every day 12:00
#   timezone: America/New_York
#
# - description: Scheduled Refill 12:01 AM Job
#   url: /cron/scheduled-refill?schedule=1201AM
#   schedule: every day 00:01
#   timezone: America/New_York
#
# - description: Scheduled Refill 1 AM Job
#   url: /cron/scheduled-refill?schedule=1AM
#   schedule: every day 1:00
#   timezone: America/New_York
#
# - description: Scheduled Refill 1:30 AM Job
#   url: /cron/scheduled-refill?schedule=130AM
#   schedule: every day 1:30
#   timezone: America/New_York
#
# - description: Scheduled Refill 2 AM Job
#   url: /cron/scheduled-refill?schedule=2AM
#   schedule: every day 2:00
#   timezone: America/New_York
#
# - description: Pre CC Charge Job
#   url: /cron/pre-cc-charge
#   schedule: every day 4:00
#   timezone: America/New_York


# description: Scheduled Refill 12:00 PM
@periodic_task(run_every=crontab_with_correct_tz(hour=12, minute=00))
def am_and_one_pm_job():
    schedule_refill(schedule=AutoRefill.AM_AND_ONE_MINUET_PM)


# description: Scheduled Refill Midnight Job 23:59
@periodic_task(run_every=crontab_with_correct_tz(hour=23, minute=59))
def midnight_job():
    schedule_refill(schedule=AutoRefill.MN)


# description: 00:55 by US/Eastern
@periodic_task(run_every=crontab_with_correct_tz(hour=00, minute=00))
def scheduled_refills_disabling():
    today = datetime.now(pytz.timezone('US/Eastern')).date() - timedelta(days=1)
    for autorefill in AutoRefill.objects.filter(enabled=True,
                                                trigger=AutoRefill.TRIGGER_SC,
                                                renewal_end_date=today):
        autorefill.enabled = False
        autorefill.save()


# description: Scheduled Refill 12:01 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=00, minute=01))
def after_midday_job():
    schedule_refill(schedule=AutoRefill.AFTER_MID_NIGHT)


# description: Scheduled Refill 1 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=01, minute=00))
def one_hour_day_job():
    schedule_refill(schedule=AutoRefill.ONE_AM)


# description: Scheduled Refill 1:30 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=01, minute=30))
def one_hour_with_half_day_job():
    schedule_refill(schedule=AutoRefill.ONE_HALF_HOUR_AM)


# description: Scheduled Refill 2 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=02, minute=00))
def two_hour_day_job():
    schedule_refill(schedule=AutoRefill.TWO_AM)


# description:  3 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=03, minute=00))
def check_refunds_job():
    check_refunds()


# description: 11:59 AM
@periodic_task(run_every=crontab_with_correct_tz(hour=11, minute=59))
def midday_job():
    schedule_refill(schedule=AutoRefill.MD)


# description: Prepered Scheduled Refill 14:00 by US/Eastern
@periodic_task(run_every=crontab_with_correct_tz(hour=14, minute=00))
def prerefill_job():
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    tomorrow = today + timedelta(days=1)
    start_date = datetime.combine(today - timedelta(days=7), time.min)
    logger.debug('%s, %s', today, tomorrow, )
    autorefills = AutoRefill.objects.filter(enabled=True, trigger=AutoRefill.TRIGGER_SC, renewal_date=tomorrow).exclude(plan__plan_type=Plan.DOMESTIC_TOPUP)
    logger.debug('make_prerefill')
    i = 0
    for autorefill in autorefills:
        if Transaction.objects.filter(autorefill=autorefill, started__gt=start_date):
            transaction = Transaction.objects.filter(autorefill=autorefill, started__gt=start_date)[0]
            logger.debug('Found previous prerefill transaction:  %s' % transaction)
        else:
            if not autorefill.check_renewal_end_date(today=tomorrow):
                # return self.enabled
                # if False == not enabled then skip autorefill
                continue
            logger.debug('make transaction for autorefill %s', autorefill)
            transaction = Transaction.objects.create(user=autorefill.user,
                                                     autorefill=autorefill,
                                                     state="Q",
                                                     company=autorefill.company,
                                                     triggered_by='System')
        logger.debug('run trans %s', transaction)
        transaction.state = Transaction.PROCESS
        transaction.save()
        queue_prerefill.apply_async(args=[transaction.id], countdown=10*i)
        i += 1


@task
def queue_prerefill(transaction_id):
    PreRefill(transaction_id).main()


@task
def queue_refill(transaction_id):
    Refill(transaction_id).main()


@task
def schedule_time_add_on(transaction_id):
    Refill(transaction_id).recharge_phone()


def schedule_refill(schedule):
    # We stored date in GMT but needs to use in US/Eastern
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    start_date = datetime.combine(today - timedelta(days=7), time.min)

    for autorefill in AutoRefill.objects.filter(enabled=False,
                                                trigger=AutoRefill.TRIGGER_SC,
                                                renewal_date=today,
                                                schedule=schedule):
        autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)

    autorefills = AutoRefill.objects.filter(enabled=True,
                                            trigger=AutoRefill.TRIGGER_SC,
                                            renewal_date=today,
                                            schedule=schedule)
    logger.debug('%s Full Refills list^ %s' % (schedule, list(autorefills)))
    for autorefill in autorefills:
        logger.debug('Full Refill^ %s' % autorefill)
        if Transaction.objects.filter(autorefill=autorefill, started__gt=start_date):
            transaction = Transaction.objects.filter(autorefill=autorefill, started__gt=start_date)[0]
            logger.debug('Found transaction:  %s' % transaction)
        else:
            if not autorefill.check_renewal_end_date(today=today):
                logger.debug('check_renewal_end_date False: today %s' % today)
                continue
            transaction = Transaction.objects.create(user=autorefill.user,
                                                     autorefill=autorefill,
                                                     state="Q",
                                                     company=autorefill.company,
                                                     triggered_by='System')
            logger.debug('Created transaction:  %s' % transaction)
        autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)
        if transaction.completed == 'R':
            logger.debug('transaction resolved:  %s' % transaction)
            continue
        if autorefill.need_buy_pins and transaction.pin:
            transaction.state = Transaction.COMPLETED
            transaction.save()
            logger.debug('SC transaction for buy pin and add to unused:  %s' % transaction)
            continue
        transaction.state = Transaction.PROCESS
        transaction.save()
        logger.debug('transaction started:  %s' % transaction)
        queue_refill.delay(transaction.id)


def single_instance_task(timeout):
    def task_exc(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            lock_id = "celery-single-instance-" + func.__name__
            con = get_redis_connection("default")
            with con.lock(lock_id, timeout=timeout):
                ret_value = func(*args, **kwargs)
            return ret_value
        return wrapper
    return task_exc


@single_instance_task(60*10)
def get_unused_pin(plan, company):
    unused_pin = UnusedPin.objects.filter(company=company, plan=plan, used=False)
    if unused_pin:
        unused_pin = unused_pin[0]
        unused_pin.used = True
        unused_pin.save()
        return unused_pin


@task
def check_refunds():
    from ppars.apps.charge.models import Charge
    # check refunds for success
    start_date = datetime.combine(datetime.today() - timedelta(days=2), time.min)
    end_date = datetime.combine(datetime.today(), time.max)
    for cc in Charge.objects.filter(status='R', refunded__range=(start_date, end_date)):
        if not cc.refund_status or cc.refund_status == cc.ERROR or cc.refund_status == cc.PROCESS:
            cc.check_refund()
    # send email
    start_date = datetime.combine(datetime.today() - timedelta(days=3), time.min)
    end_date = datetime.combine(datetime.today() - timedelta(days=3), time.max)
    for cc in Charge.objects.filter(status='R', refunded__range=(start_date, end_date), refund_status='E'):
        failed_check_refunds_customer_notification(cc)


@task
def queue_customer_import(cache_data):
    result = list()
    user = cache_data['user']
    company = user.profile.company

    send_status_types = {send_status_type[1]: send_status_type[0] for send_status_type in Customer.SEND_STATUS_CHOICES}
    charge_types = {charge_type[1]: charge_type[0] for charge_type in Customer.CHARGE_TYPE_CHOICES}
    gateway_types = {gateway_type[1]: gateway_type[0] for gateway_type in Customer.CHARGE_GETAWAY_CHOICES}
    level_prices = {'%s' % level_price: level_price for level_price in SellingPriceLevel.objects.all()}
    customers = {'%s' % customer: customer for customer in Customer.objects.filter(company=user.profile.company)}

    for customer in cache_data['customers']:
        msg = ''
        try:
            customer['user'] = user
            customer['company'] = company
            customer['first_name'] = customer['first_name']
            customer['middle_name'] = customer['middle_name'] or ''
            customer['last_name'] = customer['last_name']
            customer['primary_email'] = customer['primary_email'] or ''
            customer['sc_account'] = customer['sellercloud_account_id'] or ''
            del customer['sellercloud_account_id']
            customer['address'] = customer['address'] or ''
            customer['city'] = customer['city'] or ''
            customer['state'] = customer['state'] or ''
            customer['zip'] = customer['zip'] or ''
            customer['charge_type'] = charge_types[customer['charge_type'] or 'Cash']
            customer['charge_getaway'] = gateway_types[customer['charge_gateway'] or company.get_cccharge_type_display() or 'Cash(PrePayment)']
            del customer['charge_gateway']
            customer['creditcard'] = customer['card_number'] or ''
            del customer['card_number']
            customer['authorize_id'] = customer['authorize_id'] or ''
            customer['usaepay_customer_id'] = customer['usaepay_customer_id'] or ''
            customer['usaepay_custid'] = customer['usaepay_custid'] or ''
            customer['selling_price_level'] = level_prices[customer['selling_price_level'] or '1 level price']
            customer['customer_discount'] = customer['customer_discount'] or '0.00'
            customer['taxable'] = bool(customer['taxable'] and customer['taxable'].upper() == 'TRUE')
            customer['precharge_sms'] = bool(customer['precharge_sms'] and customer['precharge_sms'].upper() == 'TRUE')
            customer['email_success_refill'] = bool(customer['email_success_refill']
                                                    and customer['email_success_refill'].upper() == 'TRUE')
            customer['email_success_charge'] = bool(customer['email_success_charge']
                                                    and customer['email_success_charge'].upper() == 'TRUE')
            customer['send_status'] = send_status_types[customer['send_status'] or company.get_send_status_display() or 'Don\'t Send']
            customer['send_pin_prerefill'] = send_status_types[customer['send_pin_prerefill'] or company.get_send_pin_prerefill_display() or 'Don\'t Send']
            customer['group_sms'] = bool(customer['group_sms'] and customer['group_sms'].upper() == 'TRUE')
            customer['enabled'] = bool(customer['enabled'] and customer['enabled'].upper() == 'TRUE')
            customer['notes'] = customer['notes'] or ''
            phone_numbers = customer['phone_numbers']
            del customer['phone_numbers']

            this_customer = customers.get(" ".join([customer['first_name'], customer['middle_name']or '', customer['last_name']]))
            if this_customer:
                for prop in customer:
                    setattr(this_customer, prop, customer[prop])
            else:
                this_customer = Customer(**customer)
            this_customer.save()
            msg = this_customer.check_duplicate_number(phone_numbers)
            customer['phone_numbers'] = phone_numbers
            customer['import_status'] = 'Customer imported successfully. %s' % msg
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            customer['import_status'] = 'Customer not imported. %s %s' % (e, msg)
        finally:
            logger.debug(customer['import_status'])
            result.append(customer)
    send_customer_import_status(company, result)


@task
def queue_autorefill_import(cache_data):
    schedule_types = dict()
    customers = dict()
    result = list()
    # super_profile = UserProfile.objects.filter(superuser_profile=True)
    # super_profile = super_profile[0].company
    for schedule_type in AutoRefill.SCHEDULE_TYPE_CHOICES:
        schedule_types[schedule_type[1]] = schedule_type[0]
    user = cache_data['user']
    # for customer in Customer.objects.filter(company=user.profile.company):
    #     customers['%s' % customer] = customer
    company = user.profile.company
    exists = AutoRefill.objects.filter(trigger=AutoRefill.TRIGGER_SC, company=user.profile.company).count()
    schedule_limit = company.schedule_limit
    if company.schedule_limit != 0 and (exists + len(cache_data['autorefills'])) > schedule_limit:
        send_autorefill_import_status(schedule_limit, user.get_company_profile())
    else:
        for autorefill in cache_data['autorefills']:
            if 'S' == autorefill.pop('status'):
                autorefill.pop('result')
                logger.debug('import autorefill %s' % autorefill)
                try:
                    autorefill['user'] = user
                    autorefill['company'] = user.profile.company
                    autorefill['trigger'] = AutoRefill.TRIGGER_SC
                    autorefill['refill_type'] = AutoRefill.REFILL_FR
                    autorefill['schedule'] = schedule_types[autorefill['schedule']]
                    autorefill['pre_refill_sms'] = False
                    if autorefill['enabled'].upper() == 'TRUE':
                        autorefill['enabled'] = True
                    else:
                        autorefill['enabled'] = False
                    AutoRefill.objects.create(**autorefill)
                    autorefill['import_status'] = 'Success'
                except Exception, e:
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                    autorefill['import_status'] = 'Error %s' % e
                finally:
                    result.append(autorefill)
        send_autorefill_import_status(0, user.get_company_profile(), result)


@task
def queue_import_customers_from_usaepay(company, user, usaepay_account):
    if not settings.TEST_MODE:
        from ppars.apps.price.models import SellingPriceLevel
        level_price = SellingPriceLevel.objects.get(level='1')
        message = ''
        added = 0
        exists = 0
        not_added = 0
        found = 0
        if '1' == usaepay_account:
            if company.usaepay_username and company.usaepay_password:
                usaepay_username = company.usaepay_username
                usaepay_password = company.usaepay_password
            else:
                message = 'no USAePay username/password.'
            if company.usaepay_source_key and company.usaepay_pin:
                token = company.usaepay_authorization()
            else:
                message = 'no USAePay tokens'

        elif '2' == usaepay_account:
            if company.usaepay_username_2 and company.usaepay_password_2:
                usaepay_username = company.usaepay_username_2
                usaepay_password = company.usaepay_password_2
            else:
                message = 'no USAePay[2] username/password.'
            if company.usaepay_source_key_2 and company.usaepay_pin_2:
                token = company.usaepay_authorization_2()
            else:
                message = 'no USAePay[2] tokens'
        else:
            message = 'Undefined USAePay account'
        if message:
            ImportLog.objects.create(
                company=company,
                command='USAePay for user %s' % company,
                message=message,
                )
            return
        try:
            s = requests.Session()
            r = s.get('https://secure.usaepay.com/login')
            soup = BeautifulSoup(r.text)
            stamp = soup.find('input', {'name': 'stamp'}).get('value')
            payload = {'username': usaepay_username,
                       'password': usaepay_password,
                       'stamp': stamp
                       }

            r = s.post('https://secure.usaepay.com/login', data=payload)
            if r.url not in 'https://secure.usaepay.com/console/batch':
                raise Exception("Failed to login to USAePay, please check credentials")
            r = s.get('https://secure.usaepay.com/console/billing?limitstart=0&limit=2000&filter=&sortkey=&sortdir=&level=&type=')

            # r = s.post('https://sandbox.usaepay.com/login', data=payload)
            # if r.url not in ['https://sandbox.usaepay.com/console/']:
            #     raise Exception("Failed to login to USAePay, please check credentials")
            # r = s.get('https://sandbox.usaepay.com/console/billing?limitstart=0&limit=2000&filter=&sortkey=&sortdir=&level=&type=')

            soup2 = BeautifulSoup(r.text)
            forms = soup2.findAll('form')
            usaepay_customers = []
            for form in forms:
                if form.get('name') == 'custs':
                    inputs = soup2.findAll('input')
                    if 'javascript:editCustomer' not in r.text:
                        for obj in inputs:
                            if obj.get('name') == 'sel[]':
                                usaepay_customers.append(obj.get('value'))
                    else:
                        for a in form.findAll('a'):
                            if 'javascript:editCustomer' in a.get('href'):
                                usaepay_customers.append(int(a.get('href').replace('javascript:editCustomer(\'', '').replace('\')', '')))

            found = len(usaepay_customers)
            system_customers = Customer.objects.filter(company=company)
            for customer in system_customers:
                usaepay_customer_id = None
                if '1' == usaepay_account and customer.usaepay_customer_id:
                    usaepay_customer_id = customer.usaepay_customer_id
                elif '2' == usaepay_account and customer.usaepay_customer_id_2:
                    usaepay_customer_id = customer.usaepay_customer_id_2
                if usaepay_customer_id and usaepay_customer_id in usaepay_customers:
                    usaepay_customers.remove(usaepay_customer_id)
            exists = found - len(usaepay_customers)

            if not usaepay_customers:
                message = 'All USAePay users already exist in your system'
            else:
                for usaepay_customer in usaepay_customers:
                    try:
                        client = SoapClient(wsdl=settings.USAEPAY_WSDL,
                                            trace=False,
                                            ns=False)
                        response = client.getCustomer(CustNum=usaepay_customer, Token=token)
                        result = response['getCustomerReturn']
                        if result:
                            first_name = ''
                            last_name = ''
                            enabled = False
                            city = ''
                            zip = ''
                            state = ''
                            address = ''
                            primary_email = ''
                            creditcard = ''
                            usaepay_custid = ''
                            company_name = ''
                            pns = []
                            logger.debug('Notes "%s"' % result['Notes'])
                            if 'Notes' in result and result['Notes']:
                                pns = extract_phone_numbers_from_notes(result['Notes'])
                            if 'Enabled' in result and result['Enabled']:
                                enabled = result['Enabled']
                            if 'BillingAddress' in result:
                                if 'City' in result['BillingAddress'] and result['BillingAddress']['City']:
                                    city = result['BillingAddress']['City'].strip()
                                if 'Zip' in result['BillingAddress'] and result['BillingAddress']['Zip']:
                                    zip = result['BillingAddress']['Zip'].strip()
                                if 'FirstName' in result['BillingAddress'] and result['BillingAddress']['FirstName']:
                                    first_name = result['BillingAddress']['FirstName'].strip()
                                if 'LastName' in result['BillingAddress'] and result['BillingAddress']['LastName']:
                                    last_name = result['BillingAddress']['LastName'].strip()
                                if 'Company' in result['BillingAddress'] and result['BillingAddress']['Company']:
                                    company_name = result['BillingAddress']['Company'].strip()
                                logger.debug('Phone "%s"' % result['BillingAddress']['Phone'])
                                if 'Phone' in result['BillingAddress'] and result['BillingAddress']['Phone']:
                                    for n in extract_phone_numbers_from_notes(result['BillingAddress']['Phone']):#.strip().replace('-', '').replace(' ', '')
                                        if n not in pns:
                                            pns.append(n)
                                if 'State' in result['BillingAddress'] and result['BillingAddress']['State']:
                                    state = result['BillingAddress']['State'].strip()
                                if 'Street' in result['BillingAddress'] and result['BillingAddress']['Street']:
                                    address = result['BillingAddress']['Street'].strip()
                                if 'Email' in result['BillingAddress'] and result['BillingAddress']['Email']:
                                    primary_email = result['BillingAddress']['Email'].strip()
                            if 'PaymentMethods' in result:
                                if len(result['PaymentMethods']) > 0:
                                    if 'item' in result['PaymentMethods'][0]:
                                        item = result['PaymentMethods'][0]['item']
                                        creditcard = str(item.CardNumber)
                            if 'CustomerID' in result and result['CustomerID']:
                                p = result['CustomerID']
                                for tok in [', ', '. ', ' ', ',', '.']:
                                    p = p.replace(tok, '|')
                                p = p.replace('|', ', ').strip()
                                if ',' != p[-1:]:
                                    p = '%s,' % p
                                usaepay_custid = p
                            new_customer = Customer.objects.create(usaepay_customer_id=usaepay_customer,
                                                                   user=user,
                                                                   company=company,
                                                                   charge_getaway='U',
                                                                   charge_type='CC',
                                                                   creditcard=creditcard,
                                                                   first_name=first_name or company_name or str(usaepay_customer),
                                                                   last_name=last_name or str(usaepay_customer),
                                                                   enabled=enabled,
                                                                   city=city,
                                                                   zip=zip,
                                                                   selling_price_level=level_price,
                                                                   state=state,
                                                                   address=address,
                                                                   primary_email=primary_email,
                                                                   )
                            if '1' == usaepay_account:
                                new_customer.usaepay_custid=usaepay_custid
                            elif '2' == usaepay_account:
                                new_customer.usaepay_custid_2=usaepay_custid
                            new_customer.save()
                            for number in pns:
                                PhoneNumber.objects.create(company=company,
                                                           customer=new_customer,
                                                           number=number)
                            added = added + 1
                            message = 'This is customer from USAePay. Please ' \
                                      'check them out.  <a href="%s">%s</a><br/>%s' %\
                                      (reverse('customer_update', args=[new_customer.id]),
                                       new_customer,
                                       message)
                    except Exception, e:
                        not_added = not_added + 1
                        message = 'Customer with ID "%s" did`t added. Error:%s<br/>%s' % (usaepay_customer, e, message)
            message = ('%s customers added, %s customers exists, %s not added of %s<br/><br/>%s' %
                   (added, exists, not_added, found, message)
                   )
        except Exception, e:
            message = '%s<br/><br/>%s' % (message, e)
        finally:
            ImportLog.objects.create(
                company=company,
                command='USAePay for user %s' % company,
                message=message,
                )


def extract_phone_numbers_from_notes(s):
    pn = ''
    pns = []
    part = ''
    result = s.strip().replace('-', '')
    for token in s.replace('-', ''):
        if token in (' ', '\n', '\t'):
            if len(part) > 10:
                result = result.replace(part, '')
            part = ''
        else:
            part = '%s%s' % (part, token)
    for token in result.replace(' ', ''):
        if token.isdigit():
            pn = '%s%s' % (pn, token)
        else:
            if pn and 10 == len(pn) and pn not in pns:
                pns.append(pn)
            pn = ''
    if pn and 10 == len(pn) and pn not in pns:
        pns.append(pn)
    return pns


@task(expires=1200)
def queue_import_customers_from_redfin(company, user):
    t = datetime.now()
    if settings.TEST_MODE:
        redfin_url = 'https://staging.redfinnet.com/admin/'
    else:
        redfin_url = 'https://secure.redfinnet.com/admin/'
    message = ''
    added = 0
    exists = 0
    not_added = 0
    customers_for_scheduled = []
    customer_id = []
    try:
        s = log_in_redfin(company.redfin_username, company.redfin_password)
        r, s = enter_contract_list_page(s, redfin_url, status='1', payment_preference='CC')
        soup = BeautifulSoup(r.text)
        quantity = int(soup.find('span', {'id': 'ItemNumber'}).text.split('Found: ')[1].split('Displaying')[0])
        if quantity % 250:
            parts = quantity / 250 + 1
        else:
            parts = quantity / 250

        for part in range(1, parts+1):
            logger.debug('PART %s' % part)
            start = 1
            end = 10
            if part == 1:
                start = 0
                end = 9
            for page in range(start, end + 1):
                logger.debug('PAGE %s' % page)
                r, s = enter_contract_list_page(s, redfin_url, status='1', payment_preference='CC')
                if part > 1:
                    payload = get_tokens(r.text)
                    payload.pop('__VIEWSTATEGENERATOR')
                    payload['__EVENTTARGET'] = 'ContractGrid$_ctl1$_ctl%s' % (end)
                    r = s.post('%srecurring/view_contracts.aspx' % redfin_url, data=payload)
                if part > 2:
                    p = 2
                    while p < part:
                        payload = get_tokens(r.text)
                        payload.pop('__VIEWSTATEGENERATOR')
                        payload['__EVENTTARGET'] = 'ContractGrid$_ctl1$_ctl%s' % (end + 1)
                        r = s.post('%srecurring/view_contracts.aspx' % redfin_url, data=payload)
                        p = p + 1
                payload = get_tokens(r.text)
                payload.pop('__VIEWSTATEGENERATOR')
                payload['__EVENTTARGET'] = 'ContractGrid$_ctl1$_ctl%s' % page
                r = s.post('%srecurring/view_contracts.aspx' % redfin_url, data=payload)
                soup = BeautifulSoup(r.text)
                logger.debug('REALPAGE %s' % soup.findAll('tr', {'class': 'gridPager'})[0].find('span').text if 'gridPager' in r.text else '1')
                for tr in soup.findAll('tr'):
                    try:
                        # taking customers by line
                        if tr.get('class') in (u'gridRow', u'gridAltRow'):
                            i = 1
                            # taking customer data
                            for td in tr.findAll('td'):
                                if 2 == i:
                                    phone_number = td.text.replace('.', '')
                                    contract_url = td.find('a').get('href')
                                    bill_amount, deact_msg = deactivate_contract(s, redfin_url, contract_url)
                                    if deact_msg:
                                        message = 'Contract for next customer is active, because system show "%s" %s' % (deact_msg, message)
                                    custId = contract_url.split('aspx?id=')[1].split('&')[0].replace('.', '')
                                    if custId not in customer_id:
                                        # logger.debug('CUSTOMER %s' % custId)
                                        customer_id.append(custId)
                                    else:
                                        logger.debug('DUPLICATED %s %s' % (custId, td.text))
                                        break
                                    if Customer.objects.filter(redfin_customer_key=custId):
                                        customer = Customer.objects.filter(redfin_customer_key=custId).first()
                                        if Customer.USAEPAY != customer.charge_getaway or (Customer.USAEPAY == customer.charge_getaway and not customer.usaepay_customer_id):
                                            customer.charge_type = Customer.CREDITCARD
                                            customer.charge_getaway = Customer.REDFIN
                                            customer.save()
                                        exists = exists + 1
                                        break
                                    if contract_url:
                                        try:
                                            # customer nonpayment data
                                            r = s.get('%srecurring/add.aspx?id=%s' % (redfin_url, custId))
                                            customer_data = get_customer_data(r.text)
                                            creditcard = ''
                                            redfin_cc_info_key = ''
                                            cc_notes = ''
                                            customer_cc_data = {}
                                            try:
                                                cc_href = ''
                                                # customer credit card
                                                r = s.get('%srecurring/view_customer.aspx?id=%s' % (redfin_url, custId))
                                                soup = BeautifulSoup(r.text)
                                                for a in soup.findAll('a'):
                                                    if a.get('id') and 'EditPaymentLink' in a.get('id'):
                                                        cc_href = a.get('href')
                                                        if 'type=CC' in cc_href:
                                                            break
                                                if cc_href:
                                                    r = s.get('%srecurring/%s' % (redfin_url, cc_href))
                                                    redfin_cc_info_key = cc_href.split('paymentid=')[1].split('&type')[0]
                                                    customer_cc_data = get_cc_data(r.text)
                                                else:
                                                    logger.debug('No customer_cc_data:')
                                            except Exception, e:
                                                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                                            if customer_cc_data:
                                                creditcard = customer_cc_data['card_number']
                                                cc_notes = ' card exp: %s,' \
                                                           'card name: %s, ' \
                                                           'card adrress: %s, ' \
                                                           'card zip: %s,' % (
                                                    customer_cc_data['card_exp'],
                                                    customer_cc_data['card_name'],
                                                    customer_cc_data['card_adrress'],
                                                    customer_cc_data['card_zip'],
                                                )
                                            pn = None
                                            if phone_number:
                                                pns = PhoneNumber.objects.filter(company=company, number=phone_number).exclude(customer=None)
                                                ms = []
                                                if pns.count() > 1:
                                                    for ph in pns:
                                                        m = '<a href="%s">%s</a>' % (reverse('customer_update', args=[ph.customer.id]), ph.customer)
                                                        ms.append(m)
                                                    message = 'Customers %s have same number %s. Please, make this phone number unique and restart import<br/>%s' % (', '.join(ms), phone_number, message)
                                                    not_added = not_added + 1
                                                    break
                                                elif pns.count() == 1:
                                                    pn = pns.first()
                                                    pn.title = 'rf'
                                                    pn.save()
                                            if pn:
                                                customer = pn.customer
                                                if not customer.creditcard:
                                                    customer.creditcard=creditcard
                                                customer.redfin_customer_key = custId
                                                customer.redfin_cc_info_key = redfin_cc_info_key
                                                customer.notes = 'title: %s, department: %s, day phone: %s, night phone: %s, fax: %s, street address 2: %s, street address 3: %s, province: %s%s' % (
                                                        customer_data['title'],
                                                        customer_data['department'],
                                                        customer_data['day_phone'],
                                                        customer_data['night_phone'],
                                                        customer_data['fax'],
                                                        customer_data['street_address_2'],
                                                        customer_data['street_address_3'],
                                                        customer_data['province'],
                                                        cc_notes)
                                                if Customer.USAEPAY != customer.charge_getaway or (Customer.USAEPAY == customer.charge_getaway and not customer.usaepay_customer_id):
                                                    customer.charge_type=Customer.CREDITCARD
                                                    customer.charge_getaway=Customer.REDFIN
                                                message = 'Customer <a href="%s">%s</a> was updated with RedFinNetwork tokens<br/>%s' % (reverse('customer_update', args=[customer.id]), customer, message)
                                                customer.save()
                                                exists = exists + 1
                                            else:
                                                customer = Customer.objects.create(
                                                    user=user,
                                                    company=company,
                                                    first_name=customer_data['first_name'] or 'Walk-in',
                                                    middle_name='',
                                                    last_name=customer_data['last_name'] or 'Customer',
                                                    primary_email=customer_data['email'] or '',
                                                    address=customer_data['street_address_1'],
                                                    city=customer_data['city_name'],
                                                    state='',
                                                    zip=customer_data['zip_code'] or '',
                                                    charge_type=Customer.CREDITCARD,
                                                    charge_getaway=Customer.REDFIN,
                                                    creditcard=creditcard,
                                                    redfin_customer_key=custId,
                                                    redfin_cc_info_key=redfin_cc_info_key,
                                                    notes='title: %s, '
                                                          'department: %s, '
                                                          'day phone: %s, '
                                                          'night phone: %s, '
                                                          'fax: %s, '
                                                          'street address 2: %s,  '
                                                          'street address 3: %s, '
                                                          'province: %s%s' % (
                                                        customer_data['title'],
                                                        customer_data['department'],
                                                        customer_data['day_phone'],
                                                        customer_data['night_phone'],
                                                        customer_data['fax'],
                                                        customer_data['street_address_2'],
                                                        customer_data['street_address_3'],
                                                        customer_data['province'],
                                                        cc_notes)
                                                )
                                                if phone_number:
                                                    PhoneNumber.objects.create(
                                                        company=company,
                                                        customer=customer,
                                                        number=phone_number,
                                                        title='rf')
                                                if customer_data['mobile']:
                                                    PhoneNumber.objects.create(
                                                        company=company,
                                                        customer=customer,
                                                        number=customer_data['mobile'],
                                                        title='mobile')
                                                added = added + 1
                                                message = 'This is customer from RedFinNetwork. Please check them out. <a href="%s">%s</a><br/>%s' % (reverse('customer_update', args=[customer.id]), customer, message)
                                            customers_for_scheduled.append([customer.id, phone_number, bill_amount])
                                        except Exception, e:
                                            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                                            not_added = not_added +1
                                            return
                                    else:
                                        not_added = not_added + 1
                                        logger.debug('No contract_url: %s' % r.text)
                                    break
                                i += 1
                    except Exception, e:
                        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            r, s = enter_contract_list_page(s, redfin_url, status='1', payment_preference='CC')
            payload = get_tokens(r.text)
            payload.pop('__VIEWSTATEGENERATOR')
            payload['__EVENTTARGET'] = 'ContractGrid$_ctl1$_ctl%s' % (end + 1)
            r = s.post('%srecurring/view_contracts.aspx' % redfin_url, data=payload)
        message = ('%s customers added, %s customers exists, %s not added of %s<br/><br/>%s' %
               (added, exists, not_added, quantity, message)
               )
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        message = '%s<br/><br/>%s' % (message, e)
    finally:
        ImportLog.objects.create(
            company=company,
            command='RedFin for user %s' % company,
            message=message,
            )
        t2 = datetime.now()
        logger.debug('time1 %s' % (t2 - t))
        CommandLog.objects.create(command='REDFIN Number', message=customers_for_scheduled)
        WrongResultRedFin.objects.filter(
            user_profile=user.profile).delete() #need for restart
        start = 0
        while start < len(customers_for_scheduled):
            end = start + 100
            auto_creation_schedules_refill.delay(customers_for_scheduled[start: end], user.profile)
            start = start + 100
        t3 = datetime.now()
        logger.debug('time1 %s time %s' % ((t2 - t), (t3 - t)))


@task
def queue_import_phone_numbers(company, rows):
    if not settings.TEST_MODE:
        message = ''
        added = 0
        exists = 0
        not_added = 0
        for row in rows:
            try:
                phone_number = int(row[3])
                customers = Customer.objects.filter(company=company, usaepay_custid__contains='%s,' % row[0])
                if not customers.exists():
                    message = '%s<br/>CustID "%s" don`t associate for any customer.' % (message, row[0])
                    not_added += 1
                    continue
                if customers.count() > 1:
                    customer_list = []
                    for customer in customers:
                        customer_list.append('<a href="%s">%s</a>' % (reverse('customer_update',
                                                                              args=[customer.id]),
                                                                      customer))
                    message = '%s<br/>%s associate for CustID "%s". ' \
                              'Phone number don`t added. Please, change CustId and try again' %\
                              (message,
                               ', '.join(customer_list),
                               row[0])
                    not_added += 1
                    continue
                customer = customers[0]
                phonenumbers = PhoneNumber.objects.filter(company=company, number=str(phone_number))
                note = []
                if phonenumbers:
                    for number in phonenumbers:
                        note.append('<a href="%s">%s</a>' % (reverse('customer_update',
                                                                     args=[number.customer.id]),
                                                             number.customer))
                    cust_ex = ', '.join(note)
                    message = '%s<br/>Number "%s" can not be added to <a href="%s">%s</a>.' \
                              ' It is already exists for %s' % \
                              (message,
                               phone_number,
                               reverse('customer_update', args=[customer.id]),
                               customer,
                               cust_ex)
                    exists += 1
                    continue
                if str(phone_number) not in phonenumbers.values_list('number', flat=True):  # TODO: test
                    PhoneNumber.objects.create(customer=customer, company=company, number=phone_number)
                    message = '%s<br/>Number "%s" was added to customer <a href="%s">%s</a>' % (message,
                                                                                                phone_number,
                                                                                                reverse('customer_update',
                                                                                                        args=[customer.id]), customer)
                    added += 1
                else:
                    message = '%s<br/>Number "%s" already exists for <a href="%s">%s</a>' % (message,
                                                                                             phone_number,
                                                                                             reverse('customer_update',
                                                                                                     args=[customer.id]),
                                                                                             customer)
                    exists += 1
            except Exception, e:
                message = '%s<br/><br/>%s<br/>' % (message, e)
                not_added += 1
        message = ('%s numbers added, %s numbers exists, %s not added of %s<br/><br/>%s' %
                   (added, exists, not_added, len(rows), message)
                   )
        ImportLog.objects.create(
            company=company,
            command='Phone numbers for %s' % company,
            message=message,
        )


@task
def queue_compare_pins_with_dollarphone(company_id):
    if not settings.TEST_MODE:
        from ppars.apps.charge.models import Charge

        report = 'Problem to login to Dollar Phone. Check company settings.'
        url = 'https://www.dollarphonepinless.com/sign-in'
        end = '{d.month}/{d.day}/{d.year}/'.format(d=datetime.now())
        s = requests.Session()
        company = CompanyProfile.objects.get(id=company_id)
        status = PinReport.SUCCESS

        if PinReport.objects.filter(company=company):
            start = PinReport.objects.filter(company=company, status=PinReport.SUCCESS).order_by('created').last().created.date().strftime("%m/%d/%Y")
        else:
            start = '01/01/2010'
        pin_report = PinReport.objects.create(
            company=company,
            subject='Pin report from %s to %s' % (start, end),
            report='',
            status=status,)
        try:
            r = s.get(url, auth=HTTPBasicAuth(company.dollar_user, company.dollar_pass))
            soup2 = BeautifulSoup(r.text)
            options = soup2.findAll('option')
            statements_url = ''
            for option in options:
                if option.text == 'Statements':
                    statements_url = option.get('value')
                    break
            if statements_url:
                s.get(statements_url)
                s.get('https://reports.dollarphonepinless.com/statements/?sid=%s' % statements_url.split('sid=')[1])
                s.get('https://reports.dollarphonepinless.com/statements/tree.aspx')
                r = s.get('https://reports.dollarphonepinless.com/statements/nodes.ashx?id=')
                soup = BeautifulSoup(r.text)
                node = soup.find('li', 'jstree-open').get('id')
                r = s.get('https://reports.dollarphonepinless.com/statements/transactions.aspx?id=%s&from=%s&to=%s' % (
                    node, start, end))
                soup = BeautifulSoup(r.text)
                if soup.find('h2'):
                    if soup.find('h2').text == '&nbsp; Too Many Records':
                        r = s.get(
                            'https://reports.dollarphonepinless.com/statements/transactions.aspx?id=%s&from=%s&to=%s&force=1' % (
                                node, start, end))
                        soup = BeautifulSoup(r.text)
                try:
                    table = soup.find("table", attrs={"id": "treewindowtable"})
                    table_body = table.find('tbody')
                    rows = table_body.findAll('tr')
                    for row in rows:
                        try:
                            cols = row.findAll('td')
                            cols = [ele.text.strip() for ele in cols]
                            if 'rtr' in cols[3].lower():
                                continue
                            if UnusedPin.objects.filter(pin=cols[2], company=company) or \
                                    Transaction.objects.filter(pin=cols[2], company=company) or \
                                    Charge.objects.filter(pin=cols[2], company=company):
                                continue
                            pin = cols[2]
                            plan = cols[3]
                            cost = decimal.Decimal(cols[5].replase('$', '').strip())
                            PinField.objects.create(pin_report=pin_report, pin=pin, plan=plan, cost=cost)
                        except Exception, e:
                            pin_report.report = '%s' % e
                except Exception, e:
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
                    if soup.find('div', id='core').find('h2').text == 'No Records Found':
                        pin_report.report = 'No Records Found. %s' % soup.find('div', id='core').find('p').text
        except Exception, e:
                pin_report.report = e
                pin_report.status = PinReport.ERROR
        finally:
            pin_report.save()


@task
def back_from_logs(user):
    logs = []
    for log in Log.objects.filter(company=user.profile.company, created__gte=datetime(2015, 07, 1, 0, 0, 0, 0),
                                  note__icontains='PRECHARGE SMS: '):
        try:
            if 'updated Customer' in log.note and 'PRECHARGE SMS:' in log.note:
                customer_first_name = log.note[(log.note.find('Customer') + 10):].split('\n')[0].split(' ')[0]
                customer_last_name = log.note[(log.note.find('Customer') + 10):].split('\n')[0].split(' ')[2]
                if log.note.split('\n')[1][20] == 'F':
                    precharge_sms_before = False
                else:
                    precharge_sms_before = True
                customer = Customer.objects.filter(first_name=customer_first_name, last_name=customer_last_name)[0]
                # logger.log('\nCustomer name: %s\nCustomer last name: %s\nPrecharge sms: %s\n' % (customer.first_name, customer.last_name, customer.precharge_sms))
                if customer:
                    customer.precharge_sms = precharge_sms_before
                    customer.save()
        except Exception, e:
            logger.log('%s' % e)
        finally:
            pass


@task(expires=3600)
def auto_creation_schedules_refill(customer_and_numbers, userprofile):
    success = []
    wrong_numbers_page_plus = []
    wrong_result_red_pocket = []
    wrong_result = []
    plans = []
    failed_login = []
    duplicate_schedule = []
    carrier_admin_page_plus = \
        CarrierAdmin.objects.filter(company=userprofile.company,
                                    carrier__name__icontains='PAGE PLUS CELLULAR'
                                    ).get()
    carrier_admin_red_pocket = \
        CarrierAdmin.objects.filter(company=userprofile.company,
                                    carrier__name__icontains='RED POCKET'
                                    ).get()
    try:
        for customer_and_number in customer_and_numbers:
            customer = Customer.objects.filter(id=customer_and_number[0])
            if customer:
                customer_and_number[0] = customer[0]
        try:
            auth_pp = dealer_page_plus.login_pageplus(carrier_admin_page_plus.username, carrier_admin_page_plus.password)
            if not auth_pp['valid']:
                raise Exception(auth_pp['error'])
            br = auth_pp['browser']
        except Exception, e:
            failed_login.append('PagePlus failed login! ')
            wrong_numbers_page_plus = customer_and_numbers
            customer_and_numbers = []
        for customer_and_number in customer_and_numbers:
            try:
                result = dealer_page_plus.verify_pageplus(customer_and_number[1], br)
                if result['valid_for_schedule']:
                    if not (AutoRefill.objects.filter(
                            customer=customer_and_number[0],
                            trigger='SC',
                            phone_number=customer_and_number[1]
                    ) and userprofile.company.block_duplicate_schedule):
                        autorefill = AutoRefill.objects.create(
                            customer=customer_and_number[0],
                            phone_number=customer_and_number[1],
                            plan=result['plan'],
                            renewal_date=result['renewal_date'],
                            schedule=result['schedule'],
                            company=userprofile.company,
                            user=userprofile.user,
                            trigger='SC')
                        success.append([customer_and_number[1], autorefill.id])
                    else:
                        duplicate_schedule.append(customer_and_number)
                else:
                    if result['valid'] and not result['plan']:
                        plans.append('Carrier: PagePlus; %s' % result['error'])
                    wrong_numbers_page_plus.append(customer_and_number)
            except Exception, e:
                continue
        if wrong_numbers_page_plus:
            try:
                answer = dealer_red_pocket.log_in_red_pocket(carrier_admin_red_pocket)
                if not answer['valid']:
                    raise Exception(answer['error'])
            except Exception, e:
                wrong_result_red_pocket = wrong_numbers_page_plus
                wrong_numbers_page_plus = []
                failed_login.append(str(e))
            for customer_and_number in wrong_numbers_page_plus:
                try:
                    result = dealer_red_pocket.verify_carrier(
                        customer_and_number[1], answer['session'])
                    if result['valid_for_schedule']:
                        if not (AutoRefill.objects.filter(
                                customer=customer_and_number[0],
                                trigger='SC',
                                phone_number=customer_and_number[1]
                        ) and userprofile.company.block_duplicate_schedule):
                            autorefill = AutoRefill.objects.create(
                            customer=customer_and_number[0],
                            phone_number=customer_and_number[1],
                            plan=result['plan'],
                            renewal_date=result['renewal_date'],
                            schedule=result['schedule'],
                            company=userprofile.company,
                            user=userprofile.user,
                            trigger='SC')
                            success.append([customer_and_number[1], autorefill.id])
                        else:
                            duplicate_schedule.append(customer_and_number)
                    else:
                        if result['valid'] and not result['plan']:
                            plans.append('Carrier: RedPokcet; %s' % result['error'])
                        wrong_result_red_pocket.append(customer_and_number)
                except Exception, e:
                    continue
        if wrong_result_red_pocket:
            for customer_and_number in wrong_result_red_pocket:
                try:
                    result = dealer_airvoice.verify_carrier(
                        customer_and_number[1], customer_and_number[2])
                    if result['valid_for_schedule']:
                        if not (AutoRefill.objects.filter(
                                customer=customer_and_number[0],
                                trigger='SC',
                                phone_number=customer_and_number[1]
                        ) and userprofile.company.block_duplicate_schedule):
                            autorefill = AutoRefill.objects.create(
                                customer=customer_and_number[0],
                                phone_number=customer_and_number[1],
                                plan=result['plan'],
                                renewal_date=result['renewal_date'],
                                schedule=result['schedule'],
                                company=userprofile.company,
                                user=userprofile.user,
                                trigger='SC')
                            success.append(
                                [customer_and_number[1], autorefill.id])
                        else:
                            duplicate_schedule.append(customer_and_number)
                    else:
                        if result['valid'] and not result['plan']:
                            plans.append('Carrier: Airvoice;  %s' % result['error'])
                        wrong_result.append(customer_and_number)
                except Exception, e:
                    continue
        if success:
            note = '[IMPORT FROM REDFIN] (%s) Successfully numbers import  ' \
                   'from red fin and auto create schedules\n' % len(success)
            for result in success:
                note += '[phone: %s autorefill: %s]' % (result[0], result[1])
            Log.objects.create(company=userprofile.company,
                               note=note)
        if wrong_result:
            note = '[IMPORT FROM REDFIN] (%s) Wrong numbers import from redfin,' \
                   ' can not create schedule by these number\n' %\
                   len(wrong_result)
            for result in wrong_result:
                note = note + '[%s]' % result[1]
                if result[0].charge_getaway == Customer.REDFIN:
                    phone = PhoneNumber.objects.filter(customer=result[0],
                                                       number=result[1])
                    WrongResultRedFin.objects.create(user_profile=userprofile,
                                                     customer=result[0],
                                                     phone_number=phone[0],
                                                     contract_amount=result[2])
            Log.objects.create(company=userprofile.company,
                               note=note.replace('\n', ' '))
        if plans:
            note = '[IMPORT FROM REDFIN] Can not find plan for: \n'
            for plan in plans:
                if not plan in note:
                    note += '[%s]' % plan
            Log.objects.create(company=userprofile.company,
                               note=note.replace('\n', ' '))
        if failed_login:
            note = '[IMPORT FROM REDFIN] Failed login!\n'
            for carrier_message in failed_login:
                note += carrier_message
            note += '(Please check the credentials!)'
            Log.objects.create(company=userprofile.company,
                               note=note.replace('\n', ' '))
        if duplicate_schedule:
            note = '[IMPORT FROM REDFIN] (%s) Schedule refill for these ' \
                   'customer and number exists!\n' % len(duplicate_schedule)
            for number_and_schedule in duplicate_schedule:
                note += '[Customer: %s, Phone Number:%s]' %(
                    number_and_schedule[0], number_and_schedule[1])
            Log.objects.create(company=userprofile.company,
                               note=note.replace('\n', ' '))
    except Exception, e:
        logger.error("Exception: %s. "
                     "Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def restart_auto_creating_schedules_refill(userprofile):
    customer_and_numbers = []
    logger.debug('Start restart_auto_creation_schedules_refill')
    for customer_and_number in WrongResultRedFin.objects.filter(
            user_profile=userprofile):
        try:
            customer_and_numbers.append([customer_and_number.customer.id,
                                        customer_and_number.phone_number.number,
                                         customer_and_number.contract_amount])
        except Exception, e:
            continue
    WrongResultRedFin.objects.filter(user_profile=userprofile).delete()
    start = 0
    while start < len(customer_and_numbers):
        end = start + 100
        auto_creation_schedules_refill.delay(customer_and_numbers[start: end],
                                             userprofile)
        start = start + 100


@task
def send_urgent_updates(id):
    news = News.objects.get(id=id)
    news_email = NewsMessage.objects.create(title='[Urgent Update] ' + news.title + ' ' +
                                                  datetime.now(pytz.timezone('US/Eastern')).date().strftime("%m/%d/%Y"),
                                            message=news.message)
    news_email.send_mandrill_email()


@task(expires=1800)
def disabling_schedules(phone_numbers):
    if settings.TEST_MODE:
        redfin_url = 'https://staging.redfinnet.com/admin/'
    else:
        redfin_url = 'https://secure.redfinnet.com/admin/'
    n = ''
    g = ''
    sd = ''
    f = ''
    d = ''
    for company in CompanyProfile.objects.filter(use_redfin=True):
        s = log_in_redfin(company.redfin_username, company.redfin_password)
        for number in phone_numbers:
            phone_number = PhoneNumber.objects.filter(company=company, number=number).exclude(customer=None)
            if not phone_number:
                continue
            else:
                phone_number = phone_number[0]
            r, s = enter_contract_list_page(s, redfin_url, contract_id=phone_number.number)
            soup = BeautifulSoup(r.text)
            for tr in soup.findAll('tr'):
                try:
                    # taking customers by line
                    if tr.get('class') in (u'gridRow', u'gridAltRow'):
                        i = 1
                        # taking customer data
                        for td in tr.findAll('td'):
                            if 2 == i:
                                contract_url = td.find('a').get('href')
                                r = s.get('%srecurring/%s' % (redfin_url, contract_url))
                                page = r.text
                                soup = BeautifulSoup(page)
                                next_bill_date = soup.find('input', {'id': 'Next_Bill_DT'}).get('value') if 'Next_Bill_DT' in page else ''
                                if not next_bill_date:
                                    break
                                month, day, year = next_bill_date.split('/')
                                autorefills = AutoRefill.objects.filter(company=company, phone_number=phone_number.number, enabled=True)
                                if int(year) >= 2015 and int(month) >= 10:
                                    if autorefills:
                                        f = '{0}\n Refill {1} for {2} was created'.format(f, autorefills, phone_number.number)
                                    else:
                                        n = '{0}\n!!!!!!!next date {1} and number {2} hasn`t refill for customer {3}'.format(n, next_bill_date, phone_number.number, phone_number.customer)
                                else:
                                    if autorefills:
                                        for autorefill in autorefills:
                                            if Log.objects.filter(company=company, note__icontains='system created autorefill: %s' % autorefill.id):
                                                d = '{0}\n!!!!!!!Refill {1} for {2} should be deleted'.format(d, autorefill.get_full_url(), phone_number.number)
                                            else:
                                                 sd = '{0}\nRefill {1} for {2} created by user but not in redfin billable time'.format(sd, autorefill.get_full_url(), phone_number.number)
                                    else:
                                         g = '{0}\nGreat. next date {1} and number {2} hasn`t refill for customer {3}'.format(g, next_bill_date, phone_number.number, phone_number.customer)
                                break
                            i += 1
                except Exception, e:
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        logger.debug('%s\n%s\n%s\n%s\n%s' % (n, d, f, sd,g))


@task(expires=21600)
def verify_scheduled_refills(company):
    from ppars.apps.core.models import Carrier
    body_email = ''
    schedule_refills = AutoRefill.objects.filter(company=company,
                                                 trigger=AutoRefill.TRIGGER_SC,
                                                 enabled=True)
    #Page PLus
    carrier_page_plus = Carrier.objects.filter(name__icontains="PAGE PLUS CELLULAR")
    carrier_admin_page_plus = CarrierAdmin.objects.filter(company=company, carrier=carrier_page_plus[0])
    if carrier_admin_page_plus:
        auth_page_plus = dealer_page_plus.login_pageplus(carrier_admin_page_plus[0].username,
                                                         carrier_admin_page_plus[0].password)
        if auth_page_plus['valid']:
            br = auth_page_plus['browser']
            body_email += "\nCarrier Page Plus:"
            report, schedule_refills = verify_update_scheduled_refills(dealer_page_plus.verify_pageplus,
                                                                       br,
                                                                       schedule_refills,
                                                                       carrier_page_plus[0])
            body_email += report
        else:
            body_email += '\nPagePlus: %s;\n' % auth_page_plus['error']
    #Red Pocket
    carrier_red_pocket = Carrier.objects.filter(name__icontains="RED POCKET")
    carrier_admin_red_pocket = CarrierAdmin.objects.filter(company=company, carrier=carrier_red_pocket[0])
    if carrier_admin_red_pocket:
        auth_red_pocket = dealer_red_pocket.log_in_red_pocket(carrier_admin_red_pocket[0])
        if auth_red_pocket['valid']:
            body_email += "\nCarrier Red Pokcet:"
            report, schedule_refills = verify_update_scheduled_refills(dealer_red_pocket.verify_carrier,
                                                                       auth_red_pocket['session'],
                                                                       schedule_refills,
                                                                       carrier_red_pocket[0])
            body_email += report
        else:
            body_email += '\nRedPocket: %s\n' % auth_red_pocket['error']
    #H2O
    carrier_h2o = Carrier.objects.filter(name__icontains="H2O UNLIMITED")
    carrier_admin_h2o = CarrierAdmin.objects.filter(company=company, carrier=carrier_h2o[0])
    if carrier_admin_h2o:
        auth_h2o = dealer_h2o.login_h2o(carrier_admin_h2o[0])
        if auth_h2o['valid']:
            body_email += "\nCarrier H2O:"
            report, schedule_refills = verify_update_scheduled_refills(dealer_h2o.verify_carrier,
                                                                       auth_h2o['session'],
                                                                       schedule_refills,
                                                                       carrier_h2o[0])
            body_email += report
        else:
            body_email += '\nH2O: %s\n' % auth_h2o['error']
    #AirVoice
    carrier_air_voice = Carrier.objects.filter(name__icontains='AIRVOICE').get()
    body_email += "\nCarrier AirVoice:"
    report, schedule_refills = verify_update_scheduled_refills(dealer_airvoice.verify_carrier,
                                                               None,
                                                               schedule_refills,
                                                               carrier_air_voice)
    body_email += report
    #ApprovedLink
    carrier_approvedlink = Carrier.objects.filter(name__icontains='Approved Link').get()
    body_email += "\nCarrier ApprovedLink:"
    report, schedule_refills = verify_update_scheduled_refills(dealer_pvc_approvedlink.verify_carrier,
                                                               None,
                                                               schedule_refills,
                                                               carrier_approvedlink)
    body_email += report
    report = ''
    for autorefill in schedule_refills:
        report += "\nCan not find carrier for %s;" % autorefill.get_full_url()
    body_email += report
    Log.objects.create(
        company=company,
        note="Verify Scheduled Refills\n %s" % body_email
    )
    notification_about_verify_schedules(company, body_email)


def verify_update_scheduled_refills(func_verify_scheduled, auth_object, schedule_refills, carrier):
    """
    This function is using in verify_scheduled_refills for PagePlus, RedPokcet, H2O, ApprovedLink and AirVoice.
    :param func_verify_scheduled: it's function from each dealer which called verify_carrier. example dealer_page_plus.verify_carrier
    :param auth_object: it's object of session or of browser
    :param schedule_refills: it's QuerySet of AutoRefills
    :param carrier: it's object of Carrier
    :return: report and schedule_refills
    :rtype report: str
    :rtype schedule_refills: QuerySet of AutoRefills
    """
    report = ''
    autorefills = schedule_refills
    for autorefill in autorefills:
        if auth_object:
            result_verify_scheduled = func_verify_scheduled(autorefill.phone_number, auth_object)
        else:
            result_verify_scheduled = func_verify_scheduled(autorefill.phone_number)
        if result_verify_scheduled['valid_for_schedule']:
            report += '\nSchedule: %s;' \
                         'Old Carrier: %s;' \
                          'New Carrier: %s;' % (autorefill.get_full_url(),
                                                 autorefill.plan.carrier.name,
                                                 carrier.name)
            report += 'Old renewal date: %s;' % autorefill.renewal_date.strftime('%m/%d/%y')
            autorefill.renewal_date = result_verify_scheduled['renewal_date']
            report += 'New renewal date: %s;' % result_verify_scheduled['renewal_date'].strftime('%m/%d/%y')
            report += 'Old plan: %s;' % autorefill.plan.plan_name
            autorefill.plan = result_verify_scheduled['plan']
            report += 'New Plan: %s;' % result_verify_scheduled['plan'].plan_name
            autorefill.save()
            schedule_refills = schedule_refills.exclude(id=autorefill.id)
        else:
            if result_verify_scheduled['valid']:
                report += '\nSchedule: %s; ' \
                             'Carrier: %s; ' \
                             'Verify carrier error: %s;' % (autorefill.get_full_url(),
                                                           carrier.name,
                                                           result_verify_scheduled['error'].replace('\n', '; '))
                schedule_refills = schedule_refills.exclude(id=autorefill.id)
    return report, schedule_refills
