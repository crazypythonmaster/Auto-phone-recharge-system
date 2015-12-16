from django.core.management.base import BaseCommand
from ppars.apps.notification.models import Notification
from ppars.apps.core.models import Transaction, CompanyProfile, Plan, UnusedPin
import datetime
from ppars.apps.core.ext_lib import get_mdn_status
from ppars.apps.core.tasks import queue_refill
from ppars.apps.charge.models import TransactionCharge

class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        not_refilled = []
        refilled = []
        notified = []
        for transaction in Transaction.objects.filter(started__range=(datetime.datetime.combine(datetime.date(2015, 11,
                                                                                                              07),
                                                                                                datetime.time.min),
                                                                      datetime.datetime.combine(datetime.date(2015, 11,
                                                                                                              07),
                                                                                                datetime.time.max)),
                                                      state=Transaction.INTERMEDIATE):
            if transaction.autorefill:
                try:
                    result = get_mdn_status(transaction.autorefill.phone_number, transaction.autorefill.company)
                except Exception as e:
                    not_refilled.append('Not refilled: ' + transaction.get_full_url())
                    continue
                if not result['login_exception']:
                    if 'renewal_date' in result and (not result['renewal_date'] or
                                                        result['renewal_date'] == datetime.date(2015, 11, 8)):
                        refilled.append('Refilled: ' + transaction.get_full_url())
                        autorefill = transaction.autorefill
                        autorefill.renewal_date = datetime.date(2015, 11, 8)
                        autorefill.save()
                        autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)
                        queue_refill.delay(transaction.id)
                        send_with = transaction.autorefill.customer.send_status
                        if send_with == 'NO':
                            send_with = 'EM'
                        notification = Notification.objects.create(
                            company=CompanyProfile.objects.get(superuser_profile=True),
                            customer=transaction.autorefill.customer,
                            email='info@e-zoffer.com',
                            phone_number='',
                            subject='Apology for delay in the service',
                            body='Hi, %s. Our system had a server issues and your reifll didn\'t run on time. It\'s'
                                 ' fixed and it should not repeat, we apologize for any inconvenience'
                                 ' this has caused you.' % transaction.autorefill.customer.first_name,
                            send_with=send_with)
                        notification.send_notification()
                    elif 'renewal_date' in result and result['renewal_date'] > datetime.date(2015, 11, 8):
                        notified.append('Only notified: ' + transaction.get_full_url())
                        autorefill = transaction.autorefill
                        autorefill.renewal_date = datetime.date(2015, 11, 8)
                        autorefill.save()
                        autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)
                        send_with = transaction.autorefill.customer.send_status
                        if send_with == 'NO':
                            send_with = 'EM'
                        autorefill = transaction.autorefill
                        autorefill.renewal_date = result['renewal_date']
                        autorefill.save()
                        if TransactionCharge.objects.filter(transaction=transaction).exists():
                            for tc in TransactionCharge.objects.filter(transaction=transaction):
                                try:
                                    tc.charge.make_refund(transaction.user)
                                except Exception as e:
                                    pass
                        for pin in transaction.pin.replace(' ', '').split(','):
                            if transaction.autorefill:
                                plan = transaction.autorefill.plan
                            else:
                                plan = Plan.objects.filter(plan_id__icontains=transaction.plan_str).first()
                            if not plan.available and plan.universal_plan:
                                    plan = plan.universal_plan
                            UnusedPin.objects.get_or_create(
                                company=transaction.company,
                                plan=plan,
                                pin=pin,
                                defaults={'user': transaction.user,
                                          'used': False,
                                          'notes': 'Pin bought from transaction %s' % transaction.get_full_url()})
                        notification = Notification.objects.create(
                            company=CompanyProfile.objects.get(superuser_profile=True),
                            customer=transaction.autorefill.customer,
                            email='info@e-zoffer.com',
                            phone_number='',
                            subject='Apology for delay in the service',
                            body='Hi, %s. Our system had a server issues and your reifll didn\'t run on time. It\'s'
                                 ' fixed and it should not repeat, we apologize for any inconvenience'
                                 ' this has caused you.',
                            send_with=send_with)
                        notification.send_notification()
                    else:
                        not_refilled.append('Not refilled: ' + transaction.get_full_url())
                else:
                    not_refilled.append('Not refilled: ' + transaction.get_full_url())
            else:
                not_refilled.append('Not refilled: ' + transaction.get_full_url())
        print not_refilled
        print notified
        print refilled
        print "done"
