# test deposit to get IFP account for deposits
# test when user reply endpoint of transaction sent
# Test withdrawal from the protocol
# 
import json
from .test_setup import TestSetUpClass, stablecoin, stablecoin_issuer, stablecoin_signer, staking_asset_issuer, staking_asset_code
from django.urls import reverse
from stellar_sdk.keypair import Keypair
from modelApp.models import MerchantsTable
from unittest.mock import patch
from modelApp.models import TransactionsTable
from model_bakery import baker
from utils.utils import Id_generator





class User_Testing(TestSetUpClass):

    # need to add merchant 
    @patch("Api.views.is_Asset_trusted")
    def test_user_deposit(self, mock_requests):
        mock_requests.return_value = [True, 10000]
        self.url = reverse('deposit')
        # use self.client.generic when you need to pass data into your get request
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        # test needs to check for merchant details that is been return
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["amount"] == self.request_data["amount"])
        self.assertTrue(req_data.data["amount_to_pay"] == 1200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    @patch("Api.views.is_Asset_trusted")
    def test_user_deposit_with_invalid_amount(self, mock_trust):
        mock_trust.return_value = [True, 10000]
        self.url = reverse('deposit')
        self.request_data["amount"] = 999.99
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')



    def test_user_deposit_with_invalid_blockchain_address(self):
        self.url = reverse('deposit')
        self.request_data["blockchainAddress"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIP"
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    def test_user_address_has_no_trustline_or_not_created(self):
        self.url = reverse('deposit')
        self.request_data["blockchainAddress"] = Keypair.random().public_key
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    def test_deposit_with_existing_narration(self):
        self.url = reverse('deposit')
        self.client.post(
            self.url, data=self.request_data, format="json")

        new_user_details = {"amount": 1000,
                            "blockchainAddress": "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP",
                            "bankType": "FBN",
                            "narration": "payment for utilities"}
        main_req = self.client.post(
            self.url, data=new_user_details, format="json")



        self.assertEqual(main_req.status_code, 400)
        self.assertTrue("error" in main_req.data)
        self.assertTrue(main_req.headers["Content-Type"] == 'application/json')



        
# ============================================================================
            # test user send payment to merchant
# ============================================================================
    @patch("Api.views.is_Asset_trusted")
    def test_user_made_deposit_to_MA_account_with_correct_details(self, mock_requests):
        mock_requests.return_value =[True, 10000]
        self.url = reverse('deposit')
        post_data = self.client.post(
            self.url, data=self.request_data, format="json")

        deposit_made_to_ma = {
            "memo": post_data.data["memo"],
            "amount": float(post_data.data["amount"]) + float(200),
            "bank_name": "FBN",
            "account_number": "697079895",
            "phone_number": "670074567876",
            "transaction_narration": post_data.data["narration"],
            "blockchain_address": self.request_data["blockchainAddress"]
        }


        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            deposit_made_to_ma), content_type='application/json')

        self.assertTrue(req_data.status_code == 200)
        self.assertTrue(
            req_data.data["message"] == 'Your Blockchain address will credited soon. Thank You')
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    @patch("Api.views.is_Asset_trusted")
    def test_user_made_deposit_to_MA_account_with_invalid_narration(self, mock_requests):
        mock_requests.return_value = [True, 10000]
        self.url = reverse('deposit')

        post_data = self.client.post(
            self.url, data=self.request_data, format="json")
        deposit_made_to_ma = {
            "memo": post_data.data["memo"],
            "amount": float(post_data.data["amount"]) + float(200),
            "bank_name": "FBN",
            "account_number": "697079895",
            "phone_number": "670074567876",
            "transaction_narration": self.random_string(10),
            "blockchainAddress": self.request_data["blockchainAddress"]
        }
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            deposit_made_to_ma), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        

# ============================================================================
        # test user withdrawal flow from the protocol
# ============================================================================

    @patch("Api.views.check_address_balance")
    def test_user_withdrawal_with_asset_not_trusted(self, mock_arg):
        # user withdrawal with no trustline
        mock_arg.return_value =False
        self.url = reverse('withdrawal')
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')

        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
    
    def test_user_withdrawal_with_invalid_blockchain_address(self):
        #withdrawals with invalid Blockchain address
        self.url = reverse('withdrawal')
        self.user_withdrawal["blockchain_address"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIP"
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    def test_user_withdrawal_with_invalid_narration(self):
        #withdrawals with invalid narrations
        self.url = reverse('withdrawal')
        self.user_withdrawal["transaction_narration"] = " "
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    @patch("Api.views.check_address_balance")
    def test_user_withdrawal_with_correct_details(self, mock_balance):
        mock_balance.return_value=True
        #users withdrawals from protocol with correct details

        self.url = reverse('withdrawal')
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("blockchain_address" in req_data.data)
        self.assertTrue("deposit_asset_code" in req_data.data)
        self.assertTrue("deposit_asset_issuer" in req_data.data)
        self.assertTrue("user_details" in req_data.data)
        self.assertEqual(self.user_withdrawal["account_number"], req_data.data["user_details"]["account_number"])
        self.assertEqual(self.user_withdrawal["phone_number"], req_data.data["user_details"]["phone_number"])
        self.assertEqual(self.user_withdrawal["blockchain_address"], req_data.data["user_details"]["blockchain_address"])



# =======================================================================
# TESTING FOR WIDGET/SEP DEPOSIT AND WITHDRAWAL
# =======================================================================

    # need to add merchant 
    @patch("Api.views.TransactionsTable.objects")
    @patch("Api.views.is_Asset_trusted")
    def test_user_deposit_via_widget(self, mock_requests, mock_transaction):
        """
        Test for a successful deposit of transaction through widget
        """
        mock_requests.return_value = [True, 10000]
        self.url = reverse('deposit')
        _id = Id_generator()
        trx = baker.make(TransactionsTable, id=_id, transaction_narration=("sep"+_id))
        mock_transaction.get.return_value = trx
        self.request_data.update({"transaction_source":"sep", "transaction_Id":trx.id})
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["amount"] == self.request_data["amount"])
        self.assertTrue(req_data.data["amount_to_pay"] == 1200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("message" in req_data.data)
        self.assertTrue("memo" in req_data.data)
        self.assertTrue("narration" in req_data.data)
        self.assertTrue("bank_name" in req_data.data)
        self.assertTrue("account_number" in req_data.data)
        self.assertTrue("phoneNumber" in req_data.data)
        self.assertTrue("eta" in req_data.data)

    @patch("Api.views.is_Asset_trusted")
    def test_user_deposit_with_invalid_amount(self, mock_trust):
        mock_trust.return_value = [True, 10000]
        self.url = reverse('deposit')
        self.request_data["amount"] = 999
        self.request_data["transaction_source"] = "sep"
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("error" in req_data.data)

    @patch("Api.views.is_Asset_trusted")
    def test_deposit_with_existing_narration(self, mock_trust):
        mock_trust.return_value = [True, 10000]
        self.url = reverse('deposit')
        _id = Id_generator()
        trx = baker.make(TransactionsTable, id=_id, transaction_narration=("sep"+_id))
        self.request_data.update({"transaction_source":"sep", "transaction_Id":trx.id})
        self.client.post(
            self.url, data=self.request_data, format="json")

        new_user_details = {"amount": 1000,
                            "blockchainAddress": "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP",
                            "bankType": "FBN",
                            "narration": "payment for utilities",
                            "transaction_source":"sep",
                            "transaction_Id":trx.id}
        main_req = self.client.post(
            self.url, data=new_user_details, format="json")
        

        self.assertEqual(main_req.status_code, 400)
        self.assertTrue("error" in main_req.data)
        self.assertTrue(main_req.headers["Content-Type"] == 'application/json')

# TESTING USER WITHDRAWAL

    @patch("Api.views.check_address_balance")
    def test_user_withdrawal_with_asset_not_trusted(self, mock_arg):
        # user withdrawal with no trustline
        mock_arg.return_value =False
        self.url = reverse('withdrawal')
        self.user_withdrawal["transaction_source"] = "sep"
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')

        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
    
    def test_user_withdrawal_with_invalid_blockchain_address(self):
        #withdrawals with invalid Blockchain address
        self.url = reverse('withdrawal')
        self.user_withdrawal["transaction_source"] = "sep"
        self.user_withdrawal["blockchain_address"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIP"
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')


    def test_user_withdrawal_with_invalid_narration(self):
        #withdrawals with invalid narrations
        self.url = reverse('withdrawal')
        self.user_withdrawal["transaction_source"] = "sep"
        self.user_withdrawal["transaction_narration"] = " "
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')

    @patch("Api.views.check_address_balance")
    def test_user_withdrawal_with_correct_details(self, mock_balance):
        mock_balance.return_value=True
        #users withdrawals from protocol with correct details

        self.url = reverse('withdrawal')
        _id = Id_generator()
        trx = baker.make(TransactionsTable, id=_id, transaction_narration=("sep"+_id))
        self.user_withdrawal["transaction_source"] = "sep"
        self.user_withdrawal["transaction_Id"] =trx.id
        req_data = self.client.generic(method="POST", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        print(req_data.json())
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue("blockchain_address" in req_data.data)
        self.assertTrue("deposit_asset_code" in req_data.data)
        self.assertTrue("deposit_asset_issuer" in req_data.data)
        self.assertTrue("user_details" in req_data.data)
        self.assertEqual(self.user_withdrawal["account_number"], req_data.data["user_details"]["account_number"])
        self.assertEqual(self.user_withdrawal["phone_number"], req_data.data["user_details"]["phone_number"])
        self.assertEqual(self.user_withdrawal["blockchain_address"], req_data.data["user_details"]["blockchain_address"])



# add test for widget