from datetime import timedelta, datetime, time
from django.core.management.base import BaseCommand
from ppars.apps.core.models import AutoRefill, Transaction



class Command(BaseCommand):
    '''
    set_one_day_back
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        start = datetime.combine(datetime(2015, 06, 24), time.min)
        end = datetime.combine(datetime(2015, 07, 28), time.min)
        for transaction in Transaction.objects.filter(started__range=(start, end), autorefill__trigger=AutoRefill.TRIGGER_SC,  autorefill__enabled=True):
            if int(transaction.ended.strftime('%d')) - int(transaction.started.strftime('%d')) > 1:
                transaction.autorefill.renewal_date = transaction.autorefill.renewal_date + timedelta(days=1)
                transaction.autorefill.save()
        for transaction in Transaction.objects.filter(started__range=(start, end), autorefill__trigger=AutoRefill.TRIGGER_SC,  autorefill__enabled=True):
            if int(transaction.ended.strftime('%j')) - int(transaction.started.strftime('%j')) > 1:
                transaction.autorefill.renewal_date = transaction.autorefill.renewal_date - timedelta(days=1)
                transaction.autorefill.save()
        print "done"