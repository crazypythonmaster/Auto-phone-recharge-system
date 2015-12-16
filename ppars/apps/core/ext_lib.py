import decimal
import tempfile
import csv
import urllib
import json
import logging
from django.db.models import Q
import pytz
import datetime
import requests
from django.conf import settings
from django.template.defaultfilters import slugify

logger = logging.getLogger('ppars')

'''
def import_pins(file):
    temp_file = tempfile.TemporaryFile()
    output = []
    for chunk in file.chunks():
            temp_file.write(chunk)
    temp_file.seek(0)
    format = os.path.splitext(file.name)[1].lower()
    if format in ['.csv', '.tsv']:
	reader = csv.reader(temp_file)
	reader.next()
	for row in reader:
		output.append(row[0])
    if format in ['.xls', '.xlsx']:

	workbook = xlrd.open_workbook(file_contents=temp_file.read())
	worksheet = workbook.sheet_by_name(workbook.sheet_names()[0])
	num_rows = worksheet.nrows - 1
	curr_row = 0
	while curr_row < num_rows:
		curr_row += 1
		row = worksheet.row(curr_row)
		output.append(row[0].value)
    temp_file.close
    return output
'''


def import_csv(file):
    temp_file = tempfile.TemporaryFile()
    output = []
    # for chunk in file.chunks():
    # temp_file.write(chunk)
    # temp_file.seek(0)
    reader = csv.reader(file.read().splitlines())
    cols = reader.next()
    for row in reader:
        entry = dict()
        for i in range(len(cols)):
            entry[slugify(cols[i]).replace('-', '_')] = row[i] or None
        output.append(entry)
    temp_file.close
    return output


def url_with_querystring(path, **kwargs):
    return path + '?' + urllib.urlencode(kwargs)


def mandrill_emailsend(key, emailBody, emailSubject, efrom, to):
    if not settings.TEST_MODE:
        form_fields = {
            "key": key,
            "message": {
                "html": emailBody,
                "subject": emailSubject,
                "from_email": efrom,
                "to": [{
                    "email": to,
                    "type": "to",
                }],
            }
        }
        # result = urlfetch.fetch(url='https://mandrillapp.com/api/1.0/messages/send.json',
        # payload=json.dumps(form_fields),
        #     method=urlfetch.POST,
        #     headers={'Content-Type': 'application/json'}
        # )
        result = requests.post('https://mandrillapp.com/api/1.0/messages/send.json',
                               data=json.dumps(form_fields),
                               headers={'Content-Type': 'application/json'})
        return result
    return False


def search_unused_charges(autorefill, amount):
    from ppars.apps.charge.models import Charge

    charges = Charge.objects.filter(
        customer=autorefill.customer,
        used=False,
        status=Charge.SUCCESS).order_by('created')
    exist_amount = decimal.Decimal(0.0)
    # calculate sum for cost
    for charge in charges:
        if exist_amount < amount:
            exist_amount = exist_amount + (charge.amount - charge.summ)
    result = amount - exist_amount
    if result < 0:
        return False
    else:
        return result


def login_site_request(url, url_success, user, user_tag, passw, passw_tag):
    payload = {user_tag: user, passw_tag: passw}
    s = requests.Session()
    s.post(url, data=payload)
    r = s.get(url_success)
    if r.url not in url_success:
        raise Exception("Failed to login to %s, please check the credentials" % url)
    base_url = r.url
    return s, base_url


def login_site(url, url_success, user, user_tag, passw, passw_tag):
    import mechanize
    import cookielib
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    br.open(url)
    br.select_form(nr=0)
    br.form[user_tag] = user
    br.form[passw_tag] = passw
    br.submit()
    br.open(url_success)
    if br.geturl() not in url_success:
        raise Exception("Failed to login to %s, please check the credentials" % url)
    return br


def number_of_transaction_from_month_by_now_of_company(company,
                                                       month_before=None):
    today = datetime.datetime.now(pytz.timezone('US/Eastern'))
    if month_before is None:
        month_before = 0
    if today.month <= month_before:
        month_before -= today.month
        year = today.year - 1
        month = 12 - month_before
    else:
        year = today.year
        month = today.month - month_before
    from ppars.apps.core.models import Transaction, AutoRefill

    manual_transaction = Transaction.objects.filter(Q(trigger__isnull=False,
                                                      trigger__icontains=Transaction.MANUAL,
                                                      company=company,
                                                      started__gte=datetime.date(year, month, 1)) |
                                                    Q(autorefill__isnull=False,
                                                      autorefill__trigger__icontains=AutoRefill.TRIGGER_MN,
                                                      company=company,
                                                      started__gte=datetime.date(year, month, 1)
                                                      )).count()
    schedule_transaction = Transaction.objects.filter(Q(trigger__isnull=False,
                                                        trigger__icontains=Transaction.SCEDULED,
                                                        company=company,
                                                        started__gte=datetime.date(year, month, 1)) |
                                                      Q(autorefill__isnull=False,
                                                        autorefill__trigger__icontains=AutoRefill.TRIGGER_SC,
                                                        company=company,
                                                        started__gte=datetime.date(year, month, 1)
                                                        )).count()
    return manual_transaction, schedule_transaction
