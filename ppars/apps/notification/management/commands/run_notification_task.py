from django.core.management.base import BaseCommand
from ppars.apps.notification.tasks import future_charges, unused_charges, \
    transaction_sellingprice_notification, pre_refill_sms, send_notifications, \
    insufficient_funds


class Command(BaseCommand):
    '''
    run_notification_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start task"
        #transaction_sellingprice_notification.delay()
        # unused_charges.delay()
        # future_charges.delay()
        # pre_refill_sms.delay()
        # send_notifications.delay()
        # insufficient_funds.delay()
        print "done"