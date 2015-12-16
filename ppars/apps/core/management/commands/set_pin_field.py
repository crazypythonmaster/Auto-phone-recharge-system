from datetime import timedelta, datetime, time
import decimal
from django.core.management.base import BaseCommand
from ppars.apps.core.models import AutoRefill, Transaction, PinReport, PinField


class Command(BaseCommand):
    '''
    set_pin_field
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        PinField.objects.all().delete()
        print "start core"
        for report in PinReport.objects.all():
            order = report.report
            plan = ''
            cost = None
            if '<strong>' in order:
                parts = order.replace('<strong>', '').split('</strong><br/>')
                report.subject = parts[0]
                for row in parts[1].split('<br/>'):
                    if 'refund' in row.lower():
                        continue
                    try:
                        pin = row.split("\"")[1]
                        plan = row.split("\"")[3]
                        cost = decimal.Decimal(row.replace(']', '').split('[$')[1])
                        PinField.objects.create(pin_report=report, pin=pin, plan=plan, cost=cost)
                    except Exception, e:
                        print row, e
            else:
                report.subject = 'Pin report %s' % report.created.strftime('%m/%d/%y')
                for row in order.split('<br/>'):
                    try:
                        pin = row
                        PinField.objects.create(pin_report=report, pin=pin, plan=plan, cost=cost)
                    except Exception, e:
                        print row, e
            report.save()
        print "done"
