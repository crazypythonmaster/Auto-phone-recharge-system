from django.core.management.base import BaseCommand
from ppars.apps.charge.tasks import precharge_job, cash_prepayment_notification


class Command(BaseCommand):
    '''
    run_charge_task
    '''

    def handle(self, *args, **options):
        print "start run_charge_task"
        precharge_job.delay()
        cash_prepayment_notification.delay()
        print "done"