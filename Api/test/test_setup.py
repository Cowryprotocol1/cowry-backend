from decouple import config

from rest_framework.test import APITestCase
from modelApp.models import MerchantsTable, TokenTable
from stellar_sdk.keypair import Keypair


staking_address = config('STAKING_ADDRESS')
staking_asset_code = config('STAKING_TOKEN_CODE')
staking_asset_issuer = config('STAKING_TOKEN_ISSUER')
allowed_asset = config('ALLOWED_TOKEN_CODE')
allowed_asset_issuer = config('ALLOWED_AND_LICENSE_P_ADDRESS')
license_token = config('LICENSE_TOKEN_CODE')
license_token_issuer = config('ALLOWED_AND_LICENSE_P_ADDRESS')
stablecoin = config('STABLECOIN_CODE')
stablecoin_issuer = config("STAKING_TOKEN_ISSUER")


class TestSetUpClass(APITestCase):
    def setUp(self):
        self._data = {}
        self._data["bankName"] = "Wema"
        self._data["bankAccount"] = "9098989878"
        self._data["phoneNumber"] = "08054545454"
        self._data["email"] = "testman@gmail.com"

        # creating a new user instance
        self.created_user = MerchantsTable.objects.create(email=self._data)
        self.created_user.blockchainAddress = "GBXR3CBYCDW63FCPH3TCDTLS54S73JU6SDDTZAMCXPCXCNRIPE4XXJYF"
        self.created_user.bankName = "Wema"
        self.created_user.bankAccount = "9098989878"
        self.created_user.phoneNumber = "08054545454"
        self.created_user.email = "testman@gmail.com"
        self.created_user.save()

        # update merchant token balance
        self.tokenBalance = TokenTable.objects.create(merchant=self.created_user)
        self.tokenBalance.stakedTokenAmount = 100
        self.tokenBalance.allowedTokenAmount = 60000
        self.tokenBalance.licenseTokenAmount = 60000
        self.tokenBalance.stakedTokenExchangeRate = 600
        self.tokenBalance.unclear_bal = 0
        self.tokenBalance.save()
        
        self.request_data = {
            "amount": 1000,
            "blockchainAddress": "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP",
            "bankType": "FBN",
            "narration": "payment for utilities"
        }

        self.deposit_made_to_ma = {
            "memo": "db2835d966344ea3f99a",
            "amount": 1000,
            "bank_name": "FBN",
            "acct_number": "697079895",
            "phone_number": "670074567876",
            "narration": "payment for utilities",
            "blockchainAddress": "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP"
        }

        self.user_withdrawal = {
            "amount": 10000,
            "bank_name": "FBN",
            "account_number": 9078568456,
            "name_on_acct": "test man",
            "phone_number": "09067589358",
            "blockchain_address": "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP",
            "transaction_narration": "withdraw 7747"
        }

    def tearDown(self):
        pass

    def random_string(self, length):
        import random
        import string
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

    def create_a_valid_blockchain_account(self):
        import requests
        keypair = Keypair.random()
        pub_key = keypair.public_key

        url = "https://friendbot.stellar.org"

        response = requests.get(url, params={"addr": pub_key})
        if response.status_code == 200:
            return pub_key
        raise Exception("Error creating a valid blockchain account")
