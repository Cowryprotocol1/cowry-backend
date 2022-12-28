import json
from unittest.mock import patch

import toml
from test_setup import TestSetUpClass, stablecoin_issuer, domain
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
        print(req_data.data)
        self.assertTrue(req_data.status_code == 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("eta" in req_data.data)
        self.assertTrue("how" in req_data.data)
        self.assertTrue("extra_info" in req_data.data)
        self.assertTrue("bank_name" in req_data.data["extra_info"])
        self.assertTrue("account_number" in req_data.data["extra_info"])
        self.assertTrue("transaction_ref" in req_data.data["extra_info"])

    def test_02_sep6_deposit_with_incorrect_details(self):
        #Failed sep6 deposit, this only checks for trustline
        sep_url = reverse("sep6Deposit")
        _data = {"asset_code": "NGN","account": Keypair.random().public_key, "amount": 1000}
        req_data = self.client.get(sep_url, _data, content_type='application/json')
        self.assertTrue(req_data.status_code == 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    def test_03_sep6_withdrawal_with_correct_details(self):
        #test response from the sep6 withdrawal endpoint
        sep6_url = reverse("sep6Withdraw")
        _data = {"asset_code": "NGN", "account": Keypair.random().public_key, "amount": 1000, "dest":1111111111, "dest_extra":"FCMB"}
        req_data = self.client.get(sep6_url, _data, content_type='application/json')
        self.assertTrue(req_data.headers["Content-Type"] == "application/json")
        self.assertTrue(req_data.status_code == 200)
        self.assertTrue("memo" in req_data.data)
        self.assertTrue("eta" in req_data.data)
        self.assertTrue("fee_fixed" in req_data.data)
        self.assertEqual(req_data.data["account_id"], stablecoin_issuer)
        self.assertEqual(req_data.data["memo_type"], "text")

    def test_04_sep6_withdrawal_with_incorrect_details(self):
        #test response from the sep6 withdrawal endpoint with an invalid params
        sep6_url = reverse("sep6Withdraw")
        _data = {"asset_code": "BTC", "account": Keypair.random(
        ).public_key, "amount": 1000, "dest": 6666}
        req_data = self.client.get(
            sep6_url, _data, content_type='application/json')
        print(req_data.data)
        self.assertTrue(req_data.headers["Content-Type"] == "application/json")
        self.assertTrue(req_data.status_code == 400)
        self.assertTrue("asset_code" in req_data.data)
        self.assertTrue("dest" in req_data.data)
        self.assertTrue("dest_extra" in req_data.data)
    def test_05_toml_endpoint(self):
        #Test toml endpoint response
        toml_url = reverse("toml_endpoint")
        req_data = self.client.get(toml_url)
        # print(req_data.content.decode())
        toml_str =toml.loads(req_data.content.decode())

        self.assertTrue(req_data.headers["Content-Type"] == "text/plain; charset=utf-8")
        self.assertTrue(req_data.headers["Access-Control-Allow-Origin"] == "*")
        self.assertEqual(toml_str["TRANSFER_SERVER"], f"https://{domain}/sep6")



