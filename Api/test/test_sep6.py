import json
from unittest.mock import patch
from .test_setup import TestSetUpClass
from django.urls import reverse
from stellar_sdk.keypair import Keypair




class TestSep6Endpoints(TestSetUpClass):
    def test_00_check_info_endpoint(self):
        info_url = reverse("sep6Info")
        req_data = self.client.generic(method="GET", path=info_url, content_type='application/json')
        self.assertTrue(req_data.status_code == 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    @patch("Api.views.is_Asset_trusted")
    def test_01_sep6_deposit_with_correct_details(self, mock_trust):
        mock_trust.return_value = [True, 10000]
        sep_url = reverse("sep6Deposit")
        req_data = self.client.get(sep_url, {"asset_code": "NGN", "account": Keypair.random().public_key, "amount": 1000}, content_type='application/json')
        self.assertTrue(req_data.status_code == 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("eta" in req_data.data)
        self.assertTrue("how" in req_data.data)
        self.assertTrue("extra_info" in req_data.data)
        self.assertTrue("bank_name" in req_data.data["extra_info"])
        self.assertTrue("account_number" in req_data.data["extra_info"])
        self.assertTrue("transaction_ref" in req_data.data["extra_info"])

    def test_02_sep6_deposit_with_incorrect_details(self):
        #Failed sep6 deposit
        sep_url = reverse("sep6Deposit")
        req_data = self.client.get(sep_url, {"asset_code": "NGN", "account": Keypair.random().public_key, "amount": 1000}, content_type='application/json')
        self.assertTrue(req_data.status_code == 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        # self.assertTrue("eta" in req_data.data)
        # self.assertTrue("how" in req_data.data)
        # self.assertTrue("extra_info" in req_data.data)
        # self.assertTrue("bank_name" in req_data.data["extra_info"])
        # self.assertTrue("account_number" in req_data.data["extra_info"])
        # self.assertTrue("transaction_ref" in req_data.data["extra_info"])
