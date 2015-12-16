from django.core.management.base import BaseCommand
from ppars.apps.core.models import PhoneNumber, UserProfile
from ppars.apps.core.tasks import auto_creation_schedules_refill


class Command(BaseCommand):
    '''
    create_scedules
    '''

    def handle(self, *args, **options):
        pns = ['8482220188',
               '8482107118',
               '7189382920',
               '7325976237',
               '7325031516',
               '6148964197',
               '8482100946',
               '8482234045',
               '7322795785',
               '8482233736',
               '7326007989',
               '8482210568',
               '9086701405',
               '3472661946',
               '7325510569',
               '3474713669',
               '7325528582',
               '8482233806',
               '7326440962',
               '84/82403470',
               '8482210091',
               '8482143886',
               '8482349910',
               '7323674296',
               '732503532',
               '7325752066',
               '7322374967',
               '7328645132',
               '7325694010',
               '7325692851',
               '9089104957',
               '7325033568',
               '9082422788',
               '7326913902',
               '3479206890',
               '8482991847',
               '8485256879',
               '8485259737',
               '9089101679',
               '7325972905',
               '3474523296']

        company_id = raw_input("Enter the company id: ")
        profile_id = raw_input("Enter the profile id: ")
        profile = UserProfile.objects.get(id=profile_id)
        customers_for_scheduled = []
        bill_amount = None
        for p in pns:
            for phone in PhoneNumber.objects.filter(company_id=company_id,
                                                    number=p).exclude(
                    customer=None):
                customers_for_scheduled.append(
                    [phone.customer.id, p, bill_amount])
        # auto_creation_schedules_refill.delay(customers_for_scheduled,
        #                                      profile)
        print customers_for_scheduled
        print profile
        print "done"
