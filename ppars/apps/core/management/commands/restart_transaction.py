__author__ = 'eugene'

from django.core.management.base import BaseCommand
from ppars.apps.core.models import Transaction
from ppars.apps.core.tasks import queue_refill


class Command(BaseCommand):
    help = 'run job: ./manage.py run_job <<name_of_job>>'

    def handle(self, *args, **options):
        transaction = Transaction.objects.filter(id=6754102092517661).get()
        queue_refill.delay(transaction.id)