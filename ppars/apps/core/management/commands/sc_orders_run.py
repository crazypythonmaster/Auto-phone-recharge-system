from django.core.management.base import BaseCommand
from ppars.apps.core.models import TransactionStep, Transaction


class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        for transaction_id in TransactionStep.objects.filter(adv_status__contains='\'Transaction\' object has no'
                                                                                  ' attribute \'custome\'')\
                .values('transaction__id').distinct():
            Transaction.objects.get(id=transaction_id['transaction__id']).send_tratsaction_to_sellercloud()
        print "done"
