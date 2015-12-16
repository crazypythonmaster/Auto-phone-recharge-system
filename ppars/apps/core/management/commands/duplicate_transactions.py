from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Transaction, CompanyProfile, AutoRefill


class Command(BaseCommand):
    '''
    duplicate_transactions
    '''

    def handle(self, *args, **options):
        today = datetime.now(pytz.timezone('US/Eastern'))
        start = datetime.combine(today - timedelta(days=8), time.min)
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            print company
            duplicate_transactions = dict()
            for transaction in Transaction.objects.filter(company=company,
                                                          started__gt=start,
                                                          autorefill__trigger=AutoRefill.TRIGGER_SC):
                if transaction.phone_number_str in duplicate_transactions:
                    if transaction.pin == duplicate_transactions[transaction.phone_number_str].pin:
                        continue
                    print
                    print '%s' % transaction.get_full_url()
                    print '%s' % duplicate_transactions[
                        transaction.phone_number_str].get_full_url()
                else:
                    duplicate_transactions[
                        transaction.phone_number_str] = transaction
        print "done"
