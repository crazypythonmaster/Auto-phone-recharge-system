import cookielib
import json
import logging
import re
import tempfile
import traceback
import time
import urllib
from BeautifulSoup import BeautifulSoup
from django.core.cache import cache
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
import mechanize
import requests
from twilio.rest import TwilioRestClient
from deathbycaptcha.deathbycaptcha import SocketClient
from ppars.apps.core.company_notifications import \
    send_deathbycaptcha_low_balance, send_deathbycaptcha_report
from ppars.apps.core.dealer_h2o import login_h2o, mdn_status
from ppars.apps.core import dealer_page_plus
from ppars.apps.core.dealer_page_plus import login_pageplus
from ppars.apps.core.models import Transaction, CarrierAdmin, \
    CaptchaLogs, CommandLog, CompanyProfile, Plan, Customer, ERROR, SUCCESS
from ppars.apps.core.send_notifications import check_on_invalid_incomn_voucher
from ppars.apps.dollarphone import api, site

logger = logging.getLogger('ppars')


class RechargePhone:
    def __init__(self, id):
        self.transaction = Transaction.objects.get(id=id)
        self.company = self.transaction.company
        self.super_company = CompanyProfile.objects.get(superuser_profile=True)
        self.customer = self.transaction.customer
        self.carrier = self.transaction.autorefill.plan.carrier
        self.phone_number = self.transaction.autorefill.phone_number
        self.norm_pin = self.transaction.pin.replace('-', '').strip()
        self.step = 'recharge phone'
        self.transaction.current_step = self.step.replace(' ', '_')

    def main(self):
        try:
            if self.transaction.autorefill.plan.plan_type == Plan.DOMESTIC_TOPUP:
                if self.customer.charge_getaway == Customer.DOLLARPHONE:
                    from ppars.apps.charge.models import TransactionCharge
                    for transaction_charges in TransactionCharge.objects.filter(transaction=self.transaction):
                        if not transaction_charges.charge.atransaction:
                            continue
                        self.transaction.add_transaction_step(
                            self.step,
                            'topup',
                            SUCCESS,
                            'Phone was refilled, details are at <a target="blank"'
                            ' href="https://www.dollarphonepinless.com/ppm_orders/%s/receipt">receipt</a>.' %
                            transaction_charges.charge.atransaction)
                    return self.transaction
                self.topup()
            else:
                # if plan have type Get Pin - we start manual refill
                # search Dealer Site (with authorization data for Carrier site)
                if self.carrier.admin_site:
                    carrier_admin = CarrierAdmin.objects.filter(company=self.company, carrier=self.carrier).first()
                    if carrier_admin:
                        self.carrieradmin = carrier_admin
                    else:
                        raise Exception('Dealer Site user details not added for '
                                        'carrier %s, please add it '
                                        '<a href="%s">here<a>.' %
                                        (self.carrier, reverse('carrier_admin_create')))
                self.transaction.add_transaction_step(self.step, 'topup', SUCCESS,
                                                      "Call the carrier's recharge function")
                getattr(self, slugify(self.carrier).replace('-', '_'))()
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            self.transaction.add_transaction_step(self.step, 'topup', ERROR, '%s' % e)
            raise Exception(e)
        finally:
            self.transaction.save()
        return self.transaction

    def topup(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, 'topup', SUCCESS, u'Test Mode on')
            return False

        plan = self.transaction.autorefill.plan
        form_fields = {
            'username': self.company.dollar_user,
            'password': self.company.dollar_pass,
            'phone_number': self.transaction.autorefill.phone_number,
            'Amount': plan.plan_cost,
            'company': self.company,
            'transaction': '%s' % self.transaction.id
        }
        if self.company.dollar_type == 'A':
            self.transaction.add_transaction_step(self.step, 'api', SUCCESS, 'Initializing the dollarphone API client')
            if not plan.api_id:
                raise Exception(
                    'API Id for this plan has not been updated, please request the admin to update the plan with the API ID')
            form_fields['OfferingId'] = plan.api_id
            form_fields['ProviderId'] = 0
            response = api.dp_api_request(form_fields)

        else:
            self.transaction.add_transaction_step(self.step, 'site', SUCCESS,
                                                  'Initializing the dollarphone Site client')
            form_fields['Carrier'] = plan.carrier.name
            form_fields['Plan'] = plan.plan_name
            form_fields['Amount'] = '$%s' % plan.plan_cost
            response = site.purchase_top_up_cash(form_fields)
        logger.debug('DP reciept %s %s' % (self.transaction.id, response['receipt_id']))
        if not response['status']:
            raise Exception(response['adv_status'])
        self.transaction.add_transaction_step(self.step, 'topup', SUCCESS, u'%s' % response['adv_status'])

    def page_plus_cellular(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'Test Mode on')
            return False
        try:
            if self.transaction.retry_count and self.check_package_details():
                return
            # Make refill on PagePlus
            auth_pageplus = login_pageplus(self.carrieradmin.username, self.carrieradmin.password)
            if not auth_pageplus['valid']:
                raise Exception(auth_pageplus['error'])
            br = auth_pageplus['browser']
            if self.company.pageplus_refillmethod == CompanyProfile.CAPTCHA:
                self.scrape_page_plus_with_deathbycaptcha(br)
                self.check_package_details()
            else:
                self.page_plus_voice_refill()
        except Exception, e:
            if self.check_package_details():
                return
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            raise Exception(u'%s' % e)

    def page_plus_voice_refill(self):
        self.twilio_top_up("8773596695", "ww1ww%swwwwwwwwwwwwwwwwwwwwwwww1ww1ww1wwwwwwwwwwwwwwwwwwwwwwww%s" % (
        self.transaction.autorefill.phone_number, self.transaction.pin.replace('-', '')))
        raise Exception('PagePlus Recharge Failed, Result inconclusive')

    def check_package_details(self):
        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Check package details')
        try:
            result = getattr(dealer_page_plus, slugify('%s_scrape' % self.carrier).replace('-', '_'))(self.norm_pin,
                                                                                                      self.carrieradmin,
                                                                                                      self.phone_number,
                                                                                                      self.transaction.autorefill.plan.plan_cost)
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'%s' % result)
            return True
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            self.transaction.add_transaction_step(self.step, self.carrier, ERROR, '%s' % e)

    def check_red_pocket_package_details(self):
        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Check package details')
        try:
            result = self.red_pocket_scrape()
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'%s' % result)
            return True
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            self.transaction.add_transaction_step(self.step, self.carrier, ERROR, '%s' % e)

    def red_pocket_scrape(self):
        s, base_url = self.login_site_request('https://my.redpocketmobile.com/index/checkLogin',
                                              'https://my.redpocketmobile.com/sdealer',
                                              self.carrieradmin.username,
                                              'username',
                                              self.carrieradmin.password,
                                              'password')
        r = s.post('%s/search/' % base_url, data={'search': self.transaction.phone_number_str})
        account_id = r.url.split("/").pop()
        r = s.post('%s/accounts/ajax-get-orders-data/account_id/%s' % (base_url, account_id),
                   data={"_search": False, "sidx": "date", "sord": "desc"})
        response_json = json.loads(r.text)
        for row in response_json['rows']:
            if row['id'] == self.transaction.pin:
                return 'Previous try successful, pin %s found in latest red ' \
                       'pocket order' % self.transaction.pin
        raise Exception('Red Pocket Recharge Failed, Scape result inconclusive')

    def scrape_page_plus_with_deathbycaptcha(self, br, attempt=None):
        """
        :param br: logined browser object
        :type br:  mechanize.Browser()
        :return: True
        :raise: Exception
        """
        if not attempt:
            attempt = 0
        if (self.transaction.retry_count == self.company.short_retry_limit + 1 and
                    'used' not in self.transaction.adv_status):
            self.page_plus_voice_refill()

        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Log into pageplus dealer site')
        cache.set(key="%s_pp" % self.transaction.id, value=True, timeout=600)

        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Set up the recharge request')
        # modified phone number to format (xxx) xxx-xxxx
        mod_ph = '(%s) %s-%s' % (str(self.phone_number)[:3], str(self.phone_number)[3:6], str(self.phone_number)[6:])
        cache.set(key="%s_pp" % self.transaction.id, value=True, timeout=600)


        br.follow_link(br.links(text='Replenish').next())
        refill_form = BeautifulSoup(br.response().read())

        cresponse = br.open_novisit(refill_form.find('iframe')['src'].replace('noscript', 'challenge'))
        # challenge = cresponse.get_data().split(':')[1].split(',')[0].strip().replace("'", "")
        # key = cresponse.get_data().split(':')[6].split(',')[0].strip().replace("'", "")
        response_data = cresponse.get_data().split('{')[1].split('}')[0].replace('\'', '').replace(' ', '').replace(
            '\n', '').split(',')
        resp_data_dict = {i.split(':')[0].strip(): i.split(':')[1].strip() for i in response_data}
        # challenge = resp_data_dict['challenge']
        # key = resp_data_dict['site']
        logger.debug('first captcha %s: %s' % (self.transaction.id, resp_data_dict['challenge']))
        rParams = {
            'k': resp_data_dict['site'],
            'c': resp_data_dict['challenge'],
            'reason': 'i',
            'type': 'image',
            'lang': 'en',
        }
        # reloading captcha
        rresponse = br.open_novisit('https://www.google.com/recaptcha/api/reload?%s' % urllib.urlencode(rParams))
        logger.debug('first url: https://www.google.com/recaptcha/api/reload?%s' % urllib.urlencode(rParams))
        newC = rresponse.read().split("'")[1]
        rParams['c'] = newC
        logger.debug('second captcha %s: %s' % (self.transaction.id, newC))
        google_image = 'https://www.google.com/recaptcha/api/image?%s' % urllib.urlencode(rParams)
        iresponse = br.open_novisit(google_image)
        temp_file = tempfile.TemporaryFile()
        temp_file.write(iresponse.read())
        temp_file.seek(0)

        # Initializing death captcha client
        client = SocketClient(self.super_company.deathbycaptcha_user, self.super_company.deathbycaptcha_pass)
        deathbycaptcha_balance = client.get_balance()
        self.captcha_low_balance(deathbycaptcha_balance)
        self.captcha_report()
        captcha = client.decode(temp_file)
        if not captcha:
            raise Exception('Failed to get response from death by captcha')
        self.calculate_captcha()
        br.select_form(nr=0)
        br.form.set_all_readonly(False)
        br.form[
            'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$mainContentArea$Item3$AddMinutes_5$WizardReplenishMinutes$ucPhoneNumber'] = mod_ph
        br.form[
            'ctl00$ctl00$ctl00$ContentPlaceHolderDefault$mainContentArea$Item3$AddMinutes_5$WizardReplenishMinutes$txtPIN'] = self.norm_pin
        br.form['recaptcha_response_field'] = captcha["text"]
        br.form['recaptcha_challenge_field'] = newC
        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                              'Captcha <a href="%s">image</a>resolved with answer "%s"' % (
                                              google_image, captcha["text"]))
        br.submit()

        # check refill result
        refill_response = BeautifulSoup(br.response().read())
        # CommandLog.objects.create(command='pageplus answer', message='%s\n%s\n%s' % (self.transaction.get_full_url(), br.geturl(), br.response().read()))
        if refill_response.find("div",
                                id="ContentPlaceHolderDefault_mainContentArea_Item3_AddMinutes_5_WizardReplenishMinutes_divResult"):
            outcome = refill_response.find("span",
                                           id="ContentPlaceHolderDefault_mainContentArea_Item3_AddMinutes_5_WizardReplenishMinutes_lblOutcome").text
            notes = refill_response.find("span",
                                         id="ContentPlaceHolderDefault_mainContentArea_Item3_AddMinutes_5_WizardReplenishMinutes_lblNotes").text
            if outcome.upper() == 'SUCCESSFUL':
                self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                      'Pageplus refill successful with message %s' % notes)
                return True
            else:
                raise Exception('Pageplus refill outcome %s with note: %s' % (outcome, notes))

        elif attempt > 3:
            raise Exception('PagePlus Recharge Failed, Result inconclusive')

        elif refill_response.find("div",
                                  id="ContentPlaceHolderDefault_mainContentArea_Item3_AddMinutes_5_WizardReplenishMinutes_divRecaptcha"):
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Captcha have changed on page. Starting new attempt for resolve it')
            self.scrape_page_plus_with_deathbycaptcha(br)

        else:
            message = refill_response.find("span",
                                           id="ContentPlaceHolderDefault_mainContentArea_Item3_AddMinutes_5_WizardReplenishMinutes_lblMessage").text
            if not message:
                cdata = refill_response.findAll(text=re.compile("CDATA"))
                for msg in cdata:
                    if "" in msg:
                        message = msg.split(",")[1].split(")")[0]
                        # message = refill_response.find("div", id="qtip-0-content").string
            CommandLog.objects.create(command='pageplus2', message='%s\n%s\n%s' % (
            self.transaction.get_full_url(), br.geturl(), br.response().read()))
            raise Exception('Pageplus refill failed with error %s' % message)

    def twilio_top_up(self, dealer_phone_number, voice):
        if not self.company.twilio_sid or \
                not self.company.twilio_auth_token or \
                not self.company.twilio_number:
            raise Exception('Twilio account is missing in company')

        self.transaction.add_transaction_step(
            self.step,
            self.carrier,
            SUCCESS,
            'Calling to refill phone')
        cache.set(key="%s_pp" % self.transaction.id, value=True, timeout=800)
        client = TwilioRestClient(self.company.twilio_sid, self.company.twilio_auth_token)
        call = client.calls.create(
            url=self.custom_redirect_url('twilio_request'),
            method="GET",
            from_="+1%s" % self.company.twilio_number,
            to="+1%s" % dealer_phone_number,
            send_digits=voice
        )
        self.transaction.add_transaction_step(
            self.step,
            self.carrier,
            SUCCESS,
            'Call was started, wait for complete')
        cache.set(key=call.sid, value="", timeout=800)
        time.sleep(60)
        wait_count = 1
        while not cache.get(call.sid):
            if wait_count > 24:
                raise Exception('No response received from twilio')
            time.sleep(10)
            wait_count = wait_count + 1
        self.transaction.add_transaction_step(
            self.step,
            self.carrier,
            SUCCESS,
            'Call completed the recording is available at '
            '<a target="blank" href="%s">link</a>.' % cache.get(call.sid))

    def login_site_request(self, url, url_success, user, user_tag, passw, passw_tag):
        payload = {user_tag: user, passw_tag: passw}
        s = requests.Session()
        s.post(url, data=payload)
        r = s.get(url_success)
        if r.url not in url_success:
            raise Exception("Failed to login to %s, please check the credentials" % url)
        base_url = r.url
        return s, base_url

    def red_pocket(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'Test Mode on')
            return False
        try:
            if self.transaction.retry_count and self.check_red_pocket_package_details():
                return
            self.red_pocket_standart_refill()
        except Exception, e:
            check_on_invalid_incomn_voucher(e, self.company, self.transaction)
            self.transaction.add_transaction_step(
                self.step,
                self.carrier,
                ERROR,
                'Red Pocket failed')
            if self.check_red_pocket_package_details():
                return
            if 'Used RPM Voucher' in e.message:
                e.message = e.message + '%s' % \
                                        self.additional_information_of_pin()
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            raise Exception(u'Red Pocket failed with error: %s' % e)

    def red_pocket_unlogin_refill(self):
        r = requests.get('http://goredpocket.com/ajax/apply_refill2.php?mdn=%s&voucher=%s' %
                         (self.transaction.autorefill.phone_number, self.transaction.pin))
        response = json.loads(r.text)
        if 'error' in response:
            raise Exception(response['text'])
        else:
            self.transaction.add_transaction_step(
                self.step,
                self.carrier,
                SUCCESS,
                'Red Pocket recharge succeeded. %s' % (response['text']))

    def red_pocket_voice_refill(self):
        self.twilio_top_up("8889933888", "wwwwwwww1www2wwwwwww%swwwwwwwwwwwwwwwwwwwwwwww%s" % (
        self.transaction.autorefill.phone_number, self.transaction.pin.replace('-', '')))

    def red_pocket_standart_refill(self):
        if (self.transaction.retry_count == self.company.short_retry_limit + 1 and
                    'used' not in self.transaction.adv_status):
            self.red_pocket_unlogin_refill()
        else:
            self.transaction.add_transaction_step(
                self.step,
                self.carrier,
                SUCCESS,
                'Logging into RedPocket website')
            # red pocket login
            s, base_url = self.login_site_request('https://my.redpocketmobile.com/index/checkLogin',
                                                  'https://my.redpocketmobile.com/sdealer',
                                                  self.carrieradmin.username,
                                                  'username',
                                                  self.carrieradmin.password,
                                                  'password')
            # sending request to red poket
            payload = {'mdn': self.transaction.autorefill.phone_number,
                       'voucher': self.transaction.pin,
                       'id': '',
                       'submit': "Apply Voucher",
                       'validate': "1"}
            r = s.post('%s/accounts/apply-voucher-mdn/id/' % base_url, data=payload)
            # extract session from last response
            soup2 = BeautifulSoup(r.text)
            inputs = soup2.findAll('input')
            session = None
            for inp in inputs:
                if inp.get('name') == 'session':
                    session = inp.get('value')
            # if we have session - make request to apply voucher
            if session:
                payload = {'mdn': self.transaction.autorefill.phone_number,
                           'voucher': self.transaction.pin,
                           'id': '',
                           'session': session,
                           'submit': "Apply Voucher",
                           'refill': "1"}
                r = s.post('%s/accounts/apply-voucher-mdn/id/' % base_url, data=payload)
            # parsing response for extract answer
            soup2 = BeautifulSoup(r.text)
            caption = soup2.find('caption')
            trs = soup2.findAll('tr')
            redpocket_plan = ''
            redpocket_balance = ''
            for tr in trs:
                for th in tr.findAll('th'):
                    # search errors in fail refill
                    if th.text == 'Error text:':
                        logger.debug('th %s' % th)
                        for td in tr.findAll('td'):
                            logger.debug('td %s' % td)
                            raise Exception('Red Pocket recharge failed with message, %s' % td.text)
                    # search balance in successfully refill
                    if th.text == 'Balance:':
                        for td in tr.findAll('td'):
                            redpocket_balance = 'Current balance %s' % td.text
                    # search current plan in successfully refill
                    if th.text == 'Current plan:':
                        for td in tr.findAll('td'):
                            redpocket_plan = 'Current plan: %s' % td.text
            # check is refill success
            if caption.text == 'Refill Voucher Done':
                self.transaction.add_transaction_step(
                    self.step,
                    self.carrier,
                    SUCCESS,
                    'Red Pocket recharge succeeded. %s %s' % (redpocket_plan, redpocket_balance))
            else:
                # catch error
                raise Exception('Red Pocket recharge failed with message, "%s"' % caption.text)

    def airvoice(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'Test Mode on')
            return False
        try:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Get account information from Air Voice')
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
            br.select_form(nr=0)
            br.form.set_all_readonly(False)
            br.form['ctl00$ContentPlaceHolder1$txtSubscriberNumber'] = str(self.transaction.autorefill.phone_number)
            br.form['ctl00$ContentPlaceHolder1$btnAccountDetails'] = 'View Account Info'
            br.submit()
            account_info = BeautifulSoup(br.response().read())
            subscriber = account_info.find("span", id="ctl00_ContentPlaceHolder1_lblSubscriberNumber").string
            if subscriber == 'n/a':
                error = account_info.find("span", id="ctl00_ContentPlaceHolder1_lblErrorMessage").string
                raise Exception("Failed to get account info, error is %s" % error)
            expiry_date = account_info.find("span", id="ctl00_ContentPlaceHolder1_lblairTimeExpirationDate").string
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Requesting recharge for subscriber %s, with expiry %s' % (
                                                  subscriber, expiry_date))
            data = urllib.urlencode({
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$btnAccountRecharge',
                '__EVENTARGUMENT': '',
                '__VIEWSTATE': account_info.find("input", id="__VIEWSTATE")['value'],
                'ctl00$ContentPlaceHolder1$txtSubscriberNumber': str(self.transaction.autorefill.phone_number),
                'ctl00$ContentPlaceHolder1$txtPin': str(self.transaction.pin),
            })
            response = br.open('https://www.airvoicewireless.com/PINRefill.aspx', data)
            recharge_info = BeautifulSoup(response.read())
            new_expiry_date = recharge_info.find("span", id="ctl00_ContentPlaceHolder1_lblairTimeExpirationDate").string
            message = recharge_info.find("span", id="ctl00_ContentPlaceHolder1_lblErrorMessage").string
            if new_expiry_date != expiry_date or message == 'Refill has been added':
                self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                      "Phone recharged successfully with new expiry date %s" % new_expiry_date)
                return
            raise Exception("Failed to recharge phone, error is %s" % message)
        except Exception, msg:
            logger.error("Exception: %s. Trace: %s." % (msg, traceback.format_exc(limit=10)))
            raise Exception(u'%s' % msg)

    def h2o_unlimited(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Requesting recharge from h20 in TEST mode')
            return False
        try:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Logging into H2O website')
            auth_result = login_h2o(self.carrieradmin)
            if auth_result['valid']:
                s = auth_result['session']
            else:
                raise Exception(auth_result['error'])
            r = s.get('https://www.h2odealer.com/mainCtrl.php?page=do_recharge&carrier_type=GSM&min=%s&pin=%s' % (
            self.transaction.autorefill.phone_number, self.transaction.pin))
            logger.debug('H2O page %s' % r.text)
            message = 'Undefined result. Please, check result at Dealer site'
            page = r.text
            status = int(page.split('var ret_code = \'')[1].split('\';')[0])
            if status >= 0:
                message = 'Successful refill. Expiration %s' % page.split('var exp = \'')[1].split('\';')[0]
            elif status < 0:
                raise Exception(page.split('var err_note = \'')[1].split('\';')[0])
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'%s' % message)
            result = mdn_status(self.transaction.autorefill.phone_number, s)
            if result['status'] >= 0:
                details = '%s|%s|%s|%s|%s|%s|%s' % (
                result['plan_name'], result['expiration'], result['available'], result['available_balance'],
                result['data_balance'], result['card'], result['card_balance'])
            else:
                details = result['message']
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, details)
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            raise Exception(u'%s' % e)

    def envie_mobile(self):
        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Logging into ENVIE MOBILE website')
        auth_result = login_h2o(self.carrieradmin)
        if auth_result['valid']:
            s = auth_result['session']
        else:
            raise Exception(auth_result['error'])
        r = s.get('https://www.h2odealer.com/mainCtrl.php?page=do_recharge_env&carrier_type=CDMA&min=%s&pin=%s' % (
        self.transaction.autorefill.phone_number, self.transaction.pin))
        logger.debug('ENVIE page %s' % r.text)
        message = 'Undefined result. Please, check result at Dealer site'
        page = r.text
        status = int(page.split('var ret_code = \'')[1].split('\';')[0])
        if status >= 0:
            message = 'Successful refill. Expiration %s' % page.split('var exp = \'')[1].split('\';')[0]
        elif status < 0:
            raise Exception(page.split('var err_note = \'')[1].split('\';')[0])
        self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, u'%s' % message)

    def approved_link(self):
        if settings.TEST_MODE:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Requesting recharge from Approved Link in TEST mode')
            return False
        try:
            self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS,
                                                  'Requesting on Approved Link website')
            if requests.post('http://75.99.53.250/CVWebService/PhoneHandler.aspx?method=ChargePVC&phonenumber=%s&'
                             'pvcnumber=%s' % (self.transaction.autorefill.phone_number,
                                               self.transaction.pin)).text != 'CHARGE_STATUS=FAILED':
                self.transaction.add_transaction_step(self.step, self.carrier, SUCCESS, 'Charge successful')
            else:
                self.transaction.add_transaction_step(self.step, self.carrier, ERROR, 'Charge has been failed')
                raise Exception(u'Charge has been failed')
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
            raise Exception(u'%s' % e)

    def custom_redirect_url(self, redirect, id=None):
        if not id:
            id = ''
        redirect_url = '%s/%s/%s' % (settings.SITE_DOMAIN, redirect, id)
        return redirect_url

    def calculate_captcha(self):
        # count captcha and log it
        if not self.super_company.deathbycaptcha_current_count:
            self.super_company.deathbycaptcha_current_count = 0
        self.super_company.deathbycaptcha_current_count += 1
        self.super_company.save()
        CaptchaLogs.objects.create(
            user=self.transaction.user,
            user_name=self.transaction.user.username,
            customer=self.transaction.customer,
            customer_name=self.transaction.customer,
            carrier=self.transaction.autorefill.plan.carrier,
            carrier_name=self.transaction.autorefill.plan.carrier.name,
            plan=self.transaction.autorefill.plan,
            plan_name=self.transaction.autorefill.plan.sc_sku,
            refill_type=self.transaction.autorefill.get_refill_type_display(),
            transaction=self.transaction,
        )

    def captcha_low_balance(self, balance):
        if balance >= self.super_company.deathbycaptcha_email_balance:
            self.super_company.deathbycaptcha_emailed = True
        # send email to admin when we had low balance
        # 1 captcha cost 0,139 cent
        if (self.super_company.deathbycaptcha_email_balance and self.super_company.deathbycaptcha_emailed
            and balance <= self.super_company.deathbycaptcha_email_balance):
            send_deathbycaptcha_low_balance(self.super_company, balance)
            self.super_company.deathbycaptcha_emailed = False
        self.super_company.save()

    def captcha_report(self):
        # send email to admin after some number of captcha what he needs
        if (self.super_company.deathbycaptcha_count
            and self.super_company.deathbycaptcha_count <= self.super_company.deathbycaptcha_current_count):
            send_deathbycaptcha_report(self.super_company)
            self.super_company.deathbycaptcha_current_count = 0
            self.super_company.save()

    def additional_information_of_pin(self):
        from ppars.apps.core import dealer_red_pocket
        status = ''
        try:
            answer = dealer_red_pocket.log_in_red_pocket(self.carrieradmin)
            result = dealer_red_pocket.get_pin_status(self.transaction.pin, answer['session'])
            if result['status']:
                status = '%s' % result['details']
            if result['url']:
                status = status + ', %s' % result['url']
        except Exception, e:
            logger.error("Exception: %s. Trace: %s." % (e, traceback.format_exc(limit=10)))
        finally:
            return status
