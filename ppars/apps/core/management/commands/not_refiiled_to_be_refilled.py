from django.core.management.base import BaseCommand
from ppars.apps.notification.models import Notification
from ppars.apps.core.models import CompanyProfile, Transaction
from ppars.apps.core.tasks import queue_refill
import datetime


class Command(BaseCommand):
    '''
    report_sr_double_pin
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start report_sr_double_pin"

        ids = [6754102092517423, 6754102092517418, 6754102092517389,
               6754102092517377, 6754102092517373, 6754102092517371]
        for id in ids:
            transaction = Transaction.objects.get(id=id)
            if transaction.autorefill:
                autorefill = transaction.autorefill
                autorefill.renewal_date = datetime.date(2015, 11, 8)
                autorefill.save()
                autorefill.set_renewal_date_to_next(today=autorefill.renewal_date)
        print "done"
