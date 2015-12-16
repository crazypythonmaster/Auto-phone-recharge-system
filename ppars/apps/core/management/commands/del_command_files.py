from datetime import datetime
from django.core.management.base import BaseCommand
import pytz
from ppars.apps.core.models import Plan


class Command(BaseCommand):
    '''
    del_command_files
    '''

    def handle(self, *args, **options):
        today = datetime.now(pytz.timezone('US/Eastern'))
        that_date = today.replace(day=07)
        Plan.objects.filter(created__gt=that_date).delete()
        # for plan in Plan.objects.filter(created__gt=that_date):
        #     from ppars.apps.price.models import PlanSellingPrice
        #     from django.contrib.admin.util import NestedObjects
        #     collector = NestedObjects(using='default') # or specific database
        #     collector.collect([plan])
        #     to_delete = collector.nested()
        #     for o in to_delete:
        #         message = ''
        #         if isinstance(o, Plan):
        #             plan_id = 'plan %s' % o
        #         elif isinstance(o, list):
        #             for sl in o:
        #                 if isinstance(sl, PlanSellingPrice):
        #                     continue
        #                 message = '%s %s %s' % (plan_id, type(sl), sl.id)
        #         if not message:
        #             plan.delete()
        #         else:
        #             print message

        print "done"