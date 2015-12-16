from datetime import datetime, timedelta, time
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Customer, PhoneNumber, \
    AutoRefill, Transaction, Plan


class Command(BaseCommand):
    '''
    cust_en
    '''

    def handle(self, *args, **options):
        company_id = raw_input("Enter the company id: ")
        today = datetime.now(pytz.timezone('US/Eastern')).date()
        for customer in Customer.objects.filter(company_id=company_id, charge_getaway=Customer.REDFIN):
            for pn in PhoneNumber.objects.filter(customer=customer):
                for autorefill in AutoRefill.objects.filter(phone_number=pn.number, company_id=company_id,  enabled=True, renewal_date__lt=today):
                    if not Transaction.objects.filter(autorefill=autorefill).exists():
                        print autorefill.get_full_url()
        print "done"
