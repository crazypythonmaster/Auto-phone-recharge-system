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
        ids = [6754102092517410, 6754102092517388, 6754102092517386, 6754102092517350, 6754102092517349,
               6754102092517429, 6754102092517427, 6754102092517426, 6754102092517416, 6754102092517414,
               6754102092517411, 6754102092517408, 6754102092517401, 6754102092517398, 6754102092517397,
               6754102092517395, 6754102092517393, 6754102092517392, 6754102092517381, 6754102092517380,
               6754102092517379, 6754102092517378, 6754102092517364, 6754102092517361, 6754102092517360,
               6754102092517359, 6754102092517359, 6754102092517356, 6754102092517356, 6754102092517354,
               6754102092517354, 6754102092517354]
        for id in ids:
            transaction = Transaction.objects.get(id=id)
            send_with = transaction.autorefill.customer.send_status
            if send_with == 'NO':
                send_with = 'EM'
            notification = Notification.objects.create(
                            company=CompanyProfile.objects.get(superuser_profile=True),
                            customer=transaction.autorefill.customer,
                            email=transaction.autorefill.customer.primary_email,
                            phone_number=transaction.phone_number_str,
                            subject='Apology for delay in the service',
                            body='Hi, %s. Our system had a server issues and your reifll didn\'t run on time. It\'s'
                                 ' fixed and it should not repeat, we apologize for any inconvenience'
                                 ' this has caused you.',
                            send_with=send_with)
            notification.send_notification()
        print "done"
