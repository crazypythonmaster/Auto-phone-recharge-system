from django.core.management.base import BaseCommand
from ppars.apps.core.models import AutoRefill, Transaction
from ppars.apps.charge.models import TransactionCharge


class Command(BaseCommand):
    '''
    fix_mixup
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"

        # for refill in AutoRefill.objects.all().exclude(user=None).exclude(company=None).exclude(customer=None):
        #     if refill.user.profile and refill.user.profile.company.id != refill.company.id and\
        #                     refill.user.profile.company.id == refill.customer.company.id:
        #         refill.company = refill.user.profile.company
        #         refill.save()

        # for transaction in Transaction.objects.all().exclude(user=None).exclude(company=None).exclude(autorefill=None)\
        #         .exclude(autorefill__customer=None):
        #     if transaction.user.profile and transaction.user.profile.company.id != transaction.company.id and\
        #                     transaction.user.profile.company.id == transaction.autorefill.customer.company.id:
        #         transaction.company = transaction.user.profile.company
        #         transaction.save()

        for transaction_charge in TransactionCharge.objects.all().exclude(transaction=None).exclude(charge=None)\
                .exclude(transaction__company=None).exclude(charge__company=None).exclude(transaction__user=None)\
                .exclude(transaction__autorefill=None):
            if transaction_charge.transaction.user.profile and\
                            transaction_charge.charge.company.id != transaction_charge.transaction.company.id and\
                            transaction_charge.transaction.user.profile.company.id ==\
                            transaction_charge.transaction.autorefill.customer.company.id:
                charge = transaction_charge.charge
                charge.company = transaction_charge.transaction.company
                charge.save()

        print "done"
