from ppars.apps.core.models import PhoneNumber
from ppars.apps.notification.models import Notification


def prepayment_customer_notification(autorefill, need_paid, message):
    subject = "[{company_name}]Payments {messege_type}".format(company_name=autorefill.company.company_name, messege_type=message)
    body = 'Hi {customer_name},{messege_type}<br/><br/>#{phone_number}  expires on ' \
           '{expiration_date}. Please pay ${amount} so that we can '\
           'refill your phone.<br/><br/>Regards, {company_name}'.format(
            customer_name=autorefill.customer.first_name,
            messege_type=message,
            phone_number=autorefill.phone_number,
            expiration_date=autorefill.renewal_date.strftime('%m/%d/%y'),
            amount=need_paid,
            company_name=autorefill.company.company_name)

    notification = Notification.objects.create(
        company=autorefill.company,
        customer=autorefill.customer,
        email=autorefill.customer.primary_email,
        phone_number=autorefill.phone_number,
        subject=subject,
        body=body,
        send_with=autorefill.customer.notification_method)
    notification.send_notification()
