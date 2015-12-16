import logging
import traceback
from ppars.apps.core.models import CompanyProfile, CaptchaLogs
from ppars.apps.notification.models import Notification

logger = logging.getLogger('ppars')


def send_company_notification(email, subject, body, send_with):
    notification = Notification.objects.create(
        company=CompanyProfile.objects.get(superuser_profile=True),
        email=email,
        subject=subject,
        body=body,
        send_with=send_with)
    notification.send_notification()


def send_pin_error_mail(transaction, error_message):
    if transaction.company.pin_error:
        subject = "[%s] Pin Error in transaction %s" % (
            transaction.company.company_name, transaction.id)
        pin = ''
        if transaction.pin:
            pin = ' with pin %s' % transaction.pin
        body = '''Hi %s,<br/><br/>
            System failed for customer %s's phone %s with plan %s%s.
            <a href=\"%s\">Transaction</a> errored in step %s due to \"%s\".
            <br/><br/>Regards, %s ''' % \
               (
                   transaction.user,
                   transaction.customer,
                   transaction.autorefill.phone_number,
                   transaction.autorefill.plan,
                   pin,
                   transaction.get_full_url(),
                   transaction.current_step,
                   error_message,
                   CompanyProfile.objects.get(superuser_profile=True).company_name,
               )
        try:
            send_company_notification(transaction.company.email_id, subject, body,
                                  Notification.MAIL)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (
                e, traceback.format_exc(limit=10)))


def send_customer_import_status(company, result):
    subject = "[%s] Status of Customer Import" % company.company_name
    body = '''The status of customer import is as follow <br/><br/>
                <table>
                    <thead>
                        <tr>
                            <th>First Name</th>
                            <th>Middle Name</th>
                            <th>Last Name</th>
                            <th>Primary Email</th>
                            <th>Phone Numbers</th>
                            <th>SellerCloud Account ID</th>
                            <th>Address</th>
                            <th>City</th>
                            <th>State</th>
                            <th>Zip</th>
                            <th>Charge Type</th>
                            <th>Charge Gateway</th>
                            <th>Card Number</th>
                            <th>Authorize ID</th>
                            <th>USAePay customer ID</th>
                            <th>USAePay CustID</th>
                            <th>Selling Price Level</th>
                            <th>Customer Discount</th>
                            <th>Taxable</th>
                            <th>Precharge SMS</th>
                            <th>Email Successful Refill</th>
                            <th>Email Successful Charge</th>
                            <th>Send Status</th>
                            <th>Send Pin PreRefill</th>
                            <th>Group SMS</th>
                            <th>Enabled</th>
                            <th>Notes</th>
                            <th>Import Status</th>
                        </tr>
                    </thead>
                <tbody>'''
    for customer in result:
        body = '%s ' \
               '<tr>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '<td>%s</td>' \
               '</tr>' % (body,
                          customer['first_name'] or '',
                          customer['middle_name'] or '',
                          customer['last_name'] or '',
                          customer['primary_email'] or '',
                          customer['phone_numbers'] or '',
                          customer['sc_account'] or '',
                          customer['address'] or '',
                          customer['city'] or '',
                          customer['state'] or '',
                          customer['zip'] or '',
                          customer['charge_type'] or '',
                          customer['charge_getaway'] or '',
                          customer['creditcard'] or '',
                          customer['authorize_id'] or '',
                          customer['usaepay_customer_id'] or '',
                          customer['usaepay_custid'] or '',
                          customer['selling_price_level'] or '',
                          customer['customer_discount'] or '',
                          customer['taxable'] or '',
                          customer['precharge_sms'] or '',
                          customer['email_success_refill'] or '',
                          customer['email_success_charge'] or '',
                          customer['send_status'] or '',
                          customer['send_pin_prerefill'] or '',
                          customer['group_sms'] or '',
                          customer['enabled'] or '',
                          customer['notes'] or '',
                          customer['import_status'] or '',)
    body = '%s </tbody></table>' % body
    try:
        send_company_notification(company.email_id, subject, body,
                                  Notification.MAIL)
    except Exception, e:
        logger.error(
            "Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))


def send_autorefill_import_status(schedule_limit_status, company, result=[]):
    if schedule_limit_status == 0:
        subject = "[EZ-Cloud Autorefill] Status of Scheduled Refill Import"
        body = '''The status of scheduled refill imports is as follow <br/><br/>
                <table>
                    <thead>
                        <tr>
                            <th>Customer</th>
                            <th>Phone Number</th>
                            <th>Plan</th>
                            <th>Renewal Date</th>
                            <th>Renewal End Date</th>
                            <th>Renewal Interval</th>
                            <th>Schedule</th>
                            <th>Notes</th>
                            <th>Enabled</th>
                            <th>Import Status</th>
                        </tr>
                    </thead>
                <tbody>'''
        for r in result:
            body = '''%s<tr>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                            <td>%s</td>
                        </tr>''' % \
                   (body,
                    r['customer'],
                    r['phone_number'],
                    r['plan'],
                    r['renewal_date'],
                    r['renewal_end_date'],
                    r['renewal_interval'],
                    r['schedule'],
                    r['notes'],
                    r['enabled'],
                    r['import_status'])
        body = body + '</tbody></table><br/><br/>'
        notification = Notification.objects.create(
            company=CompanyProfile.objects.get(superuser_profile=True),
            email=company.email_id,
            subject=subject,
            body=body,
            send_with=Notification.MAIL
        )
    else:
        subject = subject = "[EZ-Cloud Autorefill] Status of Scheduled Refill Import"
        body = """You can't import autorefills because the amount of imported Autorefills exceed your limit %s Autorefills.
        Please contact administrator.""" % schedule_limit_status
        notification = Notification.objects.create(
            company=CompanyProfile.objects.get(superuser_profile=True),
            email=company.email_id,
            subject=subject,
            body=body,
            send_with=Notification.MAIL
        )
    notification.send_notification()


def send_deathbycaptcha_low_balance(super_company, balance):
    subject = "[%s]Low balance on <a href=\"http://www.deathbycaptcha.com/\">DeathByCaptcha</a>" % super_company.company_name
    body = "Hi Admin,<br/><br/>You have only %s $ balance on DeathByCaptcha. " \
           "Please, charge you " \
           "<a href=\"http://www.deathbycaptcha.com/user/order\">balance</a>." \
           "<br/></br>Regards, %s" % (
                balance,  CompanyProfile.objects.get(superuser_profile=True).company_name)
    try:
        send_company_notification(super_company.email_id, subject, body, Notification.MAIL)
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (
            e, traceback.format_exc(limit=10)))


def send_deathbycaptcha_report(super_company):
    subject = "[%s]Report of %s used captha's" % (super_company.company_name, super_company.deathbycaptcha_count)
    start = CaptchaLogs.objects.count() - super_company.deathbycaptcha_count
    logs = CaptchaLogs.objects.all().order_by('created')[start:]
    bodies = [log.get_string() for log in logs]
    body ='<br/>'.join(bodies)
    try:
        send_company_notification(super_company.email_id, subject, body, Notification.MAIL)
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (
            e, traceback.format_exc(limit=10)))


def send_dp_low_balance(company, transaction):
    subject = "[%s]DollarPhone insufficient funds" % company.company_name
    body = 'Hi %s,<br/><br/> we tried to get a pin for <a href="%s">transaction</a>' \
           ' but you don`t have enough funds in your DollarPhone account. ' \
           'Please refill it. <br/></br>Regards, %s' % \
           (company.company_name,
            transaction.get_full_url(),
            CompanyProfile.objects.get(superuser_profile=True).company_name)
    try:
        send_company_notification(company.email_id, subject, body, Notification.MAIL)
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (
            e, traceback.format_exc(limit=10)))