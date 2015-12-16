from django.core.management.base import BaseCommand
from ppars.apps.core.models import CompanyProfile, Transaction, TransactionStep


class Command(BaseCommand):
    '''
    report_sr_double_pin
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start report_sr_double_pin"
        for company in CompanyProfile.objects.filter(superuser_profile=False):
            print company
            for transaction in Transaction.objects.filter(company=company,
                                                          autorefill__trigger=Transaction.SCEDULED,
                                                          step__adv_status__icontains='purchased pin').distinct():
                print transaction.get_full_url()
        print "done"
