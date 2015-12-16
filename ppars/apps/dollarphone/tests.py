import unittest
import decimal
from suds.client import Client
import api
from api import dp_api_request, dollar_phone_api_authorization
'''
from ppars.apps.dollarphone.tests import TestApi
import unittest
suite = unittest.TestLoader().loadTestsFromTestCase(TestApi)
unittest.TextTestRunner(verbosity=3).run(suite)
'''


class TestApi(unittest.TestCase):

    def setUp(self):
        self.success_client = dollar_phone_api_authorization('twwzalmenSYS', 'twz%432API')
        self.form_fields_pin = {
                'username': 'twwzalmenSYS',
                'password': 'twz%432API',
                'Amount': decimal.Decimal(29.95),
                'OfferingId': '30084223',
                'ProviderId': 0,
                'transaction': '369369369'
        }
        self.form_fields_rtr = {
                'username': 'username',
                'password': 'password',
                'PhoneNumber': '525553760001',
                'Amount': decimal.Decimal(10.00),
                'OfferingId': '30027940',
                'ProviderId': 0,
                'transaction': '369369369'
        }

    @unittest.skip("DollarPhone authorization doesn`t demand tokens")
    def test_dollar_phone_api_authorization_fail(self):
        self.fail_client = dollar_phone_api_authorization('', '')
        self.assertNotIsInstance(self.fail_client, Client)
        with self.assertRaisesRegexp(Exception,
                                'Failed to initialize dollarphone api, please '
                                'verify your credentials'):
            api.dollar_phone_api_authorization('', '')

    def test_dollar_phone_api_authorization_success(self):
        self.assertIsInstance(self.success_client, Client)

    @unittest.skip("DollarPhone API not working")
    def test_dp_api_request_pin(self):
        # with patch('api.dollar_phone_api_authorization') as dp_api_mock:
        #     dp_api_mock.return_value = self.success_client
            response = dp_api_request(self.form_fields_pin)
            self.assertRegexpMatches(response['adv_status'], "Pin [\d] extracted from Dollar Phone transaction [\d]")
            self.assertRegexpMatches(response['pin'], "[\d]")
            self.assertEqual(response['status'], 1)


class TestScrapper(unittest.TestCase):

    def test_dollar_phone_site_authorization(self):
        pass

if __name__ == '__main__':
    unittest.main()
