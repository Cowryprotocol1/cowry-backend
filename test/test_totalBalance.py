from lib2to3.pgen2 import token
from test_setup import TestSetUpClass
from django.urls import reverse
import json
from modelApp.models import TokenTable
from unittest.mock import patch


class BalanceTest(TestSetUpClass):
    URL = reverse("totalSupply")

    @patch("Api.views.protocolAssetTotalSupply")
    def test_001_total_balance(self, mock_totalBal):
        #total asset balance endpoint successfully returns the correct details
        mock_totalBal.return_value = {
            "NGNALLOW": {
                "total_accounts": {
                    "authorized": 100,
                    "authorized_to_maintain_liabilities": 0,
                    "unauthorized": 0,
                },
                "total_balance": {
                    "authorized": "10000000.00",
                    "authorized_to_maintain_liabilities": "0.0000000",
                    "unauthorized": "0.0000000",
                },
            },
            "NGN": {
                "total_accounts": {
                    "authorized": 2,
                    "authorized_to_maintain_liabilities": 0,
                    "unauthorized": 0,
                },
                "total_balance": {
                    "authorized": "20000000.00",

                    "authorized_to_maintain_liabilities": "0.0000000",
                    "unauthorized": "0.0000000",
                },
            },
        }
        req_data = self.client.generic(
            method="GET", path=self.URL, content_type="application/json"
        )
        self.assertTrue(req_data.status_code == 200)
        self.assertEqual(req_data.data, mock_totalBal.return_value)

    @patch("Api.views.protocolAssetTotalSupply")
    def test_002_total_balance(self, mock_exception):
        #catch error when for total asset balance endpoint
        mock_exception.side_effect = Exception()
        req_data = self.client.generic(
            method="GET", path=self.URL, content_type="application/json"
        )
        self.assertTrue(req_data.status_code == 404)
        self.assertEqual(req_data.data["error"], "error getting details for this endpoint")
        
