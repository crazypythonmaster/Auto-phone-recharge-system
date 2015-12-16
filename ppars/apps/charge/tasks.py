import logging
from datetime import timedelta, datetime
from django.db.models import Q
from ppars.apps.core.customer_notifications import \
    prepayment_customer_notification
from ppars.apps.core.ext_lib import search_unused_charges
from ppars.apps.core.send_notifications import \
    successful_precharge_customer_notification, \
    failed_precharge_customer_notification, \
    failed_precharge_company_notification, check_message_customer
import pytz
from ppars.apps.tzones.functions import crontab_with_correct_tz
from celery import task
from celery.task import periodic_task
from models import Charge, ChargeError
from ppars.apps.core.models import AutoRefill, CompanyProfile, Customer, Plan
from ppars.apps.notification.models import Notification

logger = logging.getLogger(__name__)


@periodic_task(run_every=crontab_with_correct_tz(hour=10, minute=00))
def cash_prepayment_notification():
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    for day, message in [[3, 'SECOND REMINDER'], [6, '']]:
        payment_day = today + timedelta(days=day)
        for autorefill in AutoRefill.objects.filter(
                renewal_date=payment_day,
                trigger=AutoRefill.TRIGGER_SC,
                enabled=True,
                customer__charge_getaway=Customer.CASH_PREPAYMENT):
            amount, tax = autorefill.calculate_cost_and_tax()
            need_paid = search_unused_charges(autorefill, amount)
            if need_paid:
                prepayment_customer_notification(autorefill, need_paid, message)


# description: Pre CC Charge Job 9 AM Job
@periodic_task(run_every=crontab_with_correct_tz(hour=9, minute=00))
def precharge_job():
    today = datetime.now(pytz.timezone('US/Eastern')).date()
    for company in CompanyProfile.objects.filter(superuser_profile=False):
        if not company.authorize_precharge_days:
            continue
        precharge_today = []
        t = 0
        d = 1
        payment_day = today + timedelta(days=company.authorize_precharge_days)
        for autorefill in AutoRefill.objects.filter(
                company=company,
                renewal_date=payment_day,
                trigger=AutoRefill.TRIGGER_SC,
                enabled=True,
        ).exclude(
                    Q(customer__charge_getaway=Customer.CASH) |
                    Q(customer__charge_getaway=Customer.CASH_PREPAYMENT)):
            if (autorefill.customer.charge_getaway == Customer.DOLLARPHONE and
                        autorefill.plan.plan_type == Plan.DOMESTIC_TOPUP):
                continue
            if not autorefill.check_renewal_end_date(today=payment_day):
                # return self.enabled
                # if False == not enabled then skip precharge
                continue
            check_twilio_confirm_sms, confirm_log = autorefill.check_twilio_confirm_sms()
            if autorefill.pre_refill_sms and not check_twilio_confirm_sms:
                continue

            amount, tax = autorefill.calculate_cost_and_tax()
            need_paid = search_unused_charges(autorefill, amount)
            if need_paid:
                if Charge.DOLLARPHONE == autorefill.customer.charge_getaway:
                    need_paid = autorefill.plan.plan_cost
                charge = autorefill.create_charge(need_paid, tax)
                if Charge.DOLLARPHONE == charge.payment_getaway:
                    queue_precharge.apply_async(args=[charge], countdown=60*d)
                    d += 1
                elif charge.customer.id in precharge_today:
                    t += 1
                    queue_precharge.apply_async(args=[charge], countdown=200*t)
                else:
                    precharge_today.append(charge.customer.id)
                    queue_precharge.delay(charge)


@task
def queue_precharge(charge):
    try:
        charge.make_charge()
        charge.add_charge_step('precharge', Charge.SUCCESS, 'Charge ended successfully')
        if charge.customer.email_success_charge:
            successful_precharge_customer_notification(charge)
    except Exception, e:
        charge.add_charge_step('precharge', Charge.ERROR, 'Charge ended with error: "%s"' % e)
        charge_error, created = ChargeError.objects.get_or_create(charge=charge, step='charge', message='%s' % e)

        if created and check_message_customer(str(e)):
            failed_precharge_customer_notification(charge)

        if charge.company.precharge_failed_email or not check_message_customer(str(e)):
            failed_precharge_company_notification(charge)


@task
def send_prepayment_notification(customer, amount):
    body = 'Hi %s,<br/><br/> A payment of %s$ was applied to your ' \
                   'account as credit towards your future refills.<br/><br/>' \
                   'Thanks for your business.' % \
                   (customer.first_name,
                    amount)
    subject = '[%s] Successful cash prepayment' % customer.company
    notification = Notification.objects.create(
        company=customer.company,
        customer=customer,
        email=customer.primary_email,
        subject=subject,
        body=body,
        send_with=customer.send_status)
    notification.send_notification()
