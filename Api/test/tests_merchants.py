
import json

from Blockchains.Stellar.operations import get_network_passPhrase
from django.urls import reverse
from modelApp.models import MerchantsTable
from rest_framework import status
from stellar_sdk import Payment, SetTrustLineFlags, TransactionEnvelope
from stellar_sdk.keypair import Keypair

from .test_setup import (TestSetUpClass, allowed_asset, allowed_asset_issuer,
                        license_token, stablecoin, staking_address,
                        staking_asset_code, staking_asset_issuer, license_token_issuer, stablecoin_issuer)

from modelApp.utils import assign_transaction_to_merchant, update_PendingTransaction_Model
class Merchants_Class_Test(TestSetUpClass):

    def test_merchant_with_no_trustline_for_all_assets(self):
        # clean the added user
        present_user = MerchantsTable.objects.get(
                UID=self.created_user.UID)
        present_user.delete()
        self._data["blockchainAddress"] = Keypair.random().public_key
        
        self.url = reverse('onboard')
        response = self.client.post(self.url, self._data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue("assets" in response.data)
        self.assertEquals(len(response.data["assets"]), 3)
        self.assertTrue(response.data["assets"][0]["code"] == allowed_asset)
        self.assertTrue(response.data["assets"][1]["code"] == license_token)
        self.assertTrue(response.data["assets"][2]["code"] == stablecoin)

    def test_onBoardMerchant_all_required_trustline(self):
        present_user = MerchantsTable.objects.get(UID=self.created_user.UID)
        present_user.delete()
        self._data["blockchainAddress"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIPE4XXJYF"
        self.url = reverse('onboard')
        response = self.client.post(self.url, self._data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["staking_address"], staking_address)
        self.assertEqual(response.data["staking_asset_code"], staking_asset_code)
        self.assertEqual(
            response.data["staking_asset_issuer"], staking_asset_issuer)
        self.assertTrue("memo" in response.data)
        self.assertTrue("user_details" in response.data)
        self.assertEquals(response.data["user_details"]["email"], self._data["email"])

# ==========================================================================================
            # Merchant Un-staking from the protocol
# ==========================================================================================

    def test_off_boarding_merchant_with_enough_balance_first_transaction(self):
    
        self.url = reverse('offboard')

        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]

        transactionEnvelop = TransactionEnvelope.from_xdr(xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(len(operations) == 7)
        self.assertTrue(type(operations[0]) == SetTrustLineFlags)
        self.assertTrue(operations[0].trustor == self._ma_data["merchant_PubKey"])
        self.assertTrue(operations[0].asset.code == allowed_asset)
        self.assertTrue(operations[0].asset.issuer == allowed_asset_issuer)
        self.assertTrue(operations[0].clear_flags == 2)
        self.assertTrue(operations[0].set_flags == 1)

        self.assertEqual(req_data.status_code, status.HTTP_200_OK)
        self.assertTrue("raw_xdr" in req_data.data)
        self.assertTrue(req_data.data["message"] == 'Please sign and submit the XDR below to complete the transaction')

    def test_off_boarding_merchant_with_enough_balance_2nd_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]
    
        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[1]) == SetTrustLineFlags)
        self.assertTrue(operations[1].trustor == self._ma_data["merchant_PubKey"])
        self.assertTrue(operations[1].asset.code == license_token)
        self.assertTrue(operations[1].asset.issuer == license_token_issuer)
        self.assertTrue(operations[1].clear_flags == 2)
        self.assertTrue(operations[1].set_flags == 1)


    def test_off_boarding_merchant_with_enough_balance_3rd_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]
    
        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[2]) == Payment)
        self.assertTrue(operations[2].destination.account_id == allowed_asset_issuer)
        self.assertTrue(operations[2].asset.code == allowed_asset)
        self.assertTrue(operations[2].source.account_id == self._ma_data["merchant_PubKey"])
        # not a good way to validate amount
        self.assertTrue(int(operations[2].amount) == 60000)

    def test_off_boarding_merchant_with_enough_balance_4th_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]

        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[3]) == Payment)
        self.assertTrue(
            operations[3].destination.account_id == license_token_issuer)
        self.assertTrue(operations[3].asset.code == license_token)
        self.assertTrue(operations[3].source.account_id ==
                        self._ma_data["merchant_PubKey"])
        # not a good way to validate amount
        self.assertTrue(int(operations[3].amount) == 60000)


    def test_off_boarding_merchant_with_enough_balance_5th_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]
    
        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[5]) == SetTrustLineFlags)
        self.assertTrue(operations[4].trustor == self._ma_data["merchant_PubKey"])
        self.assertTrue(operations[4].asset.code == allowed_asset)
        self.assertTrue(operations[4].asset.issuer == allowed_asset_issuer)
        self.assertTrue(operations[4].clear_flags == 1)
        self.assertTrue(operations[4].set_flags == 2)

    def test_off_boarding_merchant_with_enough_balance_6th_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]

        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[5]) == SetTrustLineFlags)
        self.assertTrue(operations[5].trustor ==
                        self._ma_data["merchant_PubKey"])
        self.assertTrue(operations[5].asset.code == license_token)
        self.assertTrue(operations[5].asset.issuer == license_token_issuer)
        self.assertTrue(operations[5].clear_flags == 1)
        self.assertTrue(operations[5].set_flags == 2)


    def test_off_boarding_merchant_with_enough_balance_7th_transaction(self):
        self._ma_data = {
            "merchant_Id": self.created_user.UID,
            "merchant_PubKey": self.created_user.blockchainAddress
        }
        self.url = reverse('offboard')

        # use self.client.generic when you need to pass data into your get request
        req_data=self.client.generic(method="GET", path=self.url, data= json.dumps(self._ma_data), content_type='application/json')
        xdr_object = req_data.data["raw_xdr"]
    
        transactionEnvelop = TransactionEnvelope.from_xdr(
            xdr_object, get_network_passPhrase())
        operations = transactionEnvelop.transaction.operations
        self.assertTrue(type(operations[6]) == Payment)
        self.assertTrue(operations[6].destination.account_id == self._ma_data["merchant_PubKey"])
        self.assertTrue(operations[6].asset.code == stablecoin)
        self.assertTrue(operations[6].asset.issuer == stablecoin_issuer)
        self.assertTrue(int(operations[6].amount) == 100)
        self.assertTrue(operations[6].source.account_id == staking_address )

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

        for i in range(10):
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
                transaction=transaction_p, merchant=self.created_user.UID)


        self._ma_data = {"merchant_public_key": transaction_p.users_address}
        self.url = reverse('merchants')
        query_params = f"?merchant_public_key={transaction_p.users_address}"
        req_data = self.client.generic(method="GET", path=self.url+query_params, data=json.dumps(
            self._ma_data), content_type='application/json')

        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(len(req_data.data) == 10)

