import cookielib
from BeautifulSoup import BeautifulSoup
import datetime
import decimal
import mechanize


def mdn_status(phone_number):
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent',
                      'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    br.open('https://www.airvoicewireless.com/PINRefill.aspx')
    if not br.response().code == 200:
        return {
            'status_find': False,
            'error': "Internal error on AirVoice. Status code: %s." % br.response().status_code
        }
    br.select_form(nr=0)
    br.form['ctl00$ContentPlaceHolder1$txtSubscriberNumber'] = phone_number
    br.submit()
    soup = BeautifulSoup(br.response().read())
    number = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblSubscriberNumber'}).text
    rate_plan = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblratePlan'}).text
    balance = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblmainAccountBalance'}).text
    exp_date = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblairTimeExpirationDate'}).text
    cancel_date = soup.find('span', {'id': 'ctl00_ContentPlaceHolder1_lblcancelDate'}).text
    status_find = True
    error = ''
    if 'n/a' in number:
        status_find = False
        error = 'Can not find the number.'
    if 'n/a' not in exp_date:
        exp_date = datetime.datetime.strptime(exp_date, "%m/%d/%Y").date()
    else:
        exp_date = ''
    if 'n/a' not in cancel_date:
        cancel_date = datetime.datetime.strptime(cancel_date, "%m/%d/%Y").date()
    return {'number': number,
            'rate_plan': rate_plan,
            'balance': balance,
            'exp_date':  exp_date,
            'cancel_date': cancel_date,
            'status_find': status_find,
            'error': error
            }


def verify_carrier(phone_number, plan_amount=None):
    from ppars.apps.core.models import Carrier, Plan
    carrier = Carrier.objects.filter(name__icontains='AIRVOICE').get()
    result = {
        'valid': False,
        'valid_for_schedule': False,
        'plan': '',
        'carrier': carrier,
        'renewal_date': '',
        'schedule': '',
        'mdn_status': '',
        'error': ''
    }
    answer = mdn_status(phone_number)
    if answer['status_find']:
        result['valid'] = True
        result['mdn_status'] = 'Subscriber Number: %s\n' \
                               'Rate Plan: %s\n' \
                               'Main Account Balance: %s\n' \
                               'Airtime Exp Date: %s\n' \
                               'Cancel Date: %s\n' % \
                               (answer['number'],
                                answer['rate_plan'],
                                answer['balance'],
                                answer['exp_date'],
                                answer['cancel_date'])
        if answer['exp_date']:
            result['renewal_date'] = answer['exp_date']
        else:
            result['error'] += 'Can not get renewal date.'
        if carrier.default_time:
            result['schedule'] = carrier.default_time
        else:
            result['error'] += '\nCan not get default schedule time.'
        if plan_amount:
            plan_amount = decimal.Decimal(plan_amount)
            if plan_amount > 50:
                result['plan'] = Plan.objects.filter(carrier=carrier, plan_cost=decimal.Decimal(50.00)).first()
            elif plan_amount > 30:
                result['plan'] = Plan.objects.filter(carrier=carrier, plan_id='Airvoice30mp').first()
            elif plan_amount > 20:
                result['plan'] = Plan.objects.filter(carrier=carrier, api_id='30086380', plan_cost=decimal.Decimal(20.00)).first()
            elif plan_amount > 9:
                result['plan'] = Plan.objects.filter(carrier=carrier, api_id='30077500').first()
        else:
            plan = Plan.objects.filter(carrier=carrier,
                                       rate_plan__icontains=answer['rate_plan'])
            if plan:
                result['plan'] = plan[0]
        if not result['plan']:
            result['error'] += '\nCan not get plan.'
        if result['plan'] and result['renewal_date'] and result['schedule']:
            result['valid_for_schedule'] = True
    else:
        result['valid'] = False
        result['error'] = answer['error']
    return result
