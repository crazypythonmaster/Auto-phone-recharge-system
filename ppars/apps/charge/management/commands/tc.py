from django.core.management.base import BaseCommand
from ppars.apps.charge.models import TransactionCharge


class Command(BaseCommand):
    '''
    tc
    '''

    def handle(self, *args, **options):
        print "start multiple_using_report"
        charge_id = raw_input("Enter the charge id: ")
        for tc in TransactionCharge.objects.filter(charge__id=charge_id):
            print tc.id
        print "done"