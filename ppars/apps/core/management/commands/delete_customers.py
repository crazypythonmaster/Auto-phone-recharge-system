from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer, CompanyProfile


class Command(BaseCommand):
    '''
    delete_customers
    '''

    def handle(self, *args, **options):
        company_id = raw_input("Enter the company id: ")
        for customer in Customer.objects.filter(company__id=company_id):
            customer.delete()
        print "done"