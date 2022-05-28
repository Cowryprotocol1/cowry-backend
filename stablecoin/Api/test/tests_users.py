# test deposit to get IFP account for deposits
# test when user reply endpoint of transaction sent
# Test withdrawal from the protocol
# 
import json
from .test_setup import TestSetUpClass
from django.urls import reverse
from stellar_sdk.keypair import Keypair




class User_Testing(TestSetUpClass):
    # need to add merchant 
    def test_user_deposit(self):
    
        self.url = reverse('deposit')
        # use self.client.generic when you need to pass data into your get request
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        # test needs to check for merchant details that is been return
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["amount"] == self.request_data["amount"])
        self.assertTrue(req_data.data["amount_to_pay"] == 1200)

    def test_user_deposit_with_invalid_amount(self):
        self.url = reverse('deposit')
        self.request_data["amount"] = 999.99
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)


    def test_user_deposit_with_invalid_blockchain_address(self):
        self.url = reverse('deposit')
        self.request_data["blockchainAddress"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIP"
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)

    def test_user_address_has_no_trustline_or_not_created(self):
        self.url = reverse('deposit')
        self.request_data["blockchainAddress"] = Keypair.random().public_key
        req_data = self.client.post(self.url, data=self.request_data, format="json")
        self.assertEqual(req_data.status_code, 400)

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


        
# ============================================================================
            # test user send payment to merchant
# ============================================================================
    def test_user_made_deposit_to_MA_account_with_correct_details(self):
        self.url = reverse('deposit')
        post_data = self.client.post(
            self.url, data=self.request_data, format="json")

        deposit_made_to_ma = {
            "memo": post_data.data["memo"],
            "amount": float(post_data.data["amount"]) + float(200),
            "bank_name": "FBN",
            "acct_number": "697079895",
            "phone_number": "670074567876",
            "narration": post_data.data["narration"],
            "blockchainAddress": self.request_data["blockchainAddress"]
        }


        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            deposit_made_to_ma), content_type='application/json')

        self.assertTrue(req_data.status_code == 200)
        self.assertTrue(
            req_data.data["message"] == 'Your Blockchain address will credited soon. Thank You')

    

    def test_user_made_deposit_to_MA_account_with_invalid_narration(self):
    
        self.url = reverse('deposit')

        post_data = self.client.post(
            self.url, data=self.request_data, format="json")
        deposit_made_to_ma = {
            "memo": post_data.data["memo"],
            "amount": float(post_data.data["amount"]) + float(200),
            "bank_name": "FBN",
            "acct_number": "697079895",
            "phone_number": "670074567876",
            "narration": self.random_string(10),
            "blockchainAddress": self.request_data["blockchainAddress"]
        }
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            deposit_made_to_ma), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        

# ============================================================================
        # test user withdrawal flow from the protocol
# ============================================================================

    def test_user_withdrawal_with_asset_not_trusted(self):
        self.url = reverse('withdrawal')
        self.user_withdrawal["blockchain_address"] = self.create_a_valid_blockchain_account()
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)
        
        pass
    def test_user_withdrawal_with_invalid_blockchain_address(self):
        self.url = reverse('withdrawal')
        self.user_withdrawal["blockchain_address"] = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIP"
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)

    def test_user_withdrawal_with_invalid_narration(self):
        self.url = reverse('withdrawal')
        self.user_withdrawal["transaction_narration"] = " "
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 400)

    def test_user_withdrawal_with_correct_details(self):
        self.url = reverse('withdrawal')
        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            self.user_withdrawal), content_type='application/json')
        self.assertEqual(req_data.status_code, 200)





        



