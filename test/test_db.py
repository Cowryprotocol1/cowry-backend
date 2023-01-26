# write tests for db checks
import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'stablecoin.settings')
django.setup()
from rest_framework.test import APITestCase
from Api.serializers import MerchantsTableSerializer


from modelApp.models import *
from modelApp.utils import get_merchant_by_pubKey
from unittest.mock import patch
# import unittest


class  MerchantTableTest(APITestCase):
    """Test possible operations for the Merchant Db """

    _data = {}

    def setUp(self) -> None:
        print("this is setup")
        self._data["blockchainAddress"] = "GA7TCONR42XF77DDBKBMT2LKQGLS6GK2ZGUQFWHQA7IZLS4LVC6YVKTF"
        self._data["bankName"] = "TestBank222"
        self._data["bankAccount"] = "9098989878"
        self._data["phoneNumber"] = "08054545454"
        self._data["email"] = "testman@gmail.com"
        print("this is done setup")
    
    @patch("modelApp.models.is_account_valid")
    def test_01_add_users(self, mock_validate):
        """Test adding merchants """
        mock_validate.return_value = True

        self.created_user = MerchantsTableSerializer(data=self._data)
        
        if self.created_user.is_valid():
            test_merchant = self.created_user.save()
            TokenTable.objects.create(merchant=test_merchant)

        merchant_object = get_merchant_by_pubKey(self._data["blockchainAddress"])
        self.assertTrue(merchant_object["ifp_block_addr"] == self._data["blockchainAddress"])
        self.assertTrue(merchant_object["ifp_acct_name"] == self._data["bankName"])
        self.assertTrue(merchant_object["ifp_acct_number"] == self._data["bankAccount"])
        self.assertTrue(merchant_object["ifp_phone_name"] == self._data["phoneNumber"])
        self.assertTrue(merchant_object["ifp_email_addr"] == self._data["email"])
        self.assertEqual(merchant_object["allowedTokenAmount"], 0.0)
        self.assertEqual(merchant_object["licenseTokenAmount"], 0.0)
        self.assertEqual(merchant_object["unclear_bal"], 0.0)
        self.assertEqual(merchant_object["stakedTokenAmount"], 0.0)
        self.assertEqual(merchant_object["stakedTokenExchangeRate"], 0.0)
        print("test passed")