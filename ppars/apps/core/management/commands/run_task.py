from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from ppars.apps.core.models import CompanyProfile, AutoRefill, Transaction


class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        count_of_mixups = 0
        for autorefill in AutoRefill.objects.exclude(customer=None).exclude(company=None)\
                .exclude(trigger=AutoRefill.TRIGGER_MN).all():
            if autorefill.customer.company != autorefill.company:
                count_of_mixups += 1
                print autorefill.id
        print count_of_mixups
        print "done"
