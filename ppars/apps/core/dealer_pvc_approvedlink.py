import datetime
from dateutil.relativedelta import relativedelta
import pytz
import requests


def verify_carrier(phone_number, login=None, secret_code=None):
    """
    :param phone_number: str
    :param login: str it is login from pvc.approvedlink
    :param secret_code: str it is password from pvc.approvedlink
    :return: answer
    :rtype: dict
    """
    from ppars.apps.core.models import Carrier, Plan
    if not (login and secret_code):
        login = 'ezramizrahi'
        secret_code = '373706'
    answer = {
        'valid': False,
        'valid_for_schedule': True,
        'plan': '',
        'schedule': '',
        'renewal_date': '',
        'mdn_status': '',
        'error': '',
        'carrier': ''
    }
    session = requests.Session()
    answer_session = session.get(
        'http://75.99.53.250/CVWebService/PhoneHandler.aspx?method=checkbalance&phonenumber=%s&secretcode=%s6&login=%s&t=%s' %
        (
            phone_number,
            secret_code,
            login,
            "1446652889579"
        ))
    if answer_session.status_code == 200:
        if not 'CANCHECK_STATUS=eCantCheck' in answer_session.text:
            answer['mdn_status'] = answer_session.text.replace(',', '\n')
            answer_text = answer_session.text.split(',')
            answer_dict = {}
            for status in answer_text:
                answer_dict[status.split('=')[0]] = status.split('=')[1]
            answer['valid'] = True
            if 'DUE_DATE' in answer_session.text:
                if answer_dict['DUE_DATE'] == '0':
                    answer['renewal_date'] = datetime.datetime.now(pytz.timezone('US/Eastern')).date() + \
                                             relativedelta(days=2)
                elif answer_dict['DUE_DATE'] == '1':
                    answer['renewal_date'] = datetime.datetime.now(pytz.timezone('US/Eastern')).date() + \
                                             relativedelta(days=3)
                else:
                    try:
                        answer['renewal_date'] = datetime.datetime.strptime(answer_dict['DUE_DATE'],
                                                                            "%m/%d/%Y").date() + \
                                                 relativedelta(days=1)
                    except Exception, e:
                        answer['valid_for_schedule'] = False
                        answer['error'] = 'Can not determine renewal date.'
                if answer['renewal_date']:
                    answer['mdn_status'] += "\nRenewal Date:%s" % answer['renewal_date'].strftime("%m/%d/%Y")
            else:
                answer['valid_for_schedule'] = False
                answer['error'] = 'Can not determine renewal date.'
            answer['carrier'] = Carrier.objects.filter(name__icontains='Approved Link').get()
            if 'PLAN' in answer_session.text:
                plan = Plan.objects.filter(carrier=answer['carrier'], rate_plan=answer_dict['PLAN'])
                if plan:
                    answer['plan'] = plan[0]
                else:
                    answer['valid_for_schedule'] = False
                    answer['error'] += "\nCan not find plan for %s." % answer_dict['PLAN']
            else:
                answer['valid_for_schedule'] = False
                answer['error'] += '\nCan not get plan from approvedlink.'
            answer['schedule'] = '1AM'
        else:
            answer['valid_for_schedule'] = False
            answer['error'] = 'Can not find the number!'
    else:
        answer['valid_for_schedule'] = False
        answer['error'] = 'Internal error on ApprovedLink. Status code: %s' % answer_session.status_code
    return answer
