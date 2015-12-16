__author__ = 'eugene'

from django.core.management.base import BaseCommand
from ppars.apps.core.tasks import queue_refill


class Command(BaseCommand):
    help = 'ls - list of jobs\n' \
           'example run job: ./manage.py run_job <<name_of_job>>'

    def handle(self, *args, **options):
        print 'Run transaction %s' % args[0]

        queue_refill(args[0])
