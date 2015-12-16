from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer, AutoRefill


class Command(BaseCommand):
    '''
    Select customer.
    '''

    def handle(self, *args, **options):
        company_id = raw_input("Enter the id of company: ")
        customer_type = bool(raw_input("Enter the customer enabled type: "))
        schedule_type = bool(raw_input("Enter the customer enabled type: "))
        print "Customer enabled: %s\nSchedule enabled:%s" %(customer_type, schedule_type)
        customers = Customer.objects.filter(company=company_id,
                                            group_sms=True,
                                            enabled=customer_type,
                                            autorefill__enabled=schedule_type).distinct()
        for customer in customers:
            enabled = False
            if AutoRefill.objects.filter(customer=customer, enabled=schedule_type):
                enabled = True
            print "\n\nID: %s \nName: %s\nEnabled: %s\nAutorefill enabled:%s" % (customer.id,
                                                                                 customer.first_name,
                                                                                 customer.enabled,
                                                                                 enabled)