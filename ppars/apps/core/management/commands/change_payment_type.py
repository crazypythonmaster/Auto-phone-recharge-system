from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer, CompanyProfile, PhoneNumber, \
    Transaction


class Command(BaseCommand):
    '''
    change_payment_type
    '''

    def handle(self, *args, **options):
        print 'start'
        company_id = raw_input("Enter the company id: ")
        for customer in Customer.objects.filter(company__id=company_id):
            transaction = Transaction.objects.filter(autorefill__customer=customer).order_by('-started').first()
            if transaction and transaction.charge_getaway_name == 'Cash':
                customer.charge_type = Customer.CASH
                customer.charge_getaway = Customer.CASH
                customer.save()
        print 'Done'