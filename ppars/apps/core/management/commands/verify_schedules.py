from django.core.management.base import BaseCommand
from ppars.apps.core.models import CompanyProfile
from ppars.apps.core.tasks import verify_scheduled_refills


class Command(BaseCommand):
    '''
    verify schedules
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print 'Verify Schedules\n'
        company_id = raw_input("Enter the company id: ")
        company = CompanyProfile.objects.get(id=company_id)
        verify_scheduled_refills.delay(company)
        print 'Result will be send to company.'
