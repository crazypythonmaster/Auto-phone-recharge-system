from django.core.management.base import BaseCommand
from ppars.apps.charge.models import ChargeStep
from ppars.apps.core.models import TransactionStep


class Command(BaseCommand):
    '''
    check_command
    '''

    def handle(self, *args, **options):
        print "start multiple_using_report"
        message = raw_input("Enter message: ")
        for charge_error in ChargeStep.objects.filter(adv_status__icontains=message):
                print charge_error.charge.get_full_url()
        for transaction_error in TransactionStep.objects.filter(adv_status__icontains=message):
                print transaction_error.transaction.get_full_url()
        print "done"

