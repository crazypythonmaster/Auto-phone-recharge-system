from django.core.management.base import BaseCommand
from ppars.apps.notification.models import Notification
from ppars.apps.core.models import CompanyProfile, Transaction, AutoRefill
from ppars.apps.core.tasks import queue_refill
from datetime import datetime, timedelta
import pytz


class Command(BaseCommand):
    '''
    report_sr_double_pin
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'


    def handle(self, *args, **options):
        print "start"
        today = datetime.now(pytz.timezone('US/Eastern')).date()
        # late for today
        print 'LATE TODAY:'
        for transaction in Transaction.objects.filter(state=Transaction.INTERMEDIATE, started__range=(
                                                                    # The start_date with the minimum possible time
                                                                    datetime.combine(today - timedelta(days=1),
                                                                                     datetime.min.time()),
                                                                    # The start_date with the maximum possible time
                                                                    datetime.combine(today - timedelta(days=1),
                                                                                     datetime.max.time())
                                                                    ),
                                                      ended__range=(
                                                                    # The start_date with the minimum possible time
                                                                    datetime.combine(today - timedelta(days=1),
                                                                                     datetime.min.time()),
                                                                    # The start_date with the maximum possible time
                                                                    datetime.combine(today - timedelta(days=1),
                                                                                     datetime.max.time())
                                                                    )).exclude(autorefill__schedule=AutoRefill.MD).\
                exclude(autorefill__schedule=AutoRefill.MN).\
                exclude(autorefill__schedule=AutoRefill.AM_AND_ONE_MINUET_PM):
            print transaction.id
        # late for yesterday
        print 'LATE YESTERDAY: '
        for transaction in Transaction.objects.filter(state=Transaction.INTERMEDIATE, started__range=(
                                                                    # The start_date with the minimum possible time
                                                                    datetime.combine(today - timedelta(days=2),
                                                                                     datetime.min.time()),
                                                                    # The start_date with the maximum possible time
                                                                    datetime.combine(today - timedelta(days=2),
                                                                                     datetime.max.time())
                                                                    ),
                                                      ended__range=(
                                                                    # The start_date with the minimum possible time
                                                                    datetime.combine(today - timedelta(days=2),
                                                                                     datetime.min.time()),
                                                                    # The start_date with the maximum possible time
                                                                    datetime.combine(today - timedelta(days=2),
                                                                                     datetime.max.time())
                                                                    )):
            print transaction.id
        print "done"
