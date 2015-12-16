from ppars.apps.core import dealer_page_plus, dealer_red_pocket, dealer_airvoice, dealer_h2o, dealer_pvc_approvedlink
import logging
import traceback

from ppars.apps.core.models import Log

logger = logging.getLogger('ppars')


def get_mdn_number(phone_number, company):
    from models import CarrierAdmin
    answer = {
        'valid': True,
        'valid_for_schedule': False,
        'carrier': '',
        'error': '',
        'mdn_status': '',
        'plan': '',
        'schedule': '',
        'renewal_date': ''
    }
    log_title = '[Verify carrier for %s]\n' % phone_number
    log_message = ''
    #PagePlus
    carrier_admin_page_plus = CarrierAdmin.objects.filter(
        company=company,
        carrier__name__icontains='PAGE PLUS CELLULAR').get()
    auth_pageplus = dealer_page_plus.login_pageplus(carrier_admin_page_plus.username, carrier_admin_page_plus.password)
    if auth_pageplus['valid']:
        result_pageplus = dealer_page_plus.verify_pageplus(phone_number, auth_pageplus['browser'])
        log_message += "[PagePlus: %s]" % create_log_message_for_verify_carrier(result_pageplus)
        if result_pageplus['valid']:
            answer = result_pageplus
            Log.objects.create(company=company, note="%s%s" % (log_title, log_message.replace('\n', ' ')))
            return answer
        else:
            answer['valid'] = False
            answer['error'] += '[PagePlus:%s]\n' % result_pageplus['error']
    else:
        answer['valid'] = False
        answer['error'] += "[PagePlus:%s]\n" % auth_pageplus['error']
        log_message += "\n[RedPocket: %s]" % auth_pageplus['error']
    #RedPocket
    carrier_admin_red_pocket = CarrierAdmin.objects.filter(company=company, carrier__name__icontains='RED POCKET').get()
    auth_redpocket = dealer_red_pocket.log_in_red_pocket(carrier_admin_red_pocket)
    if auth_redpocket['valid']:
        result_redpocket = dealer_red_pocket.verify_carrier(phone_number, auth_redpocket['session'])
        log_message += "\n[RedPocket: %s]" % create_log_message_for_verify_carrier(result_redpocket)
        if result_redpocket['valid']:
            answer = result_redpocket
            Log.objects.create(company=company, note="%s%s" % (log_title, log_message.replace('\n', ' ')))
            return answer
        else:
            answer['valid'] = False
            answer['error'] += '[RedPocket:%s]\n' % result_redpocket['error']
    else:
        answer['valid'] = False
        answer['error'] += "[RedPocket:%s]\n" % auth_redpocket['error']
        log_message += "\n[RedPocket: %s]" % auth_redpocket['error']
    #H2O
    carrier_admin_h2o = CarrierAdmin.objects.filter(company=company, carrier__name__icontains='H2O UNLIMITED').get()
    auth_h2o = dealer_h2o.login_h2o(carrier_admin_h2o)
    if auth_h2o['valid']:
        result_h2o = dealer_h2o.verify_carrier(phone_number, auth_h2o['session'])
        log_message += "\n[H2O: %s]" % create_log_message_for_verify_carrier(result_h2o)
        if result_h2o['valid']:
            answer = result_h2o
            Log.objects.create(company=company, note="%s%s" % (log_title, log_message.replace('\n', ' ')))
            return answer
        else:
            answer['valid'] = False
            answer['error'] += '[H2O:%s]\n' % result_h2o['error']
    else:
        answer['valid'] = False
        answer['error'] += "[H2O:%s]\n" % auth_h2o['error']
        log_message += "\n[H2O: %s]" % auth_h2o['error']
    #AirVoice
    result_airvoice = dealer_airvoice.verify_carrier(phone_number)
    log_message += "\n[Airvoice: %s]" % create_log_message_for_verify_carrier(result_airvoice)
    if result_airvoice['valid']:
        answer = result_airvoice
        Log.objects.create(company=company, note="%s%s" % (log_title, log_message.replace('\n', ' ')))
        return answer
    else:
        answer['valid'] = False
        answer['error'] += "[AirVoice:%s]\n" % result_airvoice['error']
    #ApprovedLink
    result_approvedlink = dealer_pvc_approvedlink.verify_carrier(phone_number)
    log_message += "\n[ApprovedLink: %s]" % create_log_message_for_verify_carrier(result_approvedlink)
    if result_approvedlink['valid']:
        answer = result_approvedlink
    else:
        answer['valid'] = False
        answer['error'] += "[ApprovedLink:%s]\n" % result_approvedlink['error']
    Log.objects.create(company=company, note="%s%s" % (log_title, log_message.replace('\n', ' ')))
    return answer


def get_status_of_pins(company, pins):
    from models import CarrierAdmin
    carrier_admin = CarrierAdmin.objects.filter(company=company,
                                                carrier__name__icontains='RED POCKET')
    result = {'failed_login': False,
              'result': []}
    try:
        answer = dealer_red_pocket.log_in_red_pocket(carrier_admin[0])
        if not answer['valid']:
            raise Exception(answer['error'])
    except Exception, e:
        result['failed_login'] = True
        logger.error("Exception: %s. Trace: %s."
                     % (e, traceback.format_exc(limit=10)))
        return result
    for pin in pins:
        status_pin = dealer_red_pocket.get_pin_status(pin, answer['session'])
        result['result'].append(status_pin)
    return result


def create_log_message_for_verify_carrier(answer_dict):
    """
    This function to transform answer_dict to str for user.
    :param answer_dict: dict
    :return: answer_str
    """
    answer_str = ''
    if answer_dict['valid']:
        answer_str = answer_dict['mdn_status']
    else:
        answer_str = answer_dict['error']
    return answer_str