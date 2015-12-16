import logging
from BeautifulSoup import BeautifulSoup
from django.conf import settings
import requests

logger = logging.getLogger('ppars')


def log_in_redfin(username, password):
    """
    :param username: username for log in red fin network
    :type username: str

    :param password: password for log in red fin network
    :type password: str

    :returns: s, base_url
    :rtype: requests.Session, string
    """

    if settings.TEST_MODE:
        redfin_url = 'https://staging.redfinnet.com/admin/'
    else:
        redfin_url = 'https://secure.redfinnet.com/admin/'
    s = requests.Session()

    # enter to login page for taken tokens
    r = s.get('%slogin.aspx' % redfin_url)
    payload = get_tokens(r.text)
    payload.update({'username': username,
                    'password': password,
                    'Submit': 'Login'})
    # login
    r = s.post('%slogin.aspx' % redfin_url, data=payload)
    if r.url not in '%shome.aspx' % redfin_url:
        raise Exception("Failed to login to %s, please check the credentials" % redfin_url)
    logger.debug('LOGINED %s' % r.url)
    return s


def get_tokens(page):
    """
    :param page: HTML page
    :type: unicode

    :return: payload
    :rtype: dict
    """
    soup = BeautifulSoup(page)
    payload = {
           '__EVENTARGUMENT': soup.find('input', {'name': '__EVENTARGUMENT'}).get('value') if '__EVENTARGUMENT' in page else '',
           '__EVENTTARGET': soup.find('input', {'name': '__EVENTTARGET'}).get('value') if '__EVENTTARGET' in page else '',
           '__EVENTVALIDATION': soup.find('input', {'name': '__EVENTVALIDATION'}).get('value') if '__EVENTVALIDATION' in page else '',
           '__VIEWSTATE': soup.find('input', {'name': '__VIEWSTATE'}).get('value') if '__VIEWSTATE' in page else '',
           '__VIEWSTATEGENERATOR': soup.find('input', {'name': '__VIEWSTATEGENERATOR'}).get('value') if '__VIEWSTATEGENERATOR' in page else '',
           '___pffv___': soup.find('input', {'name': '___pffv___'}).get('value') if '___pffv___' in page else ''}
    return payload


def get_customer_data(page):
    """
    :param page: HTML page
    :type: unicode

    :return: customer_data
    :rtype: dict
    """
    soup = BeautifulSoup(page)
    customer_data = {
        'first_name': (soup.find('input', {'id': 'First_Name'}).get(
            'value') if 'First_Name' in page else ''),
        'last_name': (soup.find('input', {'id': 'Last_Name'}).get(
            'value') if 'Last_Name' in page else ''),
        'title': (soup.find('input', {'id': 'Title'}).get(
            'value') if 'Title' in page else ''),
        'department': (soup.find('input', {'id': 'Department'}).get(
            'value') if 'Department' in page else ''),
        'email': (soup.find('input', {'id': 'EMail'}).get(
            'value') if 'EMail' in page else ''),
        'day_phone': (soup.find('input', {'id': 'Day_Phone'}).get(
            'value') if 'Day_Phone' in page else ''),
        'night_phone': (soup.find('input', {'id': 'Night_Phone'}).get(
            'value') if 'Night_Phone' in page else ''),
        'mobile': (soup.find('input', {'id': 'Mobile'}).get(
            'value') if 'Mobile' in page else ''),
        'fax': (soup.find('input', {'id': 'Fax'}).get(
            'value') if 'Fax' in page else ''),
        'street_address_1': (soup.find('input', {'id': 'Street_Address_1'}).get(
            'value') if 'Street_Address_1' in page else ''),
        'street_address_2': (soup.find('input', {'id': 'Street_Address_2'}).get(
            'value') if 'Street_Address_2' in page else ''),
        'street_address_3': (soup.find('input', {'id': 'Street_Address_3'}).get(
            'value') if 'Street_Address_3' in page else ''),
        'city_name': (soup.find('input', {'id': 'City_Name'}).get(
            'value') if 'City_Name' in page else ''),
        'province': (soup.find('input', {'id': 'Province'}).get(
            'value') if 'Province' in page else ''),
        'zip_code': (soup.find('input', {'id': 'Zip_Code'}).get(
            'value') if 'Zip_Code' in page else '')}
    return customer_data


def get_cc_data(page):
    """
    :param page: HTML page
    :type: unicode

    :return: customer_cc_data
    :rtype: dict
    """
    soup = BeautifulSoup(page)
    customer_cc_data = {
        'card_number': (soup.find('input', {'id': 'Acct_Num_CH'}).get('value') if 'Acct_Num_CH' in page else ''),
        'card_exp': (soup.find('input', {'id': 'Exp_CH'}).get('value') if 'Exp_CH' in page else ''),
        'card_name': (soup.find('input', {'id': 'Name_on_Card_VC'}).get('value') if 'Name_on_Card_VC' in page else ''),
        'card_adrress': (soup.find('input', {'id': 'Street_CH'}).get('value') if 'Street_CH' in page else ''),
        'card_zip': (soup.find('input', {'id': 'Zip_CH'}).get('value') if 'Zip_CH' in page else '')
    }
    return customer_cc_data


def enter_contract_list_page(s, redfin_url, contract_id=None, status=None, payment_preference=None):
    """
    :param s: Session object
    :type s: request.Session

    :param redfin_url: url for entering into the system
    :type redfin_url: str

    :param contract_id: Contract_ID for request
    :type contract_id: str

    :param status: Status for request
    :type status: str

    :param payment_preference: Payment_Preference_ID for request
    :type payment_preference: str

    :return s: Session object
    :return r: Response object
    """

    if not contract_id:
        contract_id = ''
    if not status:
        status = 'All'
    if not payment_preference:
        payment_preference = 'All'
    # enter to customer view page for taken tokens
    r = s.get('%srecurring/view_contracts.aspx' % redfin_url)
    payload = get_tokens(r.text)
    payload.pop('__VIEWSTATEGENERATOR')
    payload.update({'SearchButton': 'Find Contract(s)',
                    'Contract_ID': contract_id,
                    'FilterOperator': '>',
                    'NextBillDate': '>=',
                    'Next_Bill_DT': '',
                    'Payment_Preference_ID': payment_preference,
                    'ShowFilters': 'on',
                    'Status': status,
                    'Total_Amt': '0.00',
                    '__LASTFOCUS': '',
                    })
    r = s.post('%srecurring/view_contracts.aspx' % redfin_url, data=payload)
    return r, s


def enter_customer_list_page(s, redfin_url):
    """
    :param s: Session object
    :param redfin_url: url for entering into the system
    :return s: Session object
    :return r: Response object
    """
    # enter to customer view page for taken tokens
    r = s.get('%srecurring/view.aspx' % redfin_url)
    payload = get_tokens(r.text)
    payload.update({'SearchButton': 'Find Customer(s)',
                    'SearchBy': '',
                    'SearchValue': '',
                    'ShowFilters': 'on',
                    'StatusList': '1',
                    '__LASTFOCUS': ''})
    r = s.post('%srecurring/view.aspx' % redfin_url, data=payload)
    logger.debug('CUSTOMERSPAGE')
    return r, s


def deactivate_contract(s, redfin_url, contract_url):
    """
    :param s: Session object
    :type s: request.Session

    :param contract_url: url for entering into the system
    :type contract_url: str

    :return s: Session object
    :return r: Response object
    """
    r = s.get('%srecurring/%s' % (redfin_url, contract_url))
    page = r.text
    soup = BeautifulSoup(page)
    bill_amount = soup.find('input', {'id': 'Bill_Amt'}).get('value')
    payload = get_tokens(page)
    payload.pop('__VIEWSTATEGENERATOR')
    if soup.find('table', {'id': 'Email_Merchant'}):
        email_merchant = soup.find('table', {'id': 'Email_Merchant'}).find('input', {'checked': 'checked'}).get(
                'value') if 'Email_Merchant' in page else ''
    elif soup.find('span', {'id': 'Email_Merchant'}):
        email_merchant = soup.find('span', {'id': 'Email_Merchant'}).find('input', {'checked': 'checked'}).get(
                'value') if 'Email_Merchant' in page else ''
    else:
        email_merchant = ''
    if soup.find('table', {'id': 'Email_Merchant_At_Failure'}):
        email_merchant_at_failure = soup.find('table', {'id': 'Email_Merchant_At_Failure'}).find('input', {'checked': 'checked'}).get(
                'value') if 'Email_Merchant_At_Failure' in page else ''
    elif soup.find('span', {'id': 'Email_Merchant_At_Failure'}):
        email_merchant_at_failure = soup.find('span', {'id': 'Email_Merchant_At_Failure'}).find('input', {'checked': 'checked'}).get(
                'value') if 'Email_Merchant_At_Failure' in page else ''
    else:
        email_merchant_at_failure = ''
    contract_name = soup.find('input', {'id': 'Contract_Name'}).get('value') if 'Contract_Name' in page else ''
    if not contract_name:
        contract_name = ''
    po_num = soup.find('input', {'id': 'PO_Num'}).get('value') if 'PO_Num' in page else ''
    if not po_num:
        po_num = ''
    payload.update({
        'Bill_Amt': bill_amount,

        'Billing_Interval': soup.find('select', {'id': 'Billing_Interval'}).find('option', {'selected': 'selected'}).get(
                'value') if 'Billing_Interval' in page else '',

        'Contract_ID': soup.find('input', {'id': 'Contract_ID'}).get(
            'value') if 'Contract_ID' in page else '',
        'Contract_Name': contract_name,

        'Email_Customer_Receipt_Option': soup.find('select', {'id': 'Email_Customer_Receipt_Option'}).find('option', {'selected': 'selected'}).get(
                'value') if 'Email_Customer_Receipt_Option' in page else '',

        'Email_Merchant': email_merchant,
        'Email_Merchant_At_Failure': email_merchant_at_failure,
        'End_Dt': soup.find('input', {'id': 'End_Dt'}).get(
            'value') if 'End_Dt' in page else '',
        'Max_Failures_IN': soup.find('select', {'id': 'Max_Failures_IN'}).find('option', {'selected': 'selected'}).get(
                'value') if 'Max_Failures_IN' in page else '',
        'Next_Bill_DT': soup.find('input', {'id': 'Next_Bill_DT'}).get(
            'value') if 'Next_Bill_DT' in page else '',
        'PO_Num': po_num,
        'Start_Dt': soup.find('input', {'id': 'Start_Dt'}).get(
            'value') if 'Start_Dt' in page else '',
        'StatusList': '2',
        'Tax_Amt': soup.find('input', {'id': 'Tax_Amt'}).get(
            'value') if 'Tax_Amt' in page else '',
        'Tenders': soup.find('select', {'id': 'Tenders'}).find('option', {'selected': 'selected'}).get(
                'value') if 'Tenders' in page else '',
        'Total': soup.find('input', {'id': 'Total'}).get(
            'value') if 'Total' in page else '',
        'UpdateButton': 'Update Contract',
    })
    r = s.post('%srecurring/%s' % (redfin_url, contract_url), data=payload)
    msg = BeautifulSoup(r.text).find('span', {'id': 'Msg'}).text
    return bill_amount, msg
