from decimal import Decimal
import json
import logging
import traceback
from BeautifulSoup import BeautifulSoup
import datetime
from dateutil.relativedelta import relativedelta
import math
import pytz
import re
import requests

logger = logging.getLogger('ppars')


def log_in_red_pocket(carrier_admin):
    """
    :param carrier_admin: ppars.apps.core.models.CarrierAdmin
    :returns: answer
    :rtype: dict
    """
    answer = {'valid': False,
              'session': requests.Session(),
              'error': ""}
    response_session = answer['session'].post("https://my.redpocketmobile.com/index/checkLogin",
                                              data={'username': carrier_admin.username,
                                                    'password': carrier_admin.password})
    if response_session.status_code == 200:
        response_json = json.loads(response_session.text)
        if not response_json['return_code']:
            answer['valid'] = True
        else:
            answer['valid'] = False
            answer['error'] = response_json['return_text']
    else:
        answer['valid'] = False
        answer['error'] = "Internal error on RedPocket. Status code: %s." % response_session.status_code
    return answer


def mdn_status(phone_number, s):
    """
    :param phone_number: string
    :param s: requests.Session
    :return: status_result
    :rtype: dict
    """
    status_result = {'status_find': True,
                     'account_status': True,
                     'exp_date': '',
                     'plan_cost': '',
                     'balance': '',
                     'renewal_date': '',
                     'schedule': '',
                     'provider': '',
                     'mdn_status': '',
                     'url': '',
                     'error': ''
                     }
    try:
        r = s.post('https://my.redpocketmobile.com/sdealer/search/',
                   data={'search': phone_number})
        account_id = r.url.split("/").pop()
        soup = BeautifulSoup(r.text)
        if soup.find(text="Sorry, No Results Found."):
            status_result['status_find'] = False
            status_result['error'] = "Can not find the phone number."
            return status_result
        if soup.find(text=" Account's SIM ICCID Number"):
            status_result['status_find'] = False
            status_result['error'] = "This Account was not activated with a SIM ICCID that matches your Dealerlogin. "
            return status_result
        status_result['url'] = r.url
        status_result['provider'] = soup.find('div', id='gi').find('table').contents[3].contents[5].contents[0]
        if 'AT&' in status_result['provider']:
            status_result = at_and_t_provider(soup, status_result, phone_number, s)
        elif 'Sprint' in status_result['provider']:
            status_result = sprint_provider(soup, status_result, account_id, s)
        elif 'Account Information' in status_result['provider']:
            status_result = verizon_provider(soup, status_result, account_id, s)
    except Exception, e:
        status_result['status_find'] = False
    finally:
        return status_result


def at_and_t_provider(soup, status_result, phone_number, s):
    """
    :param soup: object of BeautifulSoup
    :param status_result: dict
    :param account_id: string
    :param s: requests.Session()
    :return: status_result
    :rtype: dict
    """
    account_status = \
        soup.find('div', id='gi').find('table').contents[
            5].contents[1].contents[1].contents[3].contents[1].contents[3].contents[0]
    t = s.get("https://my.redpocketmobile.com/sdealer/accounts/ajax-update-ericsson/account_number/%s" % phone_number)
    response_json = json.loads(t.text)
    status_result['mdn_status'] = account_details_at_and_t(soup, response_json)
    if 'Active' in account_status:
        try:
            last_updated = datetime.datetime.strptime(response_json['date_modifed'], "%Y-%m-%d %H:%M:%S").date()
            today = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
            status_result['account_status'] = last_updated == today
        except Exception:
            pass
        try:
            plan_cost = soup.find('div', id='gi').find('table').contents[5].contents[1].contents[1].contents[
                3].contents[5].contents[3].contents[0].contents[0]
            status_result['plan_cost'] = plan_cost[plan_cost.index('$') + 1:]
        except Exception:
            pass
        if soup.find('span', id='ericsson_rateplan'):
            status_result['plan_name'] = soup.find('span', id='ericsson_rateplan').text
        if soup.find('span', id='ericsson_airtimeexpiration'):
            exp_date = datetime.datetime.strptime(soup.find('span', id='ericsson_airtimeexpiration').text,
                                                  "%B %d, %Y").date()
            status_result['exp_date'] = status_result['renewal_date'] = exp_date
        status_result['provider'] = 'AT&T'
    return status_result


def account_details_at_and_t(soup, response_json):
    """
    :param soup: object of BeautifulSoup
    :param response_json: json
    :return: result
    :rtype: str
    """
    result = ''
    try:
        result += 'Last Updated: %s\n' % response_json['date_modifed']
        tables = soup.find('div', id='gi').find('table').find('table')
        acount_details = tables.contents[:7]
        for detail in acount_details:
            if not u'\n' == detail:
                for det in detail:
                    if not u'\n' == det:
                        result += '%s' % det
                result += '\n'
        if soup.find('span', id='ericsson_balance'):
            result += 'Balance: %s\n' % \
                      soup.find('span', id='ericsson_balance').text
        if soup.find('span', id='ericsson_voice'):
            result += 'Voice: %s\n' % response_json['voice']
        if soup.find('span', id='ericsson_message'):
            result += 'Message: %s\n' % response_json['message']
        if soup.find('span', id='ericsson_rateplan'):
            result += 'Rate Plan: %s\n' % \
                      soup.find('span', id='ericsson_rateplan').text
        if soup.find('span', id='ericsson_activationdate'):
            result += 'Activation Date: %s\n' % \
                      soup.find('span', id='ericsson_activationdate').text
        if soup.find('span', id='ericsson_airtimeexpiration'):
            result += 'Expiration Date: %s\n' % \
                      soup.find('span', id='ericsson_airtimeexpiration').text

    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e,
                                                    traceback.format_exc(limit=10)))
    finally:
        r = re.compile(r'<.*?>')
        result = r.sub('', result)
        return result


def sprint_provider(soup, status_result, account_id, s):
    """
    :param soup: BeautifulSoup
    :param status_result: dict
    :param account_id: string
    :param s: requests.Session()
    :return: status_result
    :rtype: dict
    """
    t = s.post('https://my.redpocketmobile.com/sdealer/accounts/ajax-update-sprint/id/%s' % account_id)
    response_json = json.loads(t.text)
    status_result['mdn_status'] = account_details_sprint(soup, response_json)
    if 'Active' in response_json['AccountStatus']:
        exp_date = datetime.datetime.strptime(response_json['DataExpiry'], "%B %d, %Y").date()
        rate_plan = \
            soup.find('div', id='gi').find('table').contents[
                5].contents[
                1].contents[1].contents[3].contents[5].contents[
                3].contents[0].contents[0]
        status_result['plan_cost'] = rate_plan[rate_plan.index('$') + 1:]
        status_result['provider'] = 'Sprint'
        status_result['renewal_date'] = status_result['exp_date'] = exp_date
        status_result['plan_name'] = rate_plan
    else:
        status_result['account_status'] = False
        status_result['mdn_status'] = '%s\n%s' % ("Acount isn't active. \n",
                                                  status_result['mdn_status'])
    return status_result


def account_details_sprint(soup, response_json):
    """
    :param soup: BeautifulSoup
    :param response_json: json
    :return: result
    :rtype: str
    """
    result = ''
    try:
        tables = soup.find('div', id='gi').find('table').find('table')
        acount_details = tables.contents[:9]
        for detail in acount_details:
            if not u'\n' == detail:
                for det in detail:
                    if not u'\n' == det:
                        result += '%s' % det
                result += '\n'
        result += 'Model name:%s\n' % response_json['device_model_name']
        result += 'Model number:%s\n' % response_json['device_model_number']
        result += 'Expiration Date :%s\n' % response_json['ExpirationDate']
        result += 'Account Balance:%s\n' % response_json["AccountBalance"]
        result += 'SMS :%s\n' % response_json['SMS']
        result += 'Data :%s\n' % response_json['Data']
        result += 'Data Expiry Date:%s\n' % response_json['DataExpiry']
        result += 'Activation Date:	%s\n' % response_json['ActivationDate']
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
    finally:
        p = re.compile(r'<.*?>')
        result = p.sub('', result)
        return result


def verizon_provider(soup, status_result, account_id, s):
    """
    :param soup: BeautifulSoup
    :param status_result: dict
    :param account_id: str
    :param s: requests.Session()
    :return: status_result
    :rtype: dict
    """
    ajax_update_verizon = s.post(
        'https://my.redpocketmobile.com/sdealer/accounts/ajax-update-verizon/id/%s' % account_id)
    response_json = json.loads(ajax_update_verizon.text)
    if 'ACTIVE' == response_json['status']:
        last_updated = datetime.datetime.strptime(response_json['lastupdated'], "%Y-%m-%d %H:%M:%S").date()
        today = datetime.datetime.now(pytz.timezone('US/Eastern')).date()
        status_result['account_status'] = last_updated == today
        exp_date = 'N/a'
        renewal_date = ''
        if 'TRUE' in response_json['has_buckets'] and not response_json['Bucket'] == u'[]':
            response_json['Bucket'] = buckets_str_to_json(response_json['Bucket'])
            renewal_date = exp_date = datetime.datetime.strptime(response_json['Bucket']['1']['expTime'], "%B %d, %Y").date()
            if response_json['Bucket']['1']['bucketTypeID'] in "500":
                exp_date = datetime.datetime.strptime(response_json['Bucket']['1']['expTime'], "%B %d, %Y").date()
                renewal_date = exp_date + relativedelta(days=1)
                status_result['schedule'] = "12:01AM"
        status_result['plan_name'] = response_json['retailplan']
        try:
            status_result['plan_cost'] = Decimal(response_json['retailplan'].split(' ')[0][1:])
        except Exception:
            pass
        status_result['balance'] = response_json['balance']
        if renewal_date and response_json['balance'] and status_result['plan_cost'] and \
                Decimal(response_json['balance']):
            status_result['renewal_date'] = \
                renewal_date + relativedelta(
                    months=math.trunc(Decimal(response_json['balance']) /
                                      Decimal(status_result['plan_cost'])))
        elif renewal_date:
            status_result['renewal_date'] = renewal_date
        status_result['exp_date'] = exp_date
        status_result['mdn_status'] = account_details_verizon(soup, response_json)
    else:
        if response_json['has_buckets']:
            response_json['Bucket'] = buckets_str_to_json(response_json['Bucket'])
        status_result['mdn_status'] = account_details_verizon(soup, response_json)
        status_result['account_status'] = False
    status_result['provider'] = 'Verizon'
    if not status_result['account_status']:
        status_result['mdn_status'] = '%s\n%s' % ("Acount isn't active.", status_result['mdn_status'])
    return status_result


def buckets_str_to_json(buckets_str):
    """
    :param buckets_str: string
    :return: buckets_json
    :rtype: json
    """
    buckets_str = buckets_str.replace(u'[', u'{').replace(u']', u'}').replace(u'{{', u'{"1": {')
    bucket_count = 1
    while buckets_str.find(u',{') != -1:
        bucket_count += 1
        buckets_str = buckets_str.replace(u',{', u', "%s":{' % bucket_count, 1)
    buckets_json = json.loads(buckets_str)
    return buckets_json


def account_details_verizon(soup, response_json):
    """
    :param soup: BeautifulSoup
    :param response_json: json
    :return: result
    :rtype: str
    """
    result = ''
    try:
        result += 'Last Updated: %s\n' % response_json['lastupdated']
        tables = soup.find('div', id='gi').find('table')
        acount_details = tables.find('table').contents
        acount_details = acount_details[0:6]
        for detail in acount_details:
            if not u'\n' == detail:
                for det in detail:
                    if not u'\n' == det:
                        result += '%s' % det
                result += '\n'
        p = re.compile(r'<.*?>')
        result = p.sub('', result)
        result += 'Balance: %s\n' % response_json['balance']
        result += 'Expiration Date: %s\n' % response_json['expiration']
        if 'TRUE' in response_json['has_buckets'] and not response_json['Bucket'] == u'[]':
            if response_json['Bucket']['1']['bucketTypeID'] in "100":
                result += '1st Bucket Expiration:%s\n' % response_json['Bucket']['1']['expTime']
                result += '1st Voice Balance:%s\n' % response_json['Bucket']['1']['bucketValue']
            else:
                result += '2nd Bucket Expiration:%s\n' % response_json['Bucket']['1']['expTime']
                result += '2nd Voice Balance:%s\n' % response_json['Bucket']['1']['bucketValue']
            if response_json['Bucket']['2']['bucketTypeID'] in "350":
                result += '1st SMS/MMS Balance:%s\n' % response_json['Bucket']['2']['bucketValue']
            else:
                result += '2nd SMS/MMS Balance:%s\n' % response_json['Bucket']['2']['bucketValue']
            if response_json['Bucket']['3']['bucketTypeID'] in "200":
                result += '1st Data Balance:%s\n' % response_json['Bucket']['3']['bucketValue']
            else:
                result += '2nd Data Balance:%s\n' % response_json['Bucket']['3']['bucketValue']
        result += 'Device ID:%s\n' % response_json['deviceid']
        result += 'MIN:%s\n' % response_json['minvalue']
        result += 'Activation Date:%s\n' % response_json['activationdate']
        result += 'Equipment Model: %s\n' % response_json['equipmentmodel']
        result += 'Equipment Make: %s\n' % response_json['equipmentmake']
        result += 'Equipment Mode: %s\n' % response_json['equipmentmode']
    except Exception, e:
        pass
    finally:
        return result


def get_pin_status(pin, s):
    result = {
        'pin': pin,
        'status': True,
        'invalid_login': False,
        'status_pin': '',
        'details': '',
        'url': '',
    }
    r = s.post('https://my.redpocketmobile.com/sdealer/search/',
               data={'search': pin})
    result['url'] = r.url
    try:
        soup = BeautifulSoup(r.text)
        if soup.find('input', id='username'):
            result['invalid_login'] = True
        result['status_pin'] = \
        soup.findAll('div', id='content_wrapper')[0].contents[4].contents[3].contents[3].contents[3].contents[
            0].contents[0]
        status_invalid = ['Used', 'Removed', 'Processing', 'Expired']
        if result['status_pin'] in status_invalid:
            content_wrapper = \
                soup.findAll('div', id='content_wrapper')[0].contents[
                    10].contents[
                    3].contents[1]
            for detail in content_wrapper:
                if not u'\n' == detail:
                    for det in detail:
                        if not u'&nbsp;' == det:
                            result['details'] += '%s ' % det
            p = re.compile(r'<.*?>')
            result['details'] = ' '.join(p.sub('', result['details']).split())
            if 'Order' in result['details']:
                result['details'] = ''
                content_wrapper = \
                    soup.findAll('div', id='content_wrapper')[0].contents[
                        12]
                for detail in content_wrapper:
                    for det in detail:
                        if not det == u'&nbsp;':
                            result['details'] += '%s ' % det
                p = re.compile(r'<.*?>')
                result['details'] = ' '.join(
                    p.sub('', result['details']).split())
        else:
            result['status'] = False
    except Exception, e:
        result['status'] = False
        logger.error("Exception: %s. Trace: %s."
                     % (e, traceback.format_exc(limit=10)))
    finally:
        return result


def verify_carrier(phone_number, s):
    """
    :param phone_number: string
    :param s: requests.Session()
    :return: result
    :rtype: dict
    """
    from ppars.apps.core.models import AutoRefill, Carrier, Plan
    carrier = Carrier.objects.filter(name__icontains='RED POCKET').get()
    result = {
        'valid': False,
        'valid_for_schedule': False,
        'plan': '',
        'carrier': carrier,
        'renewal_date': '',
        'schedule': '',
        'mdn_status': '',
        'error': '',
        'url': ''
    }
    answer = mdn_status(phone_number, s)
    if answer['status_find']:
        result['url'] = answer['url']
        result['valid'] = True
        result['mdn_status'] = answer['mdn_status']
        if answer['renewal_date']:
            result['renewal_date'] = answer['renewal_date']
        else:
            result['error'] += '\nCan not determine renewal date.'
        if answer['schedule']:
            result['schedule'] = AutoRefill.AFTER_MID_NIGHT
        else:
            result['schedule'] = carrier.default_time
        if answer['plan_cost'] and answer['provider']:
            plan = Plan.objects.filter(carrier=carrier,
                                       plan_cost=answer['plan_cost'],
                                       plan_name__icontains=answer['provider'])
            if plan:
                result['plan'] = plan[0]
            elif answer['plan_cost'] == '24.99' and answer['provider'] == 'AT&T':
                plan = Plan.objects.filter(carrier=carrier,
                                           plan_cost=answer['plan_cost'],
                                           plan_name__icontains='Universal Monthly')
                if plan:
                    result['plan'] = plan[0]
        if not result['plan']:
            result['error'] = "\nCan not find plan for %s, %s." % (answer['provider'],
                                                                    answer['plan_cost'])
        if result['plan'] and result['renewal_date'] and result['schedule'] and answer['account_status']:
            result['valid_for_schedule'] = True
    else:
        result['error'] = answer['error']
    return result
