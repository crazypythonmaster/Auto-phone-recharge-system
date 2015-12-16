import unittest
from django.contrib.auth.models import User
from django.test import TestCase
from httplib2 import ServerNotFoundError
from authorize import AuthorizeResponseError
from ppars.apps.core.models import CompanyProfile, Transaction, AutoRefill, Plan, Carrier, Customer
from ppars.apps.core.refill import Refill
from pysimplesoap.client import SoapFault


class CompanyProfileTests(TestCase):
    def setUp(self):

        CompanyProfile.objects.create(
            id=1,
            company_name='Default Test Company'
        )
        CompanyProfile.objects.create(
            id=2,
            updated=True,
            superuser_profile=True,
            company_name='Test Company',
            email_id='test@test.ts',
            email_success_refill=True,
            email_success_charge=True,
            pin_error=True,
            short_retry_limit=0,
            short_retry_interval=0,
            long_retry_limit=0,
            long_retry_interval=0,
            twilio_number=1234567890,
            twilio_sid='sid987654321',
            twilio_auth_token='test123token',
            deathbycaptcha_user='testuser',
            deathbycaptcha_pass='test123pass',
            deathbycaptcha_email_balance=0,
            deathbycaptcha_count=0,
            deathbycaptcha_current_count=0,
            deathbycaptcha_emailed=False,
            pageplus_refillmethod='CP',
            dollar_type='A',
            dollar_user='testuser',
            dollar_pass='test123pass',
            mandrill_key='testkey',
            mandrill_email='mandrill@test.ts',
            authorize_api_login_id='testauthorize1D',
            authorize_transaction_key='testauthorize1k3y',
            authorize_precharge_days=0,
            cccharge_type='A',
            usaepay_source_key='usaepaytestKey4321',
            usaepay_pin='usaepaytestPin4321',
            sc_company_id='testSC6789id',
            sc_password='testSC6789pass',
            sc_email='testSC@test.ts',
            asana_api_key='asanatestkey123',
            asana_workspace='asanatestWS123',
            asana_project_name='asanatestPJ123',
            asana_user='321456765432'
        )

    def test_updated(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.updated, False)
        self.assertEqual(test_company.updated, True)

    def test_superuser_profile(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.superuser_profile, False)
        self.assertEqual(test_company.superuser_profile, True)

    def test_company_name(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.company_name, 'Default Test Company')
        self.assertEqual(test_company.company_name, 'Test Company')

    def test_email_id(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.email_id, None)
        self.assertEqual(test_company.email_id, 'test@test.ts')

    def test_email_success(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.email_success_refill, False)
        self.assertEqual(default_company.email_success_charge, False)
        self.assertEqual(default_company.email_success_refill, True)
        self.assertEqual(default_company.email_success_charge, True)

    def test_pin_error(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.pin_error, False)
        self.assertEqual(test_company.pin_error, True)

    def test_short_retry_limit(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.short_retry_limit, None)
        self.assertEqual(test_company.short_retry_limit, 0)

    def test_short_retry_interval(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.short_retry_interval, None)
        self.assertEqual(test_company.short_retry_interval, 0)

    def test_long_retry_limit(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.long_retry_limit, None)
        self.assertEqual(test_company.long_retry_limit, 0)

    def test_long_retry_interval(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.long_retry_interval, None)
        self.assertEqual(test_company.long_retry_interval, 0)

    def test_twilio_number(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.twilio_number, None)
        self.assertEqual(test_company.twilio_number, '1234567890')

    def test_twilio_sid(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.twilio_sid, None)
        self.assertEqual(test_company.twilio_sid, 'sid987654321')

    def test_twilio_auth_token(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.twilio_auth_token, None)
        self.assertEqual(test_company.twilio_auth_token, 'test123token')

    def test_deathbycaptcha_user(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_user, None)
        self.assertEqual(test_company.deathbycaptcha_user, 'testuser')

    def test_deathbycaptcha_pass(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_pass, None)
        self.assertEqual(test_company.deathbycaptcha_pass, 'test123pass')

    def test_deathbycaptcha_email_balance(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_email_balance, 70)
        self.assertEqual(test_company.deathbycaptcha_email_balance, 0)

    def test_deathbycaptcha_count(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_count, 5000)
        self.assertEqual(test_company.deathbycaptcha_count, 0)

    def test_deathbycaptcha_current_count(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_current_count, 0)
        self.assertEqual(test_company.deathbycaptcha_current_count, 0)

    def test_deathbycaptcha_emailed(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.deathbycaptcha_emailed, True)
        self.assertEqual(test_company.deathbycaptcha_emailed, False)

    def test_pageplus_refillmethod(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.pageplus_refillmethod, 'TW')
        self.assertEqual(test_company.pageplus_refillmethod, 'CP')

    def test_dollar_type(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.dollar_type, None)
        self.assertEqual(test_company.dollar_type, 'A')

    def test_dollar_user(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.dollar_user, None)
        self.assertEqual(test_company.dollar_user, 'testuser')

    def test_dollar_pass(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.dollar_pass, None)
        self.assertEqual(test_company.dollar_pass, 'test123pass')

    def test_mandrill_key(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.mandrill_key, None)
        self.assertEqual(test_company.mandrill_key, 'testkey')

    def test_mandrill_email(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.mandrill_email, None)
        self.assertEqual(test_company.mandrill_email, 'mandrill@test.ts')

    def test_authorize_api_login_id(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.authorize_api_login_id, None)
        self.assertEqual(test_company.authorize_api_login_id, 'testauthorize1D')

    def test_authorize_transaction_key(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.authorize_transaction_key, None)
        self.assertEqual(test_company.authorize_transaction_key, 'testauthorize1k3y')

    def test_authorize_precharge_days(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.authorize_precharge_days, None)
        self.assertEqual(test_company.authorize_precharge_days, 0)

    def test_cccharge_type(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.cccharge_type, None)
        self.assertEqual(test_company.cccharge_type, 'A')

    def test_usaepay_source_key(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.usaepay_source_key, None)
        self.assertEqual(test_company.usaepay_source_key, 'usaepaytestKey4321')

    def test_usaepay_pin(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.usaepay_pin, None)
        self.assertEqual(test_company.usaepay_pin, 'usaepaytestPin4321')

    def test_sc_company_id(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.sc_company_id, None)
        self.assertEqual(test_company.sc_company_id, 'testSC6789id')

    def test_sc_password(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.sc_password, None)
        self.assertEqual(test_company.sc_password, 'testSC6789pass')

    def test_sc_email(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.sc_email, None)
        self.assertEqual(test_company.sc_email, 'testSC@test.ts')

    def test_asana_api_key(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.asana_api_key, None)
        self.assertEqual(test_company.asana_api_key, 'asanatestkey123')

    def test_asana_workspace(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.asana_workspace, None)
        self.assertEqual(test_company.asana_workspace, 'asanatestWS123')

    def test_asana_project_name(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.asana_project_name, None)
        self.assertEqual(test_company.asana_project_name, 'asanatestPJ123')

    def test_asana_user(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(default_company.asana_user, None)
        self.assertEqual(test_company.asana_user, '321456765432')

    def test_company_name_unicode(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        self.assertEqual(str(default_company), 'Default Test Company')
        self.assertEqual(str(test_company), 'Test Company')

    @unittest.expectedFailure
    def test_authorize_authorization(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        with self.assertRaisesRegexp(AuthorizeResponseError,
                                     'E00006: The API user name is invalid or not present.'):
            default_company.authorize_authorization()
        with self.assertRaisesRegexp(AuthorizeResponseError,
                                     'E00007: User authentication failed due to invalid authentication values.'):
            test_company.authorize_authorization()

    @unittest.expectedFailure
    def test_usaepay_authorization(self):
        default_company = CompanyProfile.objects.get(id=1)
        test_company = CompanyProfile.objects.get(id=2)
        with self.assertRaisesRegexp(SoapFault,
                                     'SOAP-ENV:Server: 23: Specified source key not found.'):
            default_company.usaepay_authorization()
        with self.assertRaisesRegexp(ServerNotFoundError,
                                     'Unable to find the server at sandbox.usaepay.com'):
            test_company.usaepay_authorization()


# class GetPin(TestCase):
#
#     def setUp(self):
#         user = User(username='TestUser',
#              password='123',
#              email='test@test.ts')
#         user.save()
#         carrier = Carrier.objects.create(id=1,
#                                name='TestCarrier')
#         plan = Plan.objects.create(id=1,
#                             plan_id='Testplan',
#                             carrier=carrier,
#                             plan_name='TestPlan',
#                             plan_type='TP',
#                             plan_cost='10')
#         customer = Customer.objects.create(
#                             id=1,
#                             user=user,
#                             first_name='Testfirst_name',
#                             last_name='Testlast_name',
#                             phone_numbers=1234567899,
#                             primary_email='customertest@test.ts')
#         autorefill = AutoRefill.objects.create(id=1,
#                                   user=user,
#                                   customer=customer,
#                                   phone_number=1234567899,
#                                   plan=plan,
#                                   refill_type='GP',
#                                   trigger='MN',
#                                   enabled=True)
#         Transaction.objects.create(id=1,
#                                   user=user,
#                                   autorefill=autorefill,
#                                   state='P')
#
#     def test_check_is_not_top_up_plan_use_for_get_pin_operations(self):
#         ar = Refill(1)
#         with self.assertRaisesRegexp(Exception,
#                                      "Get pin request created for a top up plan"):
#             ar.check_is_not_top_up_plan_use_for_get_pin_operations()