__author__ = 'eugene'

from django.core.management.base import BaseCommand
from ppars.apps.core.models import CompanyProfile, Customer, AutoRefill
from ppars.apps.charge.models import Charge, ChargeError
from ppars.apps.core.send_notifications import failed_precharge_company_notification, \
    failed_precharge_customer_notification, check_message_customer


class Command(BaseCommand):
    help = 'ls - list of jobs\n' \
           'example run job: ./manage.py run_job <<name_of_job>>'

    def handle(self, *args, **options):
        err_msg = args[0] if args else ''

        print 'Start creating new charge'

        charge = Charge.objects.create(
            company=CompanyProfile.objects.get(id=6270652252160001),
            customer=Customer.objects.get(id=6631476682555394),
            autorefill=AutoRefill.objects.get(id=6750428821717154),
            amount=0,
            payment_getaway=Charge.DOLLARPHONE,
            status=Charge.ERROR,
            adv_status='TEST CHARGE'
        )

        print 'Created new charge: %s' % charge.id

        charge.add_charge_step('precharge', Charge.ERROR, 'Charge ended with error: "%s"' % err_msg)
        charge_error, created = ChargeError.objects.get_or_create(charge=charge, step='charge', message='%s' % err_msg)

        if created and check_message_customer(err_msg):
            failed_precharge_customer_notification(charge)

        if charge.company.precharge_failed_email or not check_message_customer(err_msg):
            failed_precharge_company_notification(charge)

        print 'Sent error message'
