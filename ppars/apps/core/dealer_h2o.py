import logging
import traceback
import datetime
import requests

logger = logging.getLogger('ppars')


def login_h2o(carrier_admin):
    """
    :param carrier_admin: ppars.apps.core.models.CarrierAdmin
    :returns: answer
    :rtype: dict
    """
    answer = {'valid': False,
              'session': requests.Session(),
              'error': ""}
    payload = {
        'dc': carrier_admin.username,
        'dp': carrier_admin.password
    }
    response_session = answer['session'].post('https://www.h2odealer.com/mainCtrl.php?page=login',
                                              data=payload)
    if response_session.status_code == 200:
        if not response_session.url == 'https://www.h2odealer.com/mainCtrl.php?page=forgotPass':
            answer['valid'] = True
        else:
            answer['valid'] = False
            answer['error'] = 'Invalid login or password.'
    else:
        answer['valid'] = False
        answer['error'] = "Internal error on H2o. Status code: %s." % response_session.status_code
    return answer


def mdn_status(phone_number, s):
    """
    :param phone_number:
    :param s: requests.Session
    :return: status_result
    :rtype: dict
    """
    status_result = {'status': '',
                     'error': '',
                     'plan_name': '',
                     'expiration': '',
                     'available': '',
                     'available_balance': '',
                     'data_balance': '',
                     'card': '',
                     'card_balance': '',
                     'mdn_status': ''
                     }
    try:
        r = s.get('https://www.h2odealer.com/mainCtrl.php?page=get_balance&min=%s&service_type=GSM' % phone_number)
        if not r.status_code == 200:
            status_result['error'] = "Internal error on H2o. Status code: %s." % r.status_code
            raise Exception(status_result['error'])
        page = r.text
        status = int(page.split('var ret_code = \'')[1].split('\';')[0])
        status_result['status'] = status
        if status >= 0:
            status_result['status'] = True
            if 'var plan = \'' in page:
                status_result['plan_name'] = '%s' % page.split('var plan = \'')[1].split('\';')[0]
            if 'var exp = \'' in page:
                status_result['expiration'] = '%s' % page.split('var exp = \'')[1].split('\';')[0]
            if 'var ild_avail = \'' in page:
                status_result['available'] = '%s' % page.split('var ild_avail = \'')[1].split('\';')[0]
            if 'var ild_bal = \'' in page:
                status_result['available_balance'] = '%s' % page.split('var ild_bal = \'')[1].split('\';')[0]
            if 'var data_bal = \'' in page:
                status_result['data_balance'] = '%s' % page.split('var data_bal = \'')[1].split('\';')[0]
            if 'fcard_balance = \'' in page:
                status_result['card'] = '%s' % page.split('fcard_balance = \'')[1].split('\';')[0]
            if 'var balance = \'' in page:
                status_result['card_balance'] = '%s' % page.split('var balance = \'')[1].split('\';')[0]
            status_result['mdn_status'] = 'Plan: %s\n' \
                               'Expiration: %s\n' \
                               'Available: %s\n' \
                               'Available Balance:%s\n' \
                               'Data Balance:%s\n' \
                               'Card:%s\n' \
                               'Card Balance:%s\n' % (
                                   status_result['plan_name'],
                                   status_result['expiration'],
                                   status_result['available'],
                                   status_result['available_balance'],
                                   status_result['data_balance'],
                                   status_result['card'],
                                   status_result['card_balance']
                               )
        else:
            status_result['status'] = False
            if 'var err_note =' in page:
                status_result['error'] = page.split('var err_note = \'')[1].split('\';')[0]
            else:
                status_result['error'] = "Can not find the phone number."
    except Exception, e:
        status_result['status'] = False
    finally:
        return status_result


def verify_carrier(phone_number, s):
    """
    This function for verification data for number of h2o.
    It returns dict with seven fields:
    valid: it is True if number from this and scraper hasn't error
    valid_for_schedule: it is True if answer has all info for creating schedule refill
    plan: object ppars.ppars.core.models.Plan
    schedule: const str for carrier
    renewal_date: it is object of datetime, for schedule refill
    mdn_status: str, it is all info of number telephone
    error: str, it has info about error if it has
    :param phone_number: str
    :param s: requests.Session
    :return: result
    :rtype: dict
    """
    from ppars.apps.core.models import Carrier, Plan
    carrier = Carrier.objects.filter(name__icontains='H2O UNLIMITED').get()
    result = {
        'valid': True,
        'valid_for_schedule': True,
        'plan': '',
        'carrier': carrier,
        'schedule': '',
        'renewal_date': '',
        'mdn_status': '',
        'error': ''
    }
    answer = mdn_status(phone_number, s)
    if answer['status']:
        result['mdn_status'] = answer['mdn_status']
        if answer['expiration'] and not answer['expiration'] == 'N/A':
            result['renewal_date'] = datetime.datetime.strptime(answer['expiration'], "%m/%d/%Y").date()
        else:
            result['valid_for_schedule'] = False
            result['error'] += '\nCan not get renewal date.'
        if answer['plan_name'] and not answer['plan_name'] == 'N/A':
            plan = Plan.objects.filter(carrier=carrier,
                                       rate_plan=answer['plan_name'])
            if plan:
                result['plan'] = plan[0]
            else:
                result['valid_for_schedule'] = False
                result['error'] += '\nCan not determine plan for %s.' % answer['plan_name']
        else:
            result['valid_for_schedule'] = False
            result['error'] += '\nCan not get plan.'
        if carrier.default_time:
            result['schedule'] = carrier.default_time
        else:
            result['valid_for_schedule'] = False
            result['error'] += '\nCan not get default schedule time.'
        if not result['plan'] and not result['renewal_date']:
            result['valid'] = False
            result['error'] = 'Can not find the number!'
    else:
        result['valid'] = False
        result['valid_for_schedule'] = False
        result['error'] = answer['error']
    return result
