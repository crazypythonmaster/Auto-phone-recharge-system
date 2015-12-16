from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Transaction, CompanyProfile


class Command(BaseCommand):
    '''
    get_intermediate_transactions
    '''

    def handle(self, *args, **options):
        today = datetime.now(pytz.timezone('US/Eastern'))
        start = datetime.combine(today - timedelta(days=5), time(hour=11, minute=59))
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            print company
            for transaction in Transaction.objects.filter(company=company,
                                                          state=Transaction.INTERMEDIATE,
                                                          started__lt=start):
                print '%s pin %s' % (transaction.get_full_url(), transaction.pin)
        print "done"