import time, traceback, logging, mechanize, cookielib, json, requests
from flask import Flask
from flask.ext.restful import reqparse, abort, Api, Resource
from flask.ext.restful import Resource, fields, marshal_with
from suds.transport.https import WindowsHttpAuthenticated
from suds.xsd.doctor import ImportDoctor, Import
from suds.client import Client as WSClient
from suds.cache import FileCache
from BeautifulSoup import BeautifulSoup
app = Flask(__name__)
api = Api(app)


purchase_pin_parser = reqparse.RequestParser()
purchase_pin_parser.add_argument('Transaction', type=str, location='form', required=True)
purchase_pin_parser.add_argument('callbackUrl', type=str, location='form', required=False)
purchase_pin_parser.add_argument('username', type=str, location='form', required=True)
purchase_pin_parser.add_argument('password', type=str, location='form', required=True)
purchase_pin_parser.add_argument('OfferingId', type=int, location='form', required=True)
purchase_pin_parser.add_argument('Amount', type=float, location='form', required=True)

purchase_pin_response = {
    'status': fields.Integer,
    'adv_status': fields.String,
    'pin': fields.String,
}

class dpapi_purchase_pin(Resource):
    @marshal_with(purchase_pin_response)
    def post(self):
        args = purchase_pin_parser.parse_args()
        try:
            response = dict()
            # lgr.info('[%s] Get pin request received'%args['Transaction'])
            ntlm = WindowsHttpAuthenticated(username='DPWEB-1\\%s'%args['username'], password=args['password'])
            imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
            imp = Import('http://www.w3.org/2001/XMLSchema')
            imp.filter.add('https://dollarphone.com/PMAPI/PinManager')
            doctor = ImportDoctor(imp)
            # lgr.info('[%s] Intializing the dollarphone api client'%args['Transaction'])
            try:
                client = WSClient("https://www.dollarphone.com/pmapi/PinManager.asmx?WSDL", transport=ntlm, doctor=doctor)
            except Exception,e:
                raise Exception('Failed to initialize dollarphone api, please verify your credentials')
            req = client.factory.create('TopUpReqType')
            action = client.factory.create('TopUpAction')
            req.Action = action.PurchasePin
            req.OfferingId = args['OfferingId']
            req.Amount = args['Amount']
            lgr.info('[%s] Requesting pin from dollarphone '%args['Transaction'])
            try:
                request_pin = client.service.TopUpRequest(req)
            except Exception,e:
                raise Exception('Failed to initialize dollarphone api, please verify your credentials')
            if request_pin.responseCode < 0 :
                raise Exception('%s'%dp_response_codes[request_pin.responseCode])
            if request_pin.TransId == 0:
                raise Exception('Dollarphone API retuned a 0 TransId, please contact Dollarphone to check your setup.')
            time.sleep(10)
            lgr.info('[%s] Checking status of dollarphone  transaction %s.'%(args['Transaction'], request_pin.TransId))
            while True:
                status = client.service.TopupConfirm(request_pin.TransId)
                if status.Status == 'Success':
                    response['status'] = 1
                    response['pin'] = status.PIN
                    break
                elif status.Status == 'Failed':
                    raise Exception('Dollar phone transaction %s failed, with message %s'%(request_pin.TransId, dp_response_codes[status.ErrorCode]))
                time.sleep(2)
            lgr.info('[%s] Pin %s received from dollarphone.'%(args['Transaction'], status.PIN))

        except Exception,e:
            response['status'] = 0
            response['adv_status'] = "Failure :%s"%e
            lgr.error('[%s] Details: %s'%(args['Transaction'], e))

        finally:
            if args['callbackUrl']:
                requests.get(args['callbackUrl'], params=response)
            return response, 200


topup_parser = reqparse.RequestParser()
topup_parser.add_argument('Transaction', type=str, location='form', required=True)
topup_parser.add_argument('callbackUrl', type=str, location='form', required=False)
topup_parser.add_argument('username', type=str, location='form', required=True)
topup_parser.add_argument('password', type=str, location='form', required=True)
topup_parser.add_argument('OfferingId', type=int, location='form', required=True)
topup_parser.add_argument('Amount', type=float, location='form', required=True)
topup_parser.add_argument('PhoneNumber', type=str, location='form', required=True)

topup_response = {
    'status': fields.Integer,
    'adv_status': fields.String,
}

class dpapi_topup(Resource):
    @marshal_with(topup_response)
    def post(self):
	args = topup_parser.parse_args()
	try:
	    response = dict()
	    lgr.info('[%s] Topup request received'%args['Transaction'])
    	    ntlm = WindowsHttpAuthenticated(username='DPWEB-1\\%s'%args['username'], password=args['password'])
	    imp = Import('http://schemas.xmlsoap.org/soap/encoding/')
	    imp = Import('http://www.w3.org/2001/XMLSchema')  
	    imp.filter.add('https://dollarphone.com/PMAPI/PinManager')
	    doctor = ImportDoctor(imp)
	    lgr.info('[%s] Intializing the dollarphone api client'%args['Transaction'])
	    try:
	        client = WSClient("https://www.dollarphone.com/pmapi/PinManager.asmx?WSDL", transport=ntlm, doctor=doctor)
	    except Exception,e:
		raise Exception('Failed to initialize dollarphone api, please verify your credentials')
	    req = client.factory.create('TopUpReqType')
	    action = client.factory.create('TopUpAction')
	    req.Action = action.AddFunds
	    req.PhoneNumber = args['PhoneNumber']
	    req.OfferingId = args['OfferingId']
	    req.Amount = args['Amount']
	    lgr.info('[%s] Requesting topup from dollarphone '%args['Transaction'])
	    try:
	    	request_pin = client.service.TopUpRequest(req)
            except Exception,e:
                raise Exception('Failed to initialize dollarphone api, please verify your credentials')
	    if request_pin.responseCode < 0 :
		raise Exception('%s'%dp_response_codes[request_pin.responseCode])
	    if request_pin.TransId == 0:
		raise Exception('Dollarphone API retuned a 0 TransId, please contact Dollarphone to check your setup.')
	    time.sleep(10)
	    lgr.info('[%s] Checking status of dollarphone  transaction %s.'%(args['Transaction'], request_pin.TransId))
	    while True:
		status = client.service.TopupConfirm(request_pin.TransId)
		if status.Status == 'Success':
		    response['status'] = 1
		    break
		elif status.Status == 'Failed':
		    raise Exception('Dollar phone transaction %s failed, with message %s'%(request_pin.TransId, dp_response_codes[status.ErrorCode]))
		time.sleep(2)
	    response['adv_status'] = 'Phone topped up successfully, with dollarphone transaction %s'%request_pin.TransId
	    lgr.info('[%s] Phone %s topped up successfully.'%(args['Transaction'], args['PhoneNumber']))

	except Exception,e:
	    response['status'] = 0
	    response['adv_status'] = "Failure :%s"%e
	    lgr.error('[%s] Details: %s'%(args['Transaction'], e))	

	finally:
	    if args['callbackUrl']:
		requests.get(args['callbackUrl'], params=response)		
	    return response, 200


spurchase_pin_parser = reqparse.RequestParser()
spurchase_pin_parser.add_argument('Transaction', type=str, location='form', required=True)
spurchase_pin_parser.add_argument('callbackUrl', type=str, location='form', required=False)
spurchase_pin_parser.add_argument('username', type=str, location='form', required=True)
spurchase_pin_parser.add_argument('password', type=str, location='form', required=True)
spurchase_pin_parser.add_argument('Carrier', type=str, location='form', required=True)
spurchase_pin_parser.add_argument('Plan', type=str, location='form', required=True)
spurchase_pin_parser.add_argument('Amount', type=str, location='form', required=True)

class dpsite_purchase_pin(Resource):
    @marshal_with(purchase_pin_response)
    def post(self):
        args = spurchase_pin_parser.parse_args()
        try:
	    response = dict()
	    lgr.info('[%s] Get Pin Site request received, logging into dollarphone'%args['Transaction'])
            br = login_site(
		'https://www.dollarphonepinless.com/sign-in', 
		['https://www.dollarphonepinless.com/dashboard'], 
		args['username'],	
		'user_session[email]',
		args['password'], 
		'user_session[password]'
	     )	
	    lgr.info('[%s] Filling the get pin form'%args['Transaction'])
	    br.follow_link(br.links(text='Domestic PIN').next())
	    br.select_form(nr=0)
	    br.form.new_control('text','ppm_order[skip_check_for_duplicates]',{'value':''})
	    br.form.fixup()
	    br.form['ppm_order[skip_check_for_duplicates]'] = '1'
	    br.form['ppm_order[country_code]'] = ['US']
	    carrier = br.find_control('ppm_order[prepaid_mobile_product_group_id]', type="select")
	    for item in carrier.items:
		if item.get_labels()[0].text == args['Carrier']:
		    br.form['ppm_order[prepaid_mobile_product_group_id]'] = [item.name]
		    break
	    plan_name = br.find_control('ppm_order[prepaid_mobile_product_id]', type="select")
	    for item in plan_name.items:
		if item.get_labels()[0].text == args['Plan']:
		    br.form['ppm_order[prepaid_mobile_product_id]'] = [item.name]
		    break
	    plan_cost = br.find_control('ppm_order[face_amount]', type="select")
	    for item in plan_cost.items:
		if item.get_labels()[0].text == args['Amount']:
		    br.form['ppm_order[face_amount]'] = [item.name]
		    break
	    br.submit()
	    lgr.info('[%s] Requesting Pin from Dollar Phone Site.'%args['Transaction'])
	    try:
		br.select_form(nr=0)
		br.submit()
		receipt_url = br.response().read().split(':')[1].split("'")[1].split('processing')[0]
	    except Exception,e:
		#lgr.info("%s"%br.response().read())
		raise Exception("Failed to request PIN, unexpected response from dollarphone website.")	
	    if not receipt_url:
		#lgr.info("%s"%br.response().read())
		raise Exception("Failed to request PIN, unexpected response from dollarphone website.")
	    time.sleep(10)
	    while True:
		br.open(u'https://www.dollarphonepinless.com%scheck_status.json'%receipt_url)
		pin_status = json.loads(br.response().read())
		if pin_status['status'] == 'Completed':
		    br.open('https://www.dollarphonepinless.com%sreceipt'%receipt_url)
		    receipt = br.response().read()
		    break
		elif pin_status['status'] == 'Failed':
		    raise Exception('Get Pin request failed, check the <a target="blank" href="https://www.dollarphonepinless.com%sreceipt">receipt</a> for more information'%receipt_url)
		time.sleep(2)
	    lgr.info('[%s] Extracting the Pin from Dollar Phone <a target="blank" href="https://www.dollarphonepinless.com%sreceipt">receipt</a>.'%(args['Transaction'], receipt_url))
	    soup = BeautifulSoup(receipt)
	    table = soup.find("table")
	    for row in table.findAll('tr')[1:]:
		col = row.findAll('td')
		if col[0].string.strip() == 'PIN:':
		    response['status'] = 1
		    response['pin'] = col[1].div.strong.string.strip()
		    break
	    lgr.info('[%s] Pin %s received from dollarphone.'%(args['Transaction'], response['pin']))

        except Exception,e:
            response['status'] = 0
            response['adv_status'] = "Failure :%s"%e
            lgr.error('[%s] Details: %s'%(args['Transaction'], e))

        finally:
	    if args['callbackUrl']:
		requests.get(args['callbackUrl'], params=response)		
            return response, 200

stopup_parser = reqparse.RequestParser()
stopup_parser.add_argument('Transaction', type=str, location='form', required=True)
stopup_parser.add_argument('callbackUrl', type=str, location='form', required=False)
stopup_parser.add_argument('username', type=str, location='form', required=True)
stopup_parser.add_argument('password', type=str, location='form', required=True)
stopup_parser.add_argument('Carrier', type=str, location='form', required=True)
stopup_parser.add_argument('Plan', type=str, location='form', required=True)
stopup_parser.add_argument('Amount', type=str, location='form', required=True)
stopup_parser.add_argument('PhoneNumber', type=str, location='form', required=True)

class dpsite_topup(Resource):
    @marshal_with(topup_response)
    def post(self):
        args = stopup_parser.parse_args()
        try:
	    response = dict()
	    lgr.info('[%s] Site Topup request received, logging into dollarphone'%args['Transaction'])
            br = login_site(
		'https://www.dollarphonepinless.com/sign-in', 
		['https://www.dollarphonepinless.com/dashboard'], 
		args['username'],	
		'user_session[email]',
		args['password'], 
		'user_session[password]'
	     )	
	    lgr.info('[%s] Filling the topup form'%args['Transaction'])
	    br.follow_link(br.links(text='Domestic Top-Up').next())
	    br.select_form(nr=0)
	    br.form['ppm_order[country_code]'] = ['US']
   	    br.form['ppm_order[prepaid_mobile_phone]'] = args['PhoneNumber'] 
	    carrier = br.find_control('ppm_order[prepaid_mobile_product_group_id]', type="select")
	    for item in carrier.items:
		if item.get_labels()[0].text == args['Carrier']:
		    br.form['ppm_order[prepaid_mobile_product_group_id]'] = [item.name]
		    break
	    plan_name = br.find_control('ppm_order[prepaid_mobile_product_id]', type="select")
	    for item in plan_name.items:
		if item.get_labels()[0].text == args['Plan']:
		    br.form['ppm_order[prepaid_mobile_product_id]'] = [item.name]
		    break
	    plan_cost = br.find_control('ppm_order[face_amount]', type="select")
	    for item in plan_cost.items:
		if item.get_labels()[0].text == args['Amount']:
		    br.form['ppm_order[face_amount]'] = [item.name]
		    break
	    br.submit()
	    lgr.info('[%s] Requesting Topup from Dollar Phone Site.'%args['Transaction'])
	    try:
		br.select_form(nr=0)
		br.submit()
		receipt_url = br.response().read().split(':')[1].split("'")[1].split('processing')[0]
	    except Exception,e:
		raise Exception("Failed to topup phone, unexpected response from dollarphone website.")
	    if not receipt_url:
		raise Exception("Failed to topup phone, unexpected response from dollarphone website.")
	    time.sleep(10)
	    while True:
		br.open(u'https://www.dollarphonepinless.com%scheck_status.json'%receipt_url)
		pin_status = json.loads(br.response().read())
		if pin_status['status'] == 'Completed':
		    response['status'] = 1
		    break
		elif pin_status['status'] == 'Failed':
		    raise Exception('Topup phone failed, details are at <a target="blank" href="https://www.dollarphonepinless.com%sreceipt">receipt</a>.'%receipt_url)
		time.sleep(2)
	    response['adv_status'] = 'Topup successful, details are at <a target="blank" href="https://www.dollarphonepinless.com%sreceipt">receipt</a>.'%receipt_url 
	    lgr.info('[%s] Phone %s topped up successfully.'%(args['Transaction'], args['PhoneNumber']))

        except Exception,e:
            response['status'] = 0
            response['adv_status'] = "Failure :%s"%e
            lgr.error('[%s] Details: %s'%(args['Transaction'], e))

        finally:
	    if args['callbackUrl']:
		requests.get(args['callbackUrl'], params=response)		
            return response, 200

##
## Actually setup the Api resource routing here
##
api.add_resource(dpapi_purchase_pin, '/dpapi/purchase_pin')
api.add_resource(dpapi_topup, '/dpapi/topup')
api.add_resource(dpsite_purchase_pin, '/dpsite/purchase_pin')
api.add_resource(dpsite_topup, '/dpsite/topup')

##
## Initialization
##
dp_response_codes = {
    -1:'Invalid Login',
    -2:'Invalid Login',
    -6:'Invalid offering',
    -34:'Account past due',
    -35:'Transaction exceeds credit limit',
    -40:'Invalid Phone number',
    -41:'Invalid amount',
    -42:'Invalid Product',
    -400:'Invalid phone number',
    -401:'Processing error',
    -402:'Transaction already completed',
    -403:'Invalid transaction amount',
    -404:'Invalid product',
    -405:'Duplicate transaction',
    -406:'Invalid Transaction Id',
    -407:'Denomination currently unavailable',
    -408:'Transaction amount limit exceeded',
    -409:'Destination Account is not prepaid',
    -410:'Handset was reloaded within the last 10 minutes',
    -411:'TopUp refused',
}

def login_site(url, url_success, user, user_tag, passw, passw_tag):	
    br = mechanize.Browser()
    cj = cookielib.LWPCookieJar()
    br.set_handle_equiv(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)
    br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
    br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
    br.open(url)
    br.select_form(nr=0)
    br.form[user_tag] = user
    br.form[passw_tag] = passw
    br.submit()
    if br.geturl() not in url_success:
	raise Exception("Failed to login to %s, please check the credentials"%url)
    return br

logfile = '/home/scriptuser/ppars_backend/ppars_backend.log'
fh = logging.FileHandler(logfile)
frmt = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(frmt)
lgr = logging.getLogger('ppars_backend')
lgr.setLevel(logging.INFO)
lgr.addHandler(fh)
if __name__ == '__main__':
    app.run(debug=True)
