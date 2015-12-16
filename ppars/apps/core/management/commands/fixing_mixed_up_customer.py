from datetime import datetime
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Transaction, Customer, AutoRefill, PhoneNumber
from ppars.apps.charge.models import TransactionCharge


class Command(BaseCommand):
    '''
    pp_wrong_pins
    '''

    def handle(self, *args, **options):
        print "start"
        customer_to_delete = Customer.objects.get(id=6743501844782947)
        customer_to_fix = Customer.objects.get(id=6743501844782957)
        for phone_number in PhoneNumber.objects.filter(customer=customer_to_fix, number='3139389557'):
            phone_number.customer = None
            phone_number.save()
        for autorefill in AutoRefill.objects.filter(customer=customer_to_delete, phone_number='3139389557'):
            for transaction in Transaction.objects.filter(autorefill=autorefill, phone_number_str='3139389557'):
                for tc in TransactionCharge.objects.filter(transaction=transaction):
                    charge = tc.charge
                    charge.customer = customer_to_fix
                    charge.save()
            autorefill.customer = customer_to_fix
            autorefill.save()
        for phone_number in PhoneNumber.objects.filter(customer=customer_to_delete, number='3139389557'):
            phone_number.customer = customer_to_fix
            phone_number.save()
        customer_to_delete.delete()
        print "done"
