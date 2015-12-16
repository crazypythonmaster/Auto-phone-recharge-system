__author__ = 'eugene'

from django.core.management.base import BaseCommand
import ppars.apps.core.tasks


class Command(BaseCommand):
    help = 'run job: ./manage.py run_job <<name_of_job>>'

    def handle(self, *args, **options):
        jobs = [func.replace('_job', '') for func in dir(ppars.apps.core.tasks) if '_job' in func]

        if args and args[0] in jobs:
            print 'Start %s_job' % args[0]
            getattr(ppars.apps.core.tasks, '%s%s' % (args[0], '_job'))()
            print 'End %s_job' % args[0]
        else:
            print 'All available jobs:\n   %s' % '\n   '.join(jobs)
