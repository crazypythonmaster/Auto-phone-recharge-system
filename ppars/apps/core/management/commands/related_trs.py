from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer


class Command(BaseCommand):
    '''
    related_trs
    '''

    def handle(self, *args, **options):
        print "start queue"
        company_id = raw_input("Enter the company id: ")
        for customer in Customer.objects.filter(company__id=company_id, charge_type=Customer.CASH):
            if customer.redfin_customer_key:
                if customer.redfin_cc_info_key:
                    customer.charge_type = Customer.CREDITCARD
                    customer.charge_getaway = Customer.REDFIN
                    customer.save()
                    print 'Changed to redfin %s' % customer.get_full_url()
                else:
                    print 'No payment cc profile %s' % customer.get_full_url()

        print "done"
