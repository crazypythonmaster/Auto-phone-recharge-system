from django.core.management.base import BaseCommand
from ppars.apps.core.models import CompanyProfile, Plan
from ppars.apps.price.models import SellingPriceLevel, PlanSellingPrice


class Command(BaseCommand):
    '''
    make_selling_price
    '''

    def handle(self, *args, **options):
        company_key = raw_input("Enter the company id: ")
        company = CompanyProfile.objects.get(id=company_key)
        for plan in Plan.objects.all():
            for price_level in SellingPriceLevel.objects.all():
                PlanSellingPrice.objects.create(carrier=plan.carrier,
                                                plan=plan,
                                                company=company,
                                                price_level=price_level,
                                                selling_price=plan.plan_cost)
        print "done"