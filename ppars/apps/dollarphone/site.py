import json
import logging
import traceback
from BeautifulSoup import BeautifulSoup
import decimal
from django.conf import settings
import requests
from django.core.cache import cache
from requests.auth import HTTPBasicAuth
import time
# Should be changed in new core. relation to other package
from ppars.apps.core.company_notifications import send_dp_low_balance

"""
This package used for making refill for scrapping on https://www.dollarphonepinless.com

Package provide 4 methods for external using.

-- purchase_pin_cash
    Method for buying pin with purchase balance on DP profile

-- purchase_top_up_cash
    Method for making refill phone number for RTR plans with purchase balance
    on DP profile

-- purchase_pin_cc
    Method for buying pin with purchase creditcard

-- purchase_top_up_cc
    Method for making refill phone number for RTR plans with purchase creditcard
"""

logger = logging.getLogger('ppars')
COMPLETED = "Completed"
FAILED = "Fulfillment Failed"
PIN = 'pin'
TOP_UP = 'top_up'
CREDITCARD = 'Customer Credit Card'
CASH = 'Cash'

required_fields = ('ppm_order_prepaid_mobile_product_group_id',
                   'ppm_order_prepaid_mobile_product_id',
                   'ppm_order_face_amount',
                   'ppm_order_payment_option')


def purchase_pin_cash(form_fields):
    """
    :param form_fields: dictionary with required fields
        form_fields = {
                'username': Dollar phone  username
                'password': Dollar phone  password
                'Carrier': Refill carrier
                'Plan': Refill plan
                'Amount': Refill plan amount
                'transaction': transaction ID. Unique identical number for dp
                'company': current store
        }
    :type form_fields: dict

    :return: dp transaction status, message, pin
    :rtype: str, str, str
    """
    return _dp_site_request(PIN, CASH, form_fields['username'],
                            form_fields['password'], form_fields['Carrier'],
                            form_fields['Plan'], form_fields['Amount'],
                            form_fields['transaction'], form_fields['company'])


def purchase_pin_cc(form_fields):
    """
    :param form_fields: dictionary with required fields
        form_fields = {
                'username': Dollar phone  username
                'password': Dollar phone  password
                'Carrier': Refill carrier
                'Plan': Refill plan
                'Amount': Refill plan amount
                'transaction': transaction ID. Unique identical number for dp
                'company': current store
                'Customer': customer with credit card
        }
    :type form_fields: dict

    :return: dp transaction status, message, pin
    :rtype: str, str, str
    """
    return _dp_site_request(PIN, CREDITCARD, form_fields['username'],
                            form_fields['password'], form_fields['Carrier'],
                            form_fields['Plan'], form_fields['Amount'],
                            form_fields['transaction'], form_fields['company'],
                            customer=form_fields['Customer'])


def purchase_top_up_cash(form_fields):
    """
    :param form_fields: dictionary with required fields
        form_fields = {
                'username': Dollar phone  username
                'password': Dollar phone  password
                'Carrier': Refill carrier
                'Plan': Refill plan
                'Amount': Refill plan amount
                'transaction': transaction ID. Unique identical number for dp
                'company': current store
                'phone_number': Refill phone_number
        }
    :type form_fields: dict

    :return: dp transaction status, message, pin
    :rtype: str, str, str
    """
    return _dp_site_request(TOP_UP, CASH, form_fields['username'],
                            form_fields['password'], form_fields['Carrier'],
                            form_fields['Plan'], form_fields['Amount'],
                            form_fields['transaction'], form_fields['company'],
                            form_fields['phone_number'])


def purchase_top_up_cc(form_fields):
    """
    :param form_fields: dictionary with required fields
        form_fields = {
                'username': Dollar phone  username
                'password': Dollar phone  password
                'Carrier': Refill carrier
                'Plan': Refill plan
                'Amount': Refill plan amount
                'transaction': transaction ID. Unique identical number for dp
                'company': current store
                'phone_number': Refill phone_number
                'Customer': customer with credit card
        }
    :type form_fields: dict

    :return: dp transaction status, message, pin
    :rtype: str, str, str
    """
    return _dp_site_request(TOP_UP, CREDITCARD, form_fields['username'],
                            form_fields['password'], form_fields['Carrier'],
                            form_fields['Plan'], form_fields['Amount'],
                            form_fields['transaction'], form_fields['company'],
                            form_fields['phone_number'], form_fields['Customer'])


def dollar_phone_site_authorization(username, password):
    """
    :param username: dollarphone username
    :type username: str

    :param password: dollarphone user password
    :type password: str

    :return s: session object
    :rtype s: requests.Session:
    """
    if cache.get('dpra_%s' % username):
        logger.debug('dpma_from cache %s' % username)
        return cache.get('dpra_%s' % username)
    s = requests.Session()
    s.get('https://www.dollarphonepinless.com/sign-in', auth=HTTPBasicAuth(username, password))
    r = s.get('https://www.dollarphonepinless.com/dashboard')
    status_code = r.status_code
    if status_code != 200:
        logger.debug('Status code: %s Page: %s' % (status_code, r.text))
        raise Exception("Failed to login to Dollar Phone, please check the credentials")
    cache.set('dpra_%s' % username, s)
    return s


def check_receipt(s, receipt_id):
    """
    :param s: session object
    :type s: requests.Session

    :param receipt_id: receipt id
    :type receipt_id: str

    :return: receipt page
    :rtype: str

    :raise Exception
    """
    co = 0
    while True:
        co += 1
        r = s.get(u'https://www.dollarphonepinless.com/ppm_orders/%s/check_status.json' % receipt_id)
        logger.debug('check_status.json %s Page %s' % (r.url, r.text))
        pin_status = json.loads(r.text)
        if pin_status['status'] == COMPLETED:
            r = s.get('https://www.dollarphonepinless.com/ppm_orders/%s/receipt' % receipt_id)
            receipt = r.text
            logger.debug('receipt %s receipt_id %s' % (receipt, receipt_id))
            return receipt
        elif pin_status['status'] == FAILED:
            raise Exception(
                'DollarPhone transaction failed, check the <a target="blank" '
                'href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>'
                ' for more information' % receipt_id)
        if co > 10:
            raise Exception(
                'DollarPhone transaction no response, check the '
                '<a target="blank" '
                'href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>'
                ' for more information' % receipt_id)
        time.sleep(10)


def get_pin(receipt):
    """
    :param receipt: receipt page
    :type receipt: str

    :return: pin
    :rtype: str
    """
    soup = BeautifulSoup(receipt)
    table = soup.find("table")
    logger.debug('table %s' % table)
    for row in table.findAll('tr')[1:]:
        col = row.findAll('td')
        if col[0].string.strip() == 'PIN:':
            return col[1].div.strong.string.strip()
    return ''


def _get_authenticity_token(soup):
    """
    :param soup: response page
    :type soup: BeautifulSoup

    :return: authenticity token
    :rtype: str
    """
    for token in soup.findAll('input'):
        if token.get('name') == 'authenticity_token':
            return token.get('value')
    return ''


def _get_carrier_id(soup, carrier):
    """
    :param soup: response page
    :type soup: BeautifulSoup

    :param carrier: Carrier name
    :type carrier: str

    :return: carrier id
    :rtype: str
    """
    for c in soup.find('select', id="group-list"):
        try:
            if c.text.replace('&amp;', '&') == carrier:
                return c.get('value')
        except AttributeError:
            pass
    return ''


def _get_plan_id(soup, plan):
    """
    :param soup: response page
    :type soup: BeautifulSoup

    :param plan: Plan name
    :type plan: str

    :return: plan id
    :rtype: str
    """
    for p in soup.find('select', id="product-list"):
        try:
            if p.text.replace('&amp;', '&') == plan:
                return p.get('value')
        except AttributeError:
            pass
    return ''


def _get_cost_id(soup, amount):
    """
    :param soup: response page
    :type soup: BeautifulSoup

    :param amount: costs
    :type amount: str

    :return: costs id
    :rtype: str
    """
    for cost in soup.find('select', id="denomination-list"):
        try:
            if cost.text == amount:
                return cost.get('value')
        except AttributeError:
            pass
    return ''


def _get_reference_number(soup):
    """
    :param soup: response page
    :type soup: BeautifulSoup

    :return: reference number
    :rtype: str
    """
    for token in soup.findAll('input'):
        if token.get('name') == 'ppm_order[reference_number]':
            return token.get('value')
    return ''


def _generate_refill_data(product_type, payment_type, authenticity_token, cost_id, carrier_id, plan_id):
    """
    :param product_type: type of product 'pin' or 'top_up'
    :type product_type: str

    :param payment_type: Cash or Customer Credit Card
    :type payment_type: str

    :param authenticity_token: authenticity token
    :type : str

    :param cost_id: costs id
    :type : str

    :param carrier_id: carrier id
    :type : str
    :param plan_id: plan id
    :type : str

    :return: dict
    """
    return {
            'authenticity_token': authenticity_token,
            'commit': "Continue",
            'location': 'domestic',
            'ppm_order[always_use_secondary_funding_source]': '',
            'ppm_order[country_code]': 'US',
            'ppm_order[face_amount]': cost_id,
            'ppm_order[notification_locale]': 'en',
            'ppm_order[notification_phone_number]': '',
            'ppm_order[payment_option]': payment_type,
            'ppm_order[prepaid_mobile_product_group_id]': carrier_id,
            'ppm_order[prepaid_mobile_product_id]': plan_id,
            'ppm_order[use_secondary_funding_source]': '',
            'product_type': product_type,
            }


def _generate_cc_data(reference_number, customer):
    """
    :param reference_number: reference number
    :type reference_number: str

    :param customer:
    :type: apps.core.models.Customer

    :return: dict
    """
    return {
            'commit': 'Process Order',
            'ppm_order[reference_number]': reference_number,
            'ppm_order[single_use_credit_card_attributes][address1]': customer.address,
            'ppm_order[single_use_credit_card_attributes][card_number]': customer.get_local_card().number,
            'ppm_order[single_use_credit_card_attributes][city]': customer.city,
            'ppm_order[single_use_credit_card_attributes][country]': 'US',
            'ppm_order[single_use_credit_card_attributes][email]': customer.primary_email,
            'ppm_order[single_use_credit_card_attributes][expires_on(1i)]': customer.get_local_card().expiration_year,
            'ppm_order[single_use_credit_card_attributes][expires_on(2i)]': customer.get_local_card().expiration_month,
            'ppm_order[single_use_credit_card_attributes][expires_on(3i)]': '1',
            'ppm_order[single_use_credit_card_attributes][name]': customer.full_name,
            'ppm_order[single_use_credit_card_attributes][phone]': '',
            'ppm_order[single_use_credit_card_attributes][state]': 'NY',
            'ppm_order[single_use_credit_card_attributes][verification_value]': customer.get_local_card().cvv,
            'ppm_order[single_use_credit_card_attributes][zip]': customer.zip,
            'ppm_order[skip_check_for_duplicates]': '',
        }


def _scrapping_dollar_phone_errors(page, **kwargs):
    message = ''
    soup = BeautifulSoup(page)

    # please enter 4 digit token
    message = '%s%s' % (message, enter_digits_token(kwargs['url']))

    # highlighted flash error
    if 'div class="flash-error"' in page:
        for span in soup.findAll('div', {"class": "flash-error"}):
            message = '%s %s' % (message, span.find(text=True))

    # fields error
    message = '%s%s' % (message, _fields_error(soup))

    # error with incorrect credit card data
    message = '%s%s' % (message, _credit_card_errors(soup, page))

    # dialog message to user
    if 'dialog' in page:
        for div in soup.findAll('div'):
            if div.get('class') == 'dialog':
                h1 = div.find('h1')
                p = div.find('p')
                message = '%s %s' % (h1.text, p.text)

    # low balance on dp profile
    low_balance = _low_cash_balance(soup, page, kwargs['cost'])
    if low_balance:
        send_dp_low_balance(kwargs['company'], kwargs['transaction'])
        message = '%s%s' % (message, low_balance)

    # can't find any message in response
    if not message:
        message = 'Undefined response from DollarPhone. Please check order at' \
                  ' DollarPhone site and you can add pin to Unused'
    logger.debug('After scrapping eerro message: %s' % message)
    return message


def enter_digits_token(url):
    """
    :param url: url
    :type url: str

    :return: error message
    :rtype: str
    """
    if '/authentication_required.html' in str(url):
        return 'Please login to the Dollarphone and enter your 4-digit Security PIN.'
    return ''


def _low_cash_balance(soup, page, cost):
    """
    :param soup: BeautifulSoup object
    :type soup: BeautifulSoup

    :param page: HTML page
    :type page: str

    :param cost: digits in string in format $xx.yy
    :type cost: str

    :return: error message
    :rtype: str
    """
    if "id='balance'" in page:
        cash_balance = decimal.Decimal(soup.find('tr', id='balance').find('td', {'class': 'data-cell'}).find(text=True)[1:].replace(',', ''))
        if decimal.Decimal(cost[1:]) > cash_balance:
            return 'Cash Balance: $%s' % cash_balance
    return ''


def _credit_card_errors(soup, page):
    """
    :param soup: BeautifulSoup object
    :type soup: BeautifulSoup

    :param page: HTML page
    :type page: str

    :return: error message
    :rtype: str
    """
    message = ''
    if 'error-explanation' in page:
        h = soup.find('div', id='error-explanation')
        for h1 in h.findAll('div'):
            if h1.get('class') == 'error-messages red':
                message = ' %s' % h1.text
        d = soup.find('div', id='credit-card-information')
        for p1 in d.findAll('p'):
            if p1.get('class') == 'inline-errors':
                message = ' %s %s %s' % (message, p1.parent.label.text, p1.text)
        d = soup.find('div', id='billing-address')
        for p1 in d.findAll('p'):
            if p1.get('class') == 'inline-errors':
                message = ' %s %s %s' % (message, p1.parent.label.text, p1.text)
    return message


def _fields_error(soup):
    """
    :param soup: BeautifulSoup object
    :type soup: BeautifulSoup

    :return: error message
    :rtype: str
    """
    message = ''
    for div in soup.findAll('div', {'class': 'input-wrapper'}):
        label = 'field'
        for span in div.findAll('span', {'class': 'form-field-error'}):
            if 'label' in str(span):
                label = span.find('label').text
                break
        if 'inline-errors' in str(div):
            warning = div.find('p', {'class': 'inline-errors'}).text
            message = '%s %s %s,' % (message, label, warning)
    return message


def _dp_site_request(refill_type, payment_type, username, password, carrier,
                    plan, amount, transaction, company, phone_number=None,
                    customer=None):
    if settings.TEST_MODE:
        response = {
            'status': 1,
            'pin': '123456',
            'adv_status': 'Dollar Phone on Test mode',
            'receipt_id': '111222333'
            }
        return response

    response = {
        'status': 0,
        'pin': '',
        'adv_status': '',
        'receipt_id': ''
        }
    try:
        s = dollar_phone_site_authorization(username, password)
        r = s.get('https://www.dollarphonepinless.com/prepaid_mobile_orders/domestic/%s/new' % refill_type)
        soup = BeautifulSoup(r.text)

        authenticity_token = _get_authenticity_token(soup)
        carrier_id = _get_carrier_id(soup, carrier)
        plan_id = _get_plan_id(soup, plan)
        cost_id = _get_cost_id(soup, amount)

        data = _generate_refill_data(refill_type, payment_type, authenticity_token, cost_id, carrier_id, plan_id)
        if TOP_UP == refill_type:
            data.update({'ppm_order[prepaid_mobile_phone]': phone_number})
        order_url = 'https://www.dollarphonepinless.com/ppm_orders/confirm?location=domestic&product_type=%s' % refill_type
        r = s.post(order_url, data)

        if CREDITCARD == payment_type:
            soup = BeautifulSoup(r.text)
            reference_number = _get_reference_number(soup)
            order = _generate_cc_data(reference_number, customer)
            data.update(order)

        pin_url = 'https://www.dollarphonepinless.com/ppm_orders'
        r = s.post(pin_url, data)
        logger.debug('url %s Page %s' % (r.url, r.text))
        if str(r.url).endswith('/processing'):
            response['receipt_id'] = str(r.url).replace('https://www.dollarphonepinless.com/ppm_orders/', '').replace('/processing', '')
            time.sleep(10)
        elif r.url in pin_url:
            message = _scrapping_dollar_phone_errors(r.text,
                                                     url=r.url,
                                                     cost=amount,
                                                     transaction=transaction,
                                                     company=company)
            raise Exception(message)
        receipt = check_receipt(s, response['receipt_id'])
        response['status'] = 1
        if TOP_UP == refill_type:
            response['adv_status'] = 'Phone was refilled, details are at ' \
                     '<a target="blank" href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' % response['receipt_id']
        else:
            response['pin'] = get_pin(receipt)
            response['adv_status'] = 'Pin %s extracted from Dollar Phone, details are at ' \
                         '<a target="blank" href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' % \
                         (response['pin'], response['receipt_id'])
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        response['status'] = 0
        response['adv_status'] = "Failure :%s" % e
    finally:
        return response
