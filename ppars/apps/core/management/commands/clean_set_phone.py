from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer, CompanyProfile, PhoneNumber


class Command(BaseCommand):
    '''
    clean_set_phone
    '''

    def handle(self, *args, **options):
        for customer in Customer.objects.all():
            sms_phone = customer.sms_email.strip()
            for token in sms_phone:
                if not token.isdigit():
                    sms_phone.find(token)
                    sms_phone = sms_phone[sms_phone.find(token)+1:]
                else:
                    break
            customer.sms_email = sms_phone
            if not sms_phone or sms_phone == ',':
                customer.sms_email = PhoneNumber.objects.filter(customer=customer,company=customer.company).first().number
            customer.save()