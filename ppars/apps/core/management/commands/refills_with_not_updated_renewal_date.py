from django.core.management.base import BaseCommand
from ppars.apps.core.models import AutoRefill, Transaction
from datetime import datetime, timedelta, time
from ppars.apps.core.ext_lib import get_mdn_status
from pytz import timezone
from ppars.apps.core.tasks import queue_refill


class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        to_refill = []
        not_to_refill = []
        today = datetime.now(timezone('US/Eastern')).date()
        start_date = datetime.combine(today - timedelta(days=7), time.min)
        for autorefill in AutoRefill.objects.filter(enabled=True, trigger=AutoRefill.TRIGGER_SC,
                                                    renewal_date__range=(datetime.now().date() - timedelta(days=64),
                                                                         datetime.now().date()))\
                .exclude(renewal_date=None).exclude(schedule='').exclude(schedule=None):
            if autorefill.renewal_date < datetime.now(timezone('US/Eastern')).date():
                result = get_mdn_status(autorefill.phone_number, autorefill.company)
                if not result['login_exception'] and result['status_find'] and\
                        result['renewal_date'] and result['renewal_date'] > datetime.now(timezone('US/Eastern')).date():
                    to_refill.append(autorefill.get_full_url())
                    if Transaction.objects.filter(autorefill=autorefill, started__gt=start_date):
                        transaction = Transaction.objects.filter(autorefill=autorefill, started__gt=start_date)[0]
                    else:
                        if not autorefill.check_renewal_end_date(today=today):
                            continue
                        transaction = Transaction.objects.create(user=autorefill.user,
                                                                 autorefill=autorefill,
                                                                 state="Q",
                                                                 company=autorefill.company,
                                                                 triggered_by='System')
                    if transaction.completed:
                        continue
                    if autorefill.need_buy_pins and transaction.pin:
                        transaction.state = Transaction.COMPLETED
                        transaction.save()
                        continue
                    transaction.state = Transaction.PROCESS
                    transaction.save()
                    queue_refill.delay(transaction.id)
                    autorefill.renewal_date = result['renewal_date']
                    autorefill.save()
                else:
                    not_to_refill.append(autorefill.get_full_url())
        print 'Was refiled: ', to_refill
        print 'Wasn\'t refiled: ', not_to_refill
