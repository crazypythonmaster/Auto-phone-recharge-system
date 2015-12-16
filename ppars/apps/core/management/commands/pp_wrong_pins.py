from datetime import datetime
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Transaction, UnusedPin, Plan, TransactionStep


class Command(BaseCommand):
    '''
    pp_wrong_pins
    '''

    def handle(self, *args, **options):
        date = int(raw_input("Enter the date from: "))
        today = datetime.now(pytz.timezone('US/Eastern'))
        that_date = today.replace(day=date)
        plan = Plan.objects.get(plan_id='PagePlus30')
        for transaction in Transaction.objects.filter(started__gt=that_date):
            if transaction.plan_str == 'PagePlus40' and transaction.pin and transaction.pin.startswith('18'):
                steps = TransactionStep.objects.filter(transaction=transaction).order_by('created')
                pin = transaction.get_pin_url()
                for step in steps:
                    if 'receipt' in step.adv_status:
                        pin = '%sa>' % step.adv_status[step.adv_status.find('<a'):step.adv_status.rfind('a>')].replace('>receipt<', '>%s<' % transaction.pin)
                print '%s %s ' % (transaction.pin, pin)
                UnusedPin.objects.create(company=transaction.company,
                                         plan=plan,
                                         pin=transaction.pin,
                                         used=False,
                                         notes='Pin bought from transaction %s' % transaction.get_full_url())
                transaction.pin = ''
                transaction.save()
        print "done"
