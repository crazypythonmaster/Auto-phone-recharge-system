from django.core.management.base import BaseCommand
from ppars.apps.core.models import Customer, CompanyProfile, PhoneNumber
from ppars.apps.core.redfin import log_in_redfin, get_cc_data


class Command(BaseCommand):
    '''
    add_redfin_card
    '''

    def handle(self, *args, **options):
        print 'start'
        redfin_url = 'https://secure.redfinnet.com/admin/'
        company_id = raw_input("Enter the company id: ")
        company = CompanyProfile.objects.get(id=company_id)
        s = log_in_redfin(company.redfin_username, company.redfin_password)
        for customer in Customer.objects.filter(company=company):
            try:
                if customer.redfin_customer_key and not customer.creditcard:
                    r = s.get('%srecurring/add_payment.aspx?id=%s&paymentid=%s&type=CC' %
                              (redfin_url,
                               customer.redfin_customer_key,
                               customer.redfin_cc_info_key))
                    customer_cc_data = get_cc_data(r.text)
                    if customer_cc_data:
                        customer.creditcard = customer_cc_data['card_number']
                        customer.notes = '%s card exp: %s,' \
                                         'card name: %s, ' \
                                         'card adrress: %s, ' \
                                         'card zip: %s,' % (
                                             customer.notes,
                                             customer_cc_data['card_exp'],
                                             customer_cc_data['card_name'],
                                             customer_cc_data['card_adrress'],
                                             customer_cc_data['card_zip'],
                                         )
                        customer.save()
            except Exception, e:
                print e
        print 'Done'
