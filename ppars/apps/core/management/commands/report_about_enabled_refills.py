from django.core.management.base import BaseCommand
from ppars.apps.notification.models import Notification
from ppars.apps.core.models import CompanyProfile

class Command(BaseCommand):
    '''
    run_task
    '''
    args = 'no args'
    help = 'send_emails_for_tags_followers'

    def handle(self, *args, **options):
        print "start core"
        message = '''
            Report after fix for scheduled refills that were disabled by system automatically:
            Companies:
            </br>
            for company %s scheduled refills that were enabled:
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719233850/">6729783719233850</a>
            </br>
            for company %s scheduled refills that were enabled:
            <a href="http://ppars-a.py3pi.com/autorefill/4784812745293824/">4784812745293824</a>
            </br>
            for company %s scheduled refills that were enabled:
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719232812/">6729783719232812</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719235635/">6729783719235635</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719232775/">6729783719232775</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719235029/">6729783719235029</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719235587/">6729783719235587</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719234427/">6729783719234427</a>
            </br>
            for company %s scheduled refills that were enabled:
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719234367/">6729783719234367</a>
            </br>
            for company %s scheduled refills that were enabled:
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719236214/">6729783719236214</a>
            <a href="http://ppars-a.py3pi.com/autorefill/6729783719235794/">6729783719235794</a>
            ''' % (CompanyProfile.objects.get(id=5684666375864320).__unicode__(),
                   CompanyProfile.objects.get(id=5752754626625536).__unicode__(),
                   CompanyProfile.objects.get(id=6317690062897155).__unicode__(),
                   CompanyProfile.objects.get(id=6317690062897157).__unicode__(),
                   CompanyProfile.objects.get(id=6317690062897166).__unicode__())
        send_it = Notification.objects.create(
                    company=CompanyProfile.objects.get(superuser_profile=True),
                    customer=None,
                    email='info@e-zoffer.com',
                    phone_number='',
                    subject='Scheduled refills that was enabled',
                    body=message,
                    send_with=Notification.MAIL)
        send_it.send_notification()
        print "done"