from django.core.management.base import BaseCommand
from ppars.apps.charge.models import ChargeStep, Charge


class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        for charge in Charge.objects.filter(used=False):
            if ChargeStep.objects.filter(adv_status__icontains='DP Charge ended with error:', charge=charge).exists():
                if ChargeStep.objects.filter(adv_status__icontains='mark charge used.', charge=charge).exists():
                    if ChargeStep.objects.filter(adv_status__icontains='mark charge used.',
                                                 charge=charge).latest('id').created > \
                            ChargeStep.objects.filter(adv_status__icontains='DP Charge ended with error:',
                                                      charge=charge).latest('id').created:
                        continue
                charge.used = True
                charge.save()
        print "done"
