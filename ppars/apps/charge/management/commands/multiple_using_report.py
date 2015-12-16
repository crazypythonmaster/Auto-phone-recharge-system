from django.core.management.base import BaseCommand
from ppars.apps.charge.models import Charge, TransactionCharge
from ppars.apps.core.models import CompanyProfile


class Command(BaseCommand):
    '''
    multiple_using_report
    '''

    def handle(self, *args, **options):
        print "start multiple_using_report"

        for company in CompanyProfile.objects.filter(superuser_profile=False):
            print company
            for charge in Charge.objects.filter(company=company):
                full_amount = 0
                transactions = []
                for tc in TransactionCharge.objects.filter(charge=charge):
                    if not tc.amount or not tc.transaction:
                        continue
                    if tc.transaction in transactions:
                        continue
                    else:
                        transactions.append(tc.transaction)
                    full_amount = full_amount + tc.amount
                if len(transactions) > 1 and full_amount > charge.amount:
                    print charge.get_full_url()
        print "done"
