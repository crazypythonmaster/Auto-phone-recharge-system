import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
import pytz
from ppars.apps.core.models import Transaction


class Command(BaseCommand):
    '''
    quryset_transactions
    '''

    def handle(self, *args, **options):
        print "start queue"
        transaction_list = []
        today = timezone.now()
        for day in range(20, today.day + 1):
            this_date = timezone.make_aware((datetime.datetime.combine(today, datetime.time.min) - datetime.timedelta(days=(today.day-day))), timezone=pytz.timezone('US/Eastern'))
            next_date = timezone.make_aware((datetime.datetime.combine(today, datetime.time.max) - datetime.timedelta(days=(today.day-day))), timezone=pytz.timezone('US/Eastern'))
            print this_date.date()
            for transaction in Transaction.objects.filter(started__range=[this_date, next_date]):
                print transaction.started, transaction.id
            print

        print "done"