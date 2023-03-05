# test deposit to get IFP account for deposits
# test when user reply endpoint of transaction sent
# Test withdrawal from the protocol
# 
import json
from test_setup import TestSetUpClass
from django.urls import reverse
from stellar_sdk.keypair import Keypair
from modelApp.models import MerchantsTable
from unittest.mock import patch
from modelApp.models import TransactionsTable
from model_bakery import baker
from utils.utils import Id_generator





class Sep24DepositAndWithdrawalUrlTest(TestSetUpClass):
    

# =======================================================================
# TESTING FOR GETTING WIDGET URL
# =======================================================================
    def test_sep24_get_url_endpoint_deposit(self):
        """
        getting url for sep 24 interactive deposit
        """
        self.url = reverse('sep24 Deposit')
        self.request_data.update({"transaction_source":"sep", "asset_code":"NGN"})
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["type"] == "interactive_customer_info_needed")
        self.assertTrue("url" in req_data.data)
        self.assertTrue("id" in req_data.data)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    def test_sep24_get_url_endpoint_withdrawal(self):
        """
        getting url for sep24 interactive withdrawal
        """
        self.url = reverse('sep24 withdrawal')
        self.request_data.update({"transaction_source":"sep", "asset_code":"NGN"})
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["type"] == "interactive_customer_info_needed")
        self.assertTrue("url" in req_data.data)
        self.assertTrue("id" in req_data.data)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    def test_sep24_get_url_endpoint_withdrawal_noParams(self):
        """
        getting url for sep 24 withdrawal fail no, params
        """
        self.url = reverse('sep24 withdrawal')
        # self.request_data.update({"transaction_source":"sep", "asset_code":"NGN"})
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        print(req_data.json())
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("error" in req_data.data)
    def test_sep24_get_url_endpoint_deposit_noParams(self):
        """
        getting url for sep 24 deposit fail no, params
        """
        self.url = reverse('sep24 Deposit')

        # self.request_data.update({"transaction_source":"sep", "asset_code":"NGN"})
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        print(req_data.json())
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("error" in req_data.data)




# add test for widget