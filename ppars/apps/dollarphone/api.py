import logging
import traceback
from suds.transport.https import WindowsHttpAuthenticated
from suds.xsd.doctor import Import, ImportDoctor
from suds.client import Client as WSClient
import time
from response_codes import dp_response_codes

logger = logging.getLogger('ppars')


def dollar_phone_api_authorization(username, password):
    """
    :param username: Dollar phone  API username
    :type username: str

    :param password: Dollar phone  API password
    :type password: str

    :return: WSClient
    :rtype : WSClient
    """
    ntlm = WindowsHttpAuthenticated(username='DPWEB-1\\%s' % username, password=password)
    imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
    imp = Import('http://www.w3.org/2001/XMLSchema')
    imp.filter.add('https://dollarphone.com/PMAPI/PinManager')
    doctor = ImportDoctor(imp)
    try:
        return WSClient("https://www.dollarphone.com/pmapi/PinManager.asmx?WSDL", transport=ntlm, doctor=doctor)
    except Exception, e:
        logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        raise Exception('Failed to initialize dollarphone api, please verify your credentials')


def dp_api_request(form_fields):
    """
    :param form_fields: dictionary with required fields
        form_fields = {
                'username': Dollar phone  API username
                'password': Dollar phone  API password
                'phone_number': phone number. Use only for Top_up operations
                'Amount': Dollar phone plan amount
                'OfferingId': Dollar phone plan API ID
                'ProviderId': every time use 0
                'transaction': transaction ID. Unique identical number for dp
        }
    :type form_fields: dict

    :return: dp transaction status, message, pin(only if it was PIN operation)
    :rtype: dict
    """
    response = {
        'status': 0,
        'pin': '',
        'adv_status': '',
        'receipt_id': ''
        }
    try:
        client = dollar_phone_api_authorization(form_fields['username'], form_fields['password'])
        req = client.factory.create('TopUpReqType')
        action = client.factory.create('TopUpAction')
        if form_fields['phone_number']:
            req.Action = action.AddFunds
            req.PhoneNumber = '1%s' % form_fields['phone_number']
        else:
            req.Action = action.PurchasePin
        req.OfferingId = form_fields['OfferingId']
        req.Amount = form_fields['Amount']
        req.ProviderId = form_fields['ProviderId']
        req.OrderId = form_fields['transaction']
        try:
            api_response = client.service.TopUpRequest(req)
            logger.debug('DP_API_PIN_BUY %s: %s' % (form_fields['transaction'], api_response))
        except Exception, e:
            logger.debug('DP_API_PIN_LAST %s: %s' % (form_fields['transaction'], client.last_sent()))
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            raise Exception('Failed to initialize dollarphone api, please verify your credentials')
        if api_response.responseCode < 0:
            raise Exception('%s' % dp_response_codes[api_response.responseCode])
        if api_response.TransId == 0:
            raise Exception('Dollarphone API retuned a 0 TransId, please contact Dollarphone to check your setup.')
        time.sleep(10)
        co = 0
        while True:
            co += 1
            response_status = client.service.TopupConfirm(api_response.TransId)
            logger.debug('DP_API_STATUS_LAST %s: %s %s' % (form_fields['transaction'], client.last_sent(), response_status))
            if response_status.Status == 'Success':
                response['status'] = 1
                response['receipt_id'] = api_response.TransId
                if form_fields['phone_number']:
                    response['adv_status'] = 'Phone topped up successfully. Dollar Phone ' \
                                 'transaction %s' % response['receipt_id']
                else:
                    response['pin'] = response_status.PIN
                    response['adv_status'] = 'Pin %s extracted from Dollar Phone ' \
                                 'transaction %s' % (response['pin'], response['receipt_id'])
                break
            elif response_status.Status == 'Failed':
                raise Exception('DollarPhone transaction failed (%s)  with message %s' % (
                    api_response.TransId, dp_response_codes[response_status.ErrorCode]))
            if co > 10:
                raise Exception('DollarPhone transaction no response (%s), '
                                'check it for more information' % response_status.TransId)
            time.sleep(4)
    except Exception, e:
        response['adv_status'] = "Failure :%s" % e
        response['status'] = 0
        logger.error("Exception for %s : %s. Trace: %s." % (form_fields['transaction'], e, traceback.format_exc(limit=10)))
    finally:
        return response
