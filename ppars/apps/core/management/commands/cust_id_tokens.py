from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer


class Command(BaseCommand):
    '''
    cust_id_tokens
    '''

    def handle(self, *args, **options):
        for customer in Customer.objects.all():
            if customer.usaepay_custid:
                p = customer.usaepay_custid
                for token in [', ', '. ', ' ', ',', '.']:
                    p = p.replace(token, '|')
                p = p.replace('|', ', ').strip()
                if ',' != p[-1:]:
                    p = '%s,' % p
                print p
                customer.usaepay_custid = p
                customer.save()
        print "done"
