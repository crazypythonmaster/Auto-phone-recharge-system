import logging
import traceback
from BeautifulSoup import BeautifulSoup
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
import decimal
from pytz import timezone
import mechanize

logger = logging.getLogger('ppars')


def login_pageplus(username, password):
    """
    This function for authorization on pageplus, it return dict with three fields:
    valid: boolean field,
    browser: object of mechanize.Browser(),
    error: string field, which has information about error of auth, if it has error.

    :param username: username from dialer site
    :type username: str

    :param password: password  from dialer site
    :type password: str

    :return: answer
    :rtype: dict
    """
    answer = {'valid': False,
              'browser': mechanize.Browser(),
              'error': ""}
    answer['browser'].set_handle_equiv(True)
    answer['browser'].set_handle_redirect(True)
    answer['browser'].set_handle_referer(True)
    answer['browser'].set_handle_robots(False)
    answer['browser'].set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    answer['browser'].addheaders = [
        ('User-agent',
         'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    try:
        response = answer['browser'].open('https://www.pagepluscellular.com/login')
    except Exception, e:
        answer['error'] = "Internal error PagePlus."
        return answer
    if response.code == 200:
        try:
            answer['browser'].select_form(nr=0)
            answer['browser'].form['username'] = username
            answer['browser'].form['password'] = password
            answer['browser'].submit()
        except Exception, e:
            answer['error'] = 'Can not login in PagePlus.'
            return answer
        if not answer['browser'].geturl() == 'https://dealer.pagepluscellular.com/my-profile/account-summary.aspx':
            answer['error'] = 'Invalid login or password.'
        else:
            answer['valid'] = True
    else:
        answer['error'] = 'Internal error PagePlus. Status code: %s' % response.code
    return answer


def mdn_status(phone_number, br):
    """
    :param phone_number: string
    :param br: mechanize.Browser()
    :return: answer
    :rtype: dict
    """
    answer = {
        'valid': False,
        'plan_str': '',
        'renewal_date': '',
        'error': '',
        'mdn_status': ''
    }
    try:
        br.follow_link(br.links(text='MDN/Number Status').next())
        br.select_form(nr=0)
        br.form['ctl00$ctl00$ctl00$ContentPlaceHolderDefault$mainContentArea$Item3$AccountStatus_5$txtPhone'] \
            = str(phone_number)
        br.submit()
    except Exception, e:
        answer['error'] = 'Can not get result from PagePlus.'
        return answer
    if br.response().code == 200:
        soup = BeautifulSoup(br.response().read())
        answer['valid'] = True
        if soup.find('span', id='ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_lbl_message',
                     text='Phone number is invalid or is not a Page Plus customer'):
            answer['valid'] = False
            answer['error'] = 'Phone number is invalid or is not a Page Plus customer.'
            return answer
        if soup.find('span', text='This account has been suspended due to failed plan renewal and insufficient balance.'
                                  ' Please replenish this account to have it reinstated to active status.'):
            answer['valid'] = False
            answer['error'] = "This account has been suspended due to failed plan renewal and insufficient balance." \
                              " Please replenish this account to have it reinstated to active status."
        if soup.find('span', id='ContentPlaceHolderDefault_mainContentArea'
                                '_Item3_AccountStatus_5_lblExpirationDate'):
            answer['mdn_status'] += "\nExpiration Date:%s" % \
                                    soup.find('span',
                                              id='ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_lblExpirationDate').text
        exp_date = scrape_expiring_date(soup)
        stacked_pins = scrape_stacked_pins(soup)
        if exp_date:
            answer['mdn_status'] += '\nPlan Exp. Date:%s' % exp_date.strftime("%m/%d/%Y")
            answer['renewal_date'] = exp_date + relativedelta(months=stacked_pins['count'])
        plan_str = scrape_plan_name(soup)
        if plan_str:
            answer['plan_str'] = plan_str
            answer['mdn_status'] += '\nRate Plan:%s' % plan_str
        balance = scrape_balance(soup)
        if balance:
            answer['mdn_status'] += "\n Balance:%s" % balance
        plan_details = scrape_plan_details(soup)
        if plan_details:
            answer['mdn_status'] += "\nPlan Balance Details:%s" % plan_details
        if stacked_pins['pins']:
            answer['mdn_status'] += "Stacked pins:%s\n" % stacked_pins['pins']
    else:
        answer['error'] = 'Internal error PagePlus. Status code: %s' % br.response().code
    return answer


def scrape_expiring_date(soup):
    """
    :param soup: object of BeautifulSoup
    :return: exp_date
    :rtype: datetime
    """
    try:
        expiring_date_string = soup.find("div",
                                         id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divDealerBundleDetails")
        expiring_date_string = expiring_date_string.contents[0].contents[0].contents[1].string.split(' ')[2][:-1]
        expiration_date = datetime.strptime(expiring_date_string, "%m/%d/%Y").date()
        return expiration_date
    except Exception, e:
        return None


def scrape_plan_name(soup):
    """
    :param soup: object of BeautifulSoup
    :return: plan_str
    :rtype: str
    """
    try:
        plan_str = \
            soup.find('span',
                      id='ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_lblRatePlan').contents[0]
        return plan_str
    except Exception, e:
        return ''


def scrape_balance(soup):
    """
    :param soup: object of BeautifulSoup
    :return: balance_str
    :rtype: str
    """
    try:
        balance_str = \
        soup.find('span', id='ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_lblBalance').contents[
            0].string[1:]
        return balance_str
    except Exception, e:
        return ''


def scrape_stacked_pins(soup):
    """
    Return dict with two fields:
    pins: str
    count: count of pins
    :param soup: object of BeautifulSoup
    :return: stacked_pins
    :rtype: dict
    """
    stacked_pins = {
        'pins': '',
        'count': 0
    }
    try:
        if soup.find("div",
                     id="ContentPlaceHolderDefault_mainContentArea"
                        "_Item3_AccountStatus_5_divResult"):
            for pin_block in soup.find("div",
                                       id="ContentPlaceHolderDefault_main"
                                          "ContentArea_Item3_AccountStatus_5"
                                          "_divStacked"
                                          "CardsDetails").findAll('div'):
                for pin in pin_block.findAll('div'):
                    if bool(re.match('[\d]{2}\*{8}[\d]{4}', pin.text)):
                        stacked_pin = pin.text
                        stacked_pins['count'] += 1
                        stacked_pins['pins'] += '%s; ' % stacked_pin
    except Exception, e:
        pass
    finally:
        return stacked_pins


def scrape_plan_details(soup):
    """
    :param soup: object of BeautifulSoup
    :return: plan_details_str
    :rtype: str
    """
    plan_details_str = ''
    try:
        plan_details = soup.find("div",
                                 id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divDealerBundleDetails")
        if plan_details:
            plan_balance_details = plan_details.contents
            Talk_n_Text = "%s %s" % (
                plan_balance_details[0].contents[0].contents[0].string,
                plan_balance_details[0].contents[0].contents[1].string)
            min_details = plan_balance_details[2].contents[0].string
            txt_details = plan_balance_details[2].contents[1].string
            data_details = plan_balance_details[2].contents[2].string
            plan_details_str = "\t%s\nmin:\t%s\ntxt:\t%s\ndata:\t%s" % \
                               (Talk_n_Text,
                                min_details,
                                txt_details,
                                data_details)
    except Exception, e:
        pass
    finally:
        return plan_details_str


def verify_pageplus(phone_number, br):
    """
    :param phone_number: string
    :param br: mechanize.Browser()
    :return: result
    :rtype: dict
    """
    from ppars.apps.core.models import Carrier, Plan
    carrier = Carrier.objects.filter(name__icontains='PAGE PLUS CELLULAR').get()
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
    answer = mdn_status(phone_number, br)
    if answer['valid']:
        if answer['plan_str']:
            plan = Plan.objects.filter(carrier=carrier, rate_plan__icontains=answer['plan_str'])
            if plan:
                result['plan'] = plan[0]
            else:
                result['valid_for_schedule'] = False
                result['error'] += "\nCan not find plan for %s." % answer['plan_str']
        else:
            result['error'] += '\nCan not get plan from PagePlus.'
        if answer['renewal_date']:
            result['renewal_date'] = answer['renewal_date']
        else:
            result['error'] += '\nCan not determine renewal date.'
            result['valid_for_schedule'] = False
        if carrier.default_time:
            result['schedule'] = carrier.default_time
        else:
            result['valid_for_schedule'] = False
            result['error'] = '\nCan not get default schedule time for carrier.'
        if answer['mdn_status']:
            result['mdn_status'] = answer['mdn_status']
    else:
        result['valid'] = False
        result['valid_for_schedule'] = False
        result['error'] = answer['error']
    return result


def page_plus_cellular_scrape(pin, carrier_admin, phone_number, plan_cost):
    today = datetime.now(timezone('US/Eastern')) + relativedelta(months=1)
    expirations_date = ['(Expiring {d.month}/{d.day}/{d.year})'.format(d=today),
                       '(Expiring {d.month}/{d.day}/{d.year})'.format(d=today - timedelta(1)),
                       '(Expiring {d.month}/{d.day}/{d.year})'.format(d=today + timedelta(1)),
                       '(Expiring {d.month}/{d.day}/{d.year})'.format(d=today - timedelta(2)),
                       '(Expiring {d.month}/{d.day}/{d.year})'.format(d=today + timedelta(2)),
                       ]

    auth_result = login_pageplus(carrier_admin.username, carrier_admin.password)
    if auth_result['valid']:
        br = auth_result['browser']
    else:
        raise Exception(auth_result['error'])
    details = scrape_more_information_page_plus(br, phone_number)

    br.follow_link(br.links(text='MDN/Number Status').next())
    br.select_form(nr=0)
    br.form['ctl00$ctl00$ctl00$ContentPlaceHolderDefault$mainContentArea$Item3$AccountStatus_5$txtPhone'] = str(phone_number)
    br.submit()

    soup = BeautifulSoup(br.response().read())
    logger.debug('Scrapping pp Info %s' % br.response().read())

    if soup.find("div", id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divResult"):
        stacked_pins = []
        for pin_blocks in soup.find("div", id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divStackedCardsDetails").findAll('div'):
            for pin_block in pin_blocks.findAll('div'):
                if bool(re.match('[\d]{2}\*{8}[\d]{4}', pin_block.text)):
                    stacked_pin = pin_block.text
                    stacked_pins.append(stacked_pin)
                    if stacked_pin == '%s********%s' % (pin[:2], pin[10:]):
                        return "PagePlus Recharge successful, stacked pin %s \n%s" % (stacked_pin, details)

        expiry_date = soup.find("div", id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divDealerBundleDetails").contents
        if expiry_date:
            expiry_date = expiry_date[0].contents[0].contents[1].strip()
            if expiry_date in expirations_date:
                return "PagePlus Recharge successful, %s \n%s" % (expiry_date, details)

        balance = soup.find("span", id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_lblBalance").string
        if decimal.Decimal(balance.replace('$', '')) >= plan_cost:
            return "PagePlus Recharge successful, balance %s\n%s" % (balance, details)

    raise Exception("PagePlus Recharge Failed, Result inconclusive %s" % details)


def scrape_more_information_page_plus(br, phone_number):
        details = ''
        br.follow_link(br.links(text='MDN/Number Status').next())
        br.select_form(nr=0)
        br.form['ctl00$ctl00$ctl00$ContentPlaceHolderDefault$mainContentArea$Item3$AccountStatus_5$txtPhone'] = str(phone_number)
        br.submit()
        logger.debug('DETAILS %s' % br.response().read())
        soup = BeautifulSoup(br.response().read())
        plan_balance_details = soup.find("div",
                                         id="ContentPlaceHolderDefault_mainContentArea_Item3_AccountStatus_5_divDealerBundleDetails")
        if plan_balance_details:
            try:
                plan_balance_details = plan_balance_details.contents
                Talk_n_Text = "%s %s" % (plan_balance_details[0].contents[0].contents[0].string,
                                         plan_balance_details[0].contents[0].contents[1].string)
                min_details = plan_balance_details[2].contents[0].string
                txt_details = plan_balance_details[2].contents[1].string
                data_details = plan_balance_details[2].contents[2].string
                details = "Plan Balance Details:" \
                           "\t%s\nmin:\t%s\ntxt:\t%s\ndata:\t%s" % (Talk_n_Text, min_details, txt_details, data_details)
            except Exception, e:
                logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        return details