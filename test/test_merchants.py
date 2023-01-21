
import json

from Blockchains.Stellar.operations import get_network_passPhrase
from django.urls import reverse
from rest_framework import status
from stellar_sdk import Payment, SetTrustLineFlags, TransactionEnvelope
from stellar_sdk.keypair import Keypair

from test_setup import (TestSetUpClass, allowed_asset, allowed_asset_issuer,
                        license_token, stablecoin, staking_address,
                        staking_asset_code, staking_asset_issuer, license_token_issuer, stablecoin_issuer)

from modelApp.utils import assign_transaction_to_merchant, update_PendingTransaction_Model
from utils.utils import Id_generator
from unittest.mock import patch

class MerchantsTest(TestSetUpClass):

    def test_merchant_with_no_trustline_for_all_assets(self):
        # clean the added user
       
        dummy_data = {}
        dummy_data["blockchainAddress"] = Keypair.random().public_key
        dummy_data["email"] = str(Id_generator())+"@gmail.com"
        dummy_data["bankName"] = "TestBank"
        dummy_data["bankAccount"] = Id_generator()
        dummy_data["phoneNumber"] = "08011122333"
        print(dummy_data)
        
        self.url = reverse('onboard')
        response = self.client.post(self.url, dummy_data)
        print(response.json())
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(response.headers["Content-Type"] == 'application/json')
        self.assertTrue("assets" in response.data)
        self.assertEquals(len(response.data["assets"]), 3)
        self.assertTrue(response.data["assets"][0]["code"] == allowed_asset)
        self.assertTrue(response.data["assets"][1]["code"] == license_token)
        self.assertTrue(response.data["assets"][2]["code"] == stablecoin)
        
    @patch("modelApp.models.is_account_valid")
    @patch("Api.views.is_Asset_trusted")
    def test_onBoardMerchant_all_required_trustline(self, mock_trust, mock_validator):
        #with python mock, you can mock any complex logic together, but always try to mock the simplest ones, the ones that return true or false
        mock_trust.return_value = [True, 10000]
        mock_validator.return_value =True
        dummy_data = {}
        dummy_data["blockchainAddress"] = Keypair.random().public_key
        dummy_data["email"] = str(Id_generator())+"@gmail.com"
        dummy_data["bankName"] = "TestBank"
        dummy_data["bankAccount"] = Id_generator()
        dummy_data["phoneNumber"] = "08011122333"
        self.url = reverse('onboard')
        response = self.client.post(self.url, dummy_data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.headers["Content-Type"] == 'application/json')
        self.assertEqual(response.data["staking_address"], staking_address)
        self.assertEqual(response.data["staking_asset_code"], staking_asset_code)
        self.assertEqual(
            response.data["staking_asset_issuer"], staking_asset_issuer)
        self.assertTrue("memo" in response.data)
        self.assertTrue("user_details" in response.data)
        self.assertEquals(response.data["user_details"]["email"], dummy_data["email"])

# ==========================================================================================
            # Merchant Un-staking from the protocol
# ==========================================================================================
    @patch("Api.views.OffBoard_Merchant_with_Burn")
    def test_off_boarding_merchant_with_enough_balance_first_transaction(self, mock_OffBoard_Merchant):
        mock_OffBoard_Merchant.return_value = "AAAAAgAAAAAhlKjAPKavhXFwhsI31_not_a_valid_xdr"
    
        self.url = reverse('offboard')

        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        self.assertEqual(req_data.status_code, status.HTTP_200_OK)
        self.assertTrue("raw_xdr" in req_data.data)
        self.assertTrue(
            req_data.data["message"] == 'Please sign and submit the XDR below within 30min to complete the transaction')
        

    def test_merchant_with_no_arguments(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
        
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
    

        self.assertEqual(req_data.status_code, 400)
        self.assertTrue("error" in req_data.data)
        self.assertTrue("merchant_PubKey" in req_data.data['error'])
    

# ==========================================================================================
        # Test for getting list of all merchant pending transactions
# ==========================================================================================

    def test_get_all_merchant_pending_transactions_with_invalid_parament(self):

        self._ma_data = {}
        self.url = reverse('merchants')
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self._ma_data), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)



    def test_get_all_merchant_pending_transactions_with_valid_parament(self):

        # for i in range(10):
        transaction_p = update_PendingTransaction_Model(
            transaction_amt=self.user_withdrawal["amount"],
            transaction_type='withdraw',
            transaction_hash=None,
            user_block_address=self.created_user.blockchainAddress,
            phone_num=self.user_withdrawal["phone_number"],
            user_bank_account=self.user_withdrawal["account_number"],
            bank_name=self.user_withdrawal["bank_name"],
            narration=self.random_string(10),

        )
        transaction_p.save()
        assign_transaction_to_merchant(
            transaction=transaction_p, merchant=self.created_user.UID, amount=self.user_withdrawal["amount"])


        self._ma_data = {"merchant_public_key": transaction_p.users_address}
        self.url = reverse('merchants')
        query_params = f"?public_key={transaction_p.users_address}&query_type=ifp"
        req_data = self.client.generic(method="GET", path=self.url+query_params, data=json.dumps(
            self._ma_data), content_type='application/json')

        query_params_user = f"?public_key={transaction_p.users_address}&query_type=user"
        req_data_user = self.client.generic(method="GET", path=self.url+query_params_user, data=json.dumps(
            self._ma_data), content_type='application/json')

        # print(req_data.json()['all_transactions'])

        self.assertEqual(req_data.status_code, 200)
        self.assertEqual(req_data_user.status_code, 200)
        self.assertTrue(len(req_data.json()["all_transactions"]) == 1)
        self.assertTrue(len(req_data_user.json()["all_transactions"]) == 1)

    

