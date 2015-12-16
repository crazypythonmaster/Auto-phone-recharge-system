from datetime import datetime, timedelta, time
import pytz
from django.core.management.base import BaseCommand
from ppars.apps.core.models import Transaction
from ppars.apps.core.tasks import queue_refill


class Command(BaseCommand):
    '''
    start_intermediate_refill
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        today = datetime.now(pytz.timezone('US/Eastern')).date()
        start_date = datetime.combine(today - timedelta(days=6), time.min)
        for transaction in Transaction.objects.filter(state=Transaction.INTERMEDIATE, started__gt=start_date):
            print 'run %s' % transaction
            queue_refill.delay(transaction.id)
        print "done"
