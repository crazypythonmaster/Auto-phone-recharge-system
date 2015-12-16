import calendar
import logging
import traceback
from celery.schedules import crontab
from celery.task import periodic_task, task
from datetime import timedelta, datetime, time, date
import decimal
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils import timezone
import pytz
from ppars.apps.core import verify_carrier
from ppars.apps.core.ext_lib import search_unused_charges, number_of_transaction_from_month_by_now_of_company
from ppars.apps.tzones.functions import crontab_with_correct_tz
from ppars.apps.charge.models import Charge
from ppars.apps.core.models import CompanyProfile, AutoRefill, Customer, \
    Transaction, News, PhoneNumber, PhoneNumberSettings
from models import Notification, SpamMessage, NewsMessage, WelcomeEmail, BulkPromotion
from twilio.rest import TwilioRestClient


logger = logging.getLogger('ppars')


@periodic_task(run_every=crontab_with_correct_tz(hour=00, minute=00))
def notify_devs_in_case_of_not_changed_renewal_date():
    report = ''
    for autorefill in AutoRefill.objects.filter(enabled=True, trigger=AutoRefill.TRIGGER_SC,
                                                renewal_date__range=(datetime.now(pytz.timezone('US/Eastern')).date() -
                                                                         timedelta(days=64),
                                                                     datetime.now(pytz.timezone('US/Eastern')).date() -
                                                                         timedelta(days=1)))\
            .exclude(renewal_date=None).exclude(schedule='').exclude(schedule=None):
        if autorefill.renewal_date < datetime.now(pytz.timezone('US/Eastern')).date():
            report += '%s/autorefill/%s/' % (settings.SITE_DOMAIN, autorefill.id) + '\n'
    if report:
        Notification.objects.create(company=CompanyProfile.objects.get(superuser_profile=True),
                                    email='vlasgambitlive@gmail.com',
                                    subject='[PPARS] Not changed renewal date',
                                    body=report,
                                    send_with=Notification.MAIL)


# description: 1 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=01, minute=00))
def one_hour_job():
    unused_charges.delay()
    pre_refill_sms.delay()
    transaction_sellingprice_notification.delay()
    unpaid_transaction_notification.delay()


# description: 8 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=8, minute=00))
def eight_hour_job():
    future_charges.delay()
    insufficient_funds.delay()
    send_notifications.delay()
    news_message_job.delay()
    notification_about_card_expiration.delay()


@task
def notification_about_card_expiration():
    i = 1
    for company in CompanyProfile.objects.filter(superuser_profile=False, card_expiration_date_info=True):
        for customer in Customer.objects.filter(company=company):
            if customer.has_local_cards and datetime.strptime('%s/%s' % (customer.get_local_card().expiration_month, customer.get_local_card().expiration_year),
                                                              '%m/%Y') + timedelta(days=30)\
                    >= datetime.now(pytz.timezone('US/Eastern')):
                email_body = 'Card of <a href="%s">%s</a> are expiring soon. Be aware.' % (customer.get_full_url(),
                                                                                           customer.full_name)
                notification = Notification.objects.create(
                    company=CompanyProfile.objects.get(superuser_profile=True),
                    email=company.email_id,
                    subject='Customer\'s card are expiring soon',
                    body=email_body,
                    send_with=Notification.MAIL
                )
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()


@task
def send_welcome_email(customer):
    phone_number = ''
    email_template = None
    if customer.charge_type == 'CA' and not AutoRefill.objects.filter(customer=customer).exists():
        if WelcomeEmail.objects.filter(enabled=True, category=WelcomeEmail.CASH_WITHOUT_SCHEDULED_REFILL).exists():
            email_template = WelcomeEmail.objects.get(enabled=True, category=WelcomeEmail.CASH_WITHOUT_SCHEDULED_REFILL)
            phone_number = PhoneNumber.objects.filter(customer=customer)[0].number
    elif customer.charge_type == 'CC' and AutoRefill.objects.filter(customer=customer).exists():
        if WelcomeEmail.objects.filter(enabled=True, category=WelcomeEmail.CREDIT_CARD_WITH_SCHEDULED_REFILL).exists():
            email_template = WelcomeEmail.objects.get(enabled=True,
                                                      category=WelcomeEmail.CREDIT_CARD_WITH_SCHEDULED_REFILL)
            phone_number = AutoRefill.objects.filter(customer=customer)[0].phone_number
    elif customer.charge_type == 'CC' and not AutoRefill.objects.filter(customer=customer).exists():
        if WelcomeEmail.objects.filter(enabled=True,
                                       category=WelcomeEmail.CREDIT_CARD_WITHOUT_SCHEDULED_REFILL).exists():
            email_template = WelcomeEmail.objects.get(enabled=True,
                                                      category=WelcomeEmail.CREDIT_CARD_WITHOUT_SCHEDULED_REFILL)
            phone_number = PhoneNumber.objects.filter(customer=customer)[0].number
    elif customer.charge_getaway == 'CP' and AutoRefill.objects.filter(customer=customer).exists():
        if WelcomeEmail.objects.filter(enabled=True,
                                       category=WelcomeEmail.CASH_PREPAYMENT_WITH_SCHEDULED_REFILL).exists():
            email_template = WelcomeEmail.objects.get(enabled=True,
                                                      category=WelcomeEmail.CASH_PREPAYMENT_WITH_SCHEDULED_REFILL)
            phone_number = AutoRefill.objects.filter(customer=customer)[0].phone_number
    if phone_number and email_template:
        welcome = Notification.objects.create(company=customer.company,
                                              customer=customer,
                                              email=customer.primary_email,
                                              phone_number=phone_number,
                                              subject='Welcome',
                                              body=email_template.body,
                                              send_with=customer.send_status)
        welcome.send_notification()


@task
def news_message_job():
    # Send PPARS News
    if News.objects.filter(created__gt=datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=23, minutes=59)).exclude(category='EZ').exclude(category='UU'):
        news_email = NewsMessage.objects.create(
            title='Updates for ' + datetime.now(pytz.timezone('US/Eastern')).date().strftime("%m/%d/%Y"),
            message='')
        for news in News.objects.filter(created__gt=datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=23,
                                                                                                          minutes=59)).exclude(category='EZ').exclude(category='UU'):
            news_email.message += '<a href=\'' + settings.SITE_DOMAIN + '%s' % (reverse('news_detail',
                                                                                        args=[news.id])) + '\'>' + \
                                  news.get_category_display() + ' ' + news.title + '</a><br><p>' + news.message + '</p><br>'
        news_email.save()
        news_email.send_mandrill_email()
    # Send EZ Cloud News
    if News.objects.filter(created__gt=datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=23, minutes=59),
                           category='EZ'):
        news_email = NewsMessage.objects.create(
            title='EZ Cloud news for ' + datetime.now(pytz.timezone('US/Eastern')).date().strftime("%m/%d/%Y"),
            message='')
        for news in News.objects.filter(created__gt=datetime.now(pytz.timezone('US/Eastern')) - timedelta(hours=23,
                                                                                                          minutes=59),
                                        category='EZ'):
            news_email.message += '<a href=\'http://ezcloudllc.com/news\'>' + \
                                  news.get_category_display() + ' ' + news.title + '</a><br><p>' + news.message + '</p><br>'
        news_email.save()
        news_email.send_ez_cloud_news_mandrill_email()


@task
def send_notifications():
    start_date = datetime.combine(datetime.today(), time.min)
    end_date = datetime.combine(datetime.today(), time.max)
    i = 1
    for notification in Notification.objects.filter(created__range=(start_date, end_date), status=None):
        logger.debug('Notification %s [%s]' % (notification.subject, notification.id))
        try:
            if notification.send_with == notification.GV_SMS:
                notification.send_notification(i=i)
                i += 1
            else:
                notification.send_notification()
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def send_gvoice_sms(gvoice_email, gvoice_pass, phone_number, text):
    from googlevoice import Voice
    voice = Voice()
    voice.login(email=gvoice_email, passwd=gvoice_pass)
    voice.send_sms(phoneNumber=phone_number,
                   text=text)


@task
def unused_charges():
    now = timezone.now()
    today = now.date()
    i = 1
    for company in CompanyProfile.objects.filter(
            superuser_profile=False,
            unused_charge_notification=True):
        if company.authorize_precharge_days:
            precharge_days = company.authorize_precharge_days
        else:
            precharge_days = 0
        subject = "[%s] Unused Credit Card Charges" % company.company_name
        charge_list = []
        for cc in Charge.objects.filter(
                status=Charge.SUCCESS,
                company=company,
                summ=decimal.Decimal(0.00),
                used=False,
                company_informed=False,
                created__lt=(today - timedelta(days=precharge_days + 1))).exclude(
                    payment_getaway=Charge.CASH_PREPAYMENT):
            charge_list.append('<a href="%s%s">%s</a>' %
                               (settings.SITE_DOMAIN,
                                reverse('charge_detail', args=[cc.id]), cc))
            cc.company_informed = True
            cc.save()
        if charge_list:
            # 'Refund started automatically. ' \
            body = 'Hi %s,\n\nThis charges didn`t used more than %s days. ' \
                   'Please, check it.\n\n%s' \
                   '\n\nRegards, EZ-Cloud Autorefill System' % \
                   (company.company_name,
                    company.authorize_precharge_days,
                    '\n'.join(charge_list)
                    )
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=company.email_id,
                subject=subject,
                body=body,
                send_with=Notification.MAIL)
            try:
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def future_charges():
    now = timezone.now()
    today = now.date()
    i = 1
    for company in CompanyProfile.objects.filter(superuser_profile=False):
        if company.authorize_precharge_days:
            payment_day = today + timedelta(days=3 + company.authorize_precharge_days)
            subject = "[%s] Credit Card Charge" % company.company_name
            for autorefill in AutoRefill.objects.filter(
                    trigger=AutoRefill.TRIGGER_SC,
                    enabled=True,
                    company=company,
                    renewal_date=payment_day,
                    customer__charge_type=Customer.CREDITCARD,
                    customer__precharge_sms=True
            ).exclude(customer__send_status=Customer.DONT_SEND):
                if not autorefill.check_renewal_end_date(today=payment_day):
                    # return self.enabled
                    # if False == not enabled then skip autorefill
                    continue
                cost, tax = autorefill.calculate_cost_and_tax()
                charge_date, refill_date = autorefill.get_formated_charge_refill_date()
                body = 'Hi %s,<br/><br/>' \
                       'We are going to charge your card on %s for $%s to ' \
                       'refill your mobile phone number %s%s on %s.<br/>Please make ' \
                       'sure you have enough funds in your card.' \
                       '<br/><br/>Regards, %s' % \
                       (autorefill.customer,
                        charge_date,
                        cost,
                        PhoneNumber.objects.filter(company=autorefill.company,
                                                   customer=autorefill.customer,
                                                   number=autorefill.phone_number)[0].title,
                        ' (' + autorefill.phone_number + ')',
                        refill_date,
                        autorefill.company.company_name,
                        )
                notification = Notification.objects.create(
                    company=company,
                    customer=autorefill.customer,
                    email=autorefill.customer.primary_email,
                    phone_number=autorefill.phone_number,
                    subject=subject,
                    body=body,
                    send_with=autorefill.customer.send_status)
                try:
                    if notification.send_with == notification.GV_SMS:
                        notification.send_notification(i=i)
                        i += 1
                    else:
                        notification.send_notification()
                except Exception, e:
                    logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def insufficient_funds():
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    payment_day = today + timedelta(days=1)
    i = 1
    for company in CompanyProfile.objects.filter(superuser_profile=False, insufficient_funds_notification=True):
        unpaid_autorefills = []
        for autorefill in AutoRefill.objects.filter(
                trigger=AutoRefill.TRIGGER_SC,
                enabled=True,
                company=company,
                renewal_date=payment_day,
                customer__charge_getaway=Customer.CASH_PREPAYMENT,
        ):
            amount, tax = autorefill.calculate_cost_and_tax()
            need_paid = search_unused_charges(autorefill, amount)
            if need_paid:
                unpaid_autorefills.append('<br/>%s needs $%s for <a href="%s">%s</a>' %
                                          (autorefill.customer,
                                           need_paid,
                                           reverse('autorefill_update', args=[autorefill.id]),
                                           autorefill.phone_number))
        if unpaid_autorefills:
            subject = "[%s] Unpaid scheduled refills at %s " % (company.company_name, payment_day)
            body = 'Unpaid scheduled refills:%s<br/><br/>Regards, %s' % (
                ','.join(unpaid_autorefills), company.company_name)
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=company.email_id,
                subject=subject,
                body=body,
                send_with=Notification.MAIL)
            try:
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month / 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


@task
def send_notification_license_expiries():
    date_expiries = add_months(datetime.now(pytz.timezone('US/Eastern')).date(), 1)
    subject_company = "The license expires in a month!"
    body_company = "The license expires in a month for company %s, date of license expiry is %s."
    subject = "The license expires in a month for companies!"
    body = "The license expires in a month for companies %s, date of license expiry is %s."
    companies = ''
    i = 1
    for company in CompanyProfile.objects.filter(license_expiries=True, date_limit_license_expiries=date_expiries):
        companies = "%s %s," % (companies, company.company_name)
        if company.email_id:
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=company.email_id,
                subject=subject_company,
                body=body_company % (company.company_name, company.date_limit_license_expiries),
                send_with=Notification.MAIL
            )
            try:
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
    if companies:
        super_company = CompanyProfile.objects.filter(superuser_profile=True)[0]
        if super_company.admin_email:
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=super_company.admin_email,
                subject=subject,
                body=body % (companies, date_expiries),
                send_with=Notification.MAIL
            )
            try:
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        if super_company.sales_agent_email:
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=super_company.sales_agent_email,
                subject=subject,
                body=body % (companies, date_expiries),
                send_with=Notification.MAIL
            )
            try:
                if notification.send_with == notification.GV_SMS:
                    notification.send_notification(i=i)
                    i += 1
                else:
                    notification.send_notification()
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def queue_send_bulk_promotion(pk):
    try:
        admin_company_settings = CompanyProfile.objects.get(superuser_profile=True).admin_company_settings
        if admin_company_settings.has_twilio_bulk_promotion_settings:
            distinct_numbers = tuple(distinct_number['phone_number__number'] for distinct_number in
                                     PhoneNumberSettings.objects.filter(bulk_promotion_subscription=True)
                                     .values('phone_number__number').distinct())
            distinct_numbers_to_send_to = []

            # Check latest unsubscribed numbers before sending messages
            client = TwilioRestClient(admin_company_settings.bulk_promotion_twilio_sid,
                                      admin_company_settings.bulk_promotion_twilio_auth_token)
            for number in distinct_numbers:
                list_of_messages = client.messages.list(to="+1%s" % admin_company_settings.bulk_promotion_twilio_number,
                                                        from_=number)
                send_to = True
                for sms in list_of_messages:
                    if sms.body.upper() == 'unsubscribe'.upper():
                        for number_to_unsubscribe in PhoneNumber.objects.filter(number=number):
                            number_to_unsubscribe_settings = number_to_unsubscribe.phone_number_settings
                            number_to_unsubscribe_settings.bulk_promotion_subscription = False
                            number_to_unsubscribe_settings.save()
                            send_to = False
                    if not send_to:
                        break
                if send_to:
                    distinct_numbers_to_send_to.append(number)

            # Sending bulk promotion messages
            for number in distinct_numbers_to_send_to:
                client = TwilioRestClient(admin_company_settings.bulk_promotion_twilio_sid,
                                          admin_company_settings.bulk_promotion_twilio_auth_token)
                client.messages.create(from_="+1%s" % admin_company_settings.bulk_promotion_twilio_number,
                                       to="+1%s" % number,
                                       body=BulkPromotion.objects.get(id=pk).body)
    except CompanyProfile.NotAdminProfile, msg:
        logger.debug(str(msg))
    except CompanyProfile.NoAdminCompanyProfileSettings, msg:
        logger.debug(str(msg))
    except PhoneNumber.NoPhoneNumberSettings, msg:
        logger.debug(str(msg))
    except Exception, msg:
        logger.debug(str(msg))


@task
def queue_send_sms(pk):
    spam_message = SpamMessage.objects.get(id=pk)
    customers = Customer.objects.filter(company=spam_message.company,
                                        group_sms=True)
    if spam_message.customer_type == 'E':
        customers = customers.filter(enabled=True)
    elif spam_message.customer_type == 'D':
        customers = customers.filter(enabled=False)
    if spam_message.schedule_type == 'E':
        customers = customers.filter(autorefill__enabled=True).distinct()
    elif spam_message.schedule_type == 'D':
        customers = customers.filter(autorefill__enabled=False,
                                     autorefill__trigger='SC').distinct()
    elif spam_message.schedule_type == 'N':
        customers = customers.filter(Q(autorefill__isnull=True) |
                                     Q(autorefill__enabled=False,
                                       autorefill__trigger='SC')).distinct()
    if spam_message.charge_type != 'A':
        customers = \
            customers.filter(charge_type__icontains=spam_message.charge_type)
    if spam_message.carrier:
        customers = \
            customers.filter(autorefill__plan__carrier=spam_message.carrier
                             ).distinct()
    if not spam_message.send_with == SpamMessage.MAIL:
        body = ''
        if len(spam_message.message) <= 140:
            body = spam_message.message
        else:
            separator = 137
            parts = int(round((len(spam_message.message) / separator)
                              + 1/separator)) + 1
            index = 0
            for part in [spam_message.message[i:i + separator] for i
                         in range(0, len(spam_message.message), separator)]:
                index += 1
                part = "%s/%s" % (index, parts) + part
                body += part
    else:
        body = spam_message.message
    i = 1
    for customer in customers:
        notification = Notification.objects.create(
            company=spam_message.company,
            customer=customer,
            phone_number=PhoneNumber.objects.filter(customer=customer).first().number,
            subject='Global Notification',
            body=body,
            send_with=spam_message.send_with)
        if notification.send_with == notification.GV_SMS:
            notification.send_notification(i=i)
            i += 1
        else:
            notification.send_notification()


@task
def unpaid_transaction_notification():
    today = datetime.now(pytz.timezone('US/Eastern'))
    for transaction in Transaction.objects.exclude(autorefill=None)\
            .filter(paid=False,
                    status='S',
                    state='C',
                    autorefill__customer__charge_getaway='CP',
                    autorefill__refill_type='MN',
                    started__range=(today - timedelta(days=1),
                                    today - timedelta(hours=2))):
        try:
            message = "HI %s, the plan for %s%s expires on %s," \
                      "to avoid interruption of your cellphone service" \
                      " Please make a  payment of %s  before expire date," \
                      " Regards, %s" % \
                      (
                          transaction.customer.first_name,
                          PhoneNumber.objects.filter(company=transaction.company,
                                                     customer=transaction.autorefill.customer,
                                                     number=transaction.phone_number_str)[0].title,
                          ' (' + transaction.phone_number_str + ')',
                          transaction.autorefill.renewal_date.strftime("%m/%d/%y"),
                          search_unused_charges(transaction.autorefill, transaction.cost),
                          transaction.company.company_name
                      )
            Notification.objects.create(
                company=transaction.company,
                customer=transaction.customer,
                email=transaction.customer.primary_email,
                phone_number=transaction.autorefill.phone_number,
                subject='Unpaid refill notification',
                body=message,
                send_with=transaction.customer.send_status)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


@task
def pre_refill_sms():
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    for autorefill in AutoRefill.objects.filter(renewal_date=today + timedelta(days=5),
                                                enabled=True,
                                                pre_refill_sms=True, trigger=AutoRefill.TRIGGER_SC):
        logger.debug('pre_refill_sms %s for autorefill %s' % (today + timedelta(days=5), autorefill))
        message = 'Hello %s, your number %s is scheduled to be refilled, ' \
                  'please, reply \"yes\" if you need a refill for %s' \
                  '\n\nRegards, %s' % \
                  (autorefill.customer.first_name,
                   autorefill.phone_number,
                   autorefill.plan.get_plansellingprice(autorefill.company,
                                                        autorefill.customer.selling_price_level),
                   autorefill.company.company_name)
        Notification.objects.create(
            company=autorefill.company,
            customer=autorefill.customer,
            email=autorefill.customer.primary_email,
            phone_number=autorefill.pre_refill_sms_number,
            subject='Refill confirmation',
            body=message,
            send_with=Notification.SMS)


@task
def transaction_sellingprice_notification():
    '''
    :param schedule:
    :return: notify on email with amount of money required for scheduled transaction in three days
    '''
    i = 1
    for company in CompanyProfile.objects.filter(superuser_profile=False, deposit_amount_notification=True):
        week = company.sellingprices_amount_for_week()
        if week[0] + week[1] + week[2] + week[3] + week[4] + week[5] + week[6] > 0:
            email_subject = "Transaction price notification"
            email_body = "Scheduled transactions selling prices amount " \
                         "- for today: %s, for tomorrow: %s, for three days: %s, " \
                         "for four days: %s, for five days: %s, for six days: %s, " \
                         "for week: %s. Please, top up your bank account if you" \
                         " don`t have enough." % \
                         (week[0], week[1], week[2], week[3], week[4], week[5], week[6])
            notification = Notification.objects.create(
                company=CompanyProfile.objects.get(superuser_profile=True),
                email=company.email_id,
                subject=email_subject,
                body=email_body,
                send_with=Notification.MAIL
            )
            if notification.send_with == notification.GV_SMS:
                notification.send_notification(i=i)
                i += 1
            else:
                notification.send_notification()


@task
def notification_about_status_of_pin(pins, user_profile):
    result = verify_carrier.get_status_of_pins(user_profile.company, pins)
    if result['failed_login']:
        body = 'Failed Login to RedPocket. ' \
               'Please check your password and login.'
    else:
        body = 'Result of checking pins on RedPocket!<br/>' \
               '<table>' \
               '<thead>' \
               '<tr>' \
               '<td><b>Pin</b></td>' \
               '<td><b>Status</b></td>' \
               '<td><b>Used By</b></td>' \
               '<td><b>Link</b></td>' \
               '</tr>' \
               '</thead>' \
               '<tbody>'
        for pin_result in result['result']:
            if pin_result['status']:
                body += '<tr>' \
                        '<td>%s</td>' \
                        '<td>%s</td>' \
                        '<td>%s</td>' \
                        '<td><a href="%s" target="_blank">%s</a></td>' \
                        '</tr>' % (pin_result['pin'],
                                   pin_result['status_pin'],
                                   pin_result['details'],
                                   pin_result['url'],
                                   pin_result['url'])
            else:
                body += '<tr>' \
                        '<td>%s</td>' \
                        '<td>%s</td>' \
                        '<td>%s</td>' \
                        '<td>%s</td>' \
                        '</tr>' % (pin_result['pin'],
                                   pin_result['status_pin'],
                                   'Error can not get information!',
                                   '')
        body += '</tbody></table>'
    subject = 'Report about unused pins of RedPocket.'
    company_admin = CompanyProfile.objects.get(superuser_profile=True)
    if user_profile.updates_email:
        email = user_profile.updates_email
    else:
        email = user_profile.company.email_id
    notification = Notification.objects.create(
        company=company_admin,
        email=email,
        subject=subject,
        body=body,
        send_with=Notification.MAIL
    )
    try:
        notification.send_notification()
    except Exception, e:
        logger.error(
            "Exception: %s. Trace: %s." % (
                e, traceback.format_exc(limit=10)))


@periodic_task(run_every=crontab(hour=04, minute=00, day_of_month=1))
def notification_about_manual_and_schedule_transaction():
    result = ''
    for company in CompanyProfile.objects.all():
        manual_transaction, schedule_transaction = number_of_transaction_from_month_by_now_of_company(company, 1)
        result += "\n%s\tManual Transaction: %s\tSchedule Transaction: %s" % \
                  (company.company_name, manual_transaction, schedule_transaction)
    if result:
        company_admin = CompanyProfile.objects.get(superuser_profile=True)
        notification = Notification.objects.create(
            company=company_admin,
            email=company_admin.admin_email,
            subject='The number of transactions per month.',
            body=result,
            send_with=Notification.MAIL
        )
        try:
            notification.send_notification()
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
