import time, traceback, logging, mechanize, cookielib


br = mechanize.Browser()
cj = cookielib.LWPCookieJar()
br.set_handle_equiv(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
br.addheaders = [('User-agent', 'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.0.1) Gecko/2008071615 Fedora/3.0.1-1.fc9 Firefox/3.0.1')]
br.open('https://www.dollarphonepinless.com/sign-in')
br.select_form(nr=0)
emailid = raw_input("Enter the dollarphone username: ")
br.form['user_session[email]'] = emailid 
br.form['user_session[password]'] = raw_input("Enter the dollarphone password: ")
br.submit()
try:
        br.select_form(nr=0)
	# br.form['user_authentication[delivery_method]'] = ["email:%s"%emailid]
        phone_number = raw_input("Enter the dollarphonemobile: ")
        br.form['user_authentication[delivery_method]'] = ["sms:%s"%phone_number]
	br.submit()
	br.select_form(nr=0)
	br.form['user_authentication[code]'] = raw_input("Enter the authentication code: ")
	br.submit()
	if br.geturl() == 'https://www.dollarphonepinless.com/dashboard':
		print "Dollarphone account verified successfully"
	else :
		print br.geturl()
		print br.response().read()
except Exception,e:
	print br.response().read()
	print 'Error %s'%e
