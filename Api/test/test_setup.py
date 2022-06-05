import logging
from decouple import config

from rest_framework.test import APITestCase
from modelApp.models import MerchantsTable, TokenTable
from stellar_sdk.keypair import Keypair
import requests
from stellar_sdk import TransactionBuilder, Asset, Server, Network




staking_address = config('STAKING_ADDRESS')
staking_asset_code = config('STAKING_TOKEN_CODE')
staking_asset_issuer = config('STAKING_TOKEN_ISSUER')

allowed_asset = config('ALLOWED_TOKEN_CODE')
allowed_asset_issuer = config('ALLOWED_AND_LICENSE_P_ADDRESS')


license_token = config('LICENSE_TOKEN_CODE')
license_token_issuer = config('ALLOWED_AND_LICENSE_P_ADDRESS')

stablecoin = config('STABLECOIN_CODE')
stablecoin_issuer = config("STABLECOIN_ISSUER")
stablecoin_signer = config('PROTOCOL_SIGNER')

ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER = config(
    "ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER")

server = Server("https://horizon-testnet.stellar.org")
_networkPassPhrase = Network.TESTNET_NETWORK_PASSPHRASE

# merchant_keypair = Keypair.random()
# general_keypair = Keypair.random()

merchant_keypair = Keypair.from_secret(
    "SALS3ZKWQPXAR42KA4X553H7ENMW2PY4X6ZHFB2I3JIZ3XQUH7DPBO63")


general_keypair = Keypair.from_secret(
    "SADG5LRJS6QONXL4JTAECMM34SSJANUZNRODYSIXGJCRJ7SKKRZNMY43")


USDC_TESTING = Keypair.from_secret(
    "SBPXIPQPTMHAJZ5NHMJPNEO34OEF5DKBYBFTUHMKUALK5IS2A6PSW3LH")



# print(merchant_keypair.public_key)

def send_payment(asset_code: str, asset_issuer: str, destination_addr: str, amt: str, src_acct:str, signer: str) -> str:
    _sender_keypair = Keypair.from_secret(signer)
    src_account = server.load_account(src_acct)

    paymentOp = TransactionBuilder(
        source_account=src_account,
        network_passphrase=_networkPassPhrase,
        base_fee=server.fetch_base_fee()
    ).append_payment_op(destination=destination_addr, amount=str(amt), asset=Asset(code=asset_code, issuer=asset_issuer), source=_sender_keypair.public_key
                        ).set_timeout(30).build()
    paymentOp.sign(_sender_keypair)
    submitTx = server.submit_transaction(paymentOp)

    return submitTx


def create_a_valid_blockchain_account(pub_key):
    url = "https://friendbot.stellar.org"

    response = requests.get(url, params={"addr": pub_key})
    if response.status_code == 200:
        return pub_key
    raise Exception("Error creating a valid blockchain account")

def add_trustline(asset_code: str, asset_issuer: str, signer: str):
        """
        Function to add trustline to an account
        """
        # stablecoin address adds trustline to ALLOWED NGN
        # protocol address adds trustline to NGN
        userKeyPair = Keypair.from_secret(signer)
        fee = server.fetch_base_fee()
        src_account = server.load_account(userKeyPair.public_key)
        trustlineOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=_networkPassPhrase,
            base_fee=fee).append_change_trust_op(Asset(code=asset_code, issuer=asset_issuer)).set_timeout(30).build()
        trustlineOp.sign(signer)

        submitted_trustlineOp = server.submit_transaction(trustlineOp)
        return submitted_trustlineOp
    

# payments_ops = send_payment(stablecoin, stablecoin_issuer,
#                             general_keypair.public_key, 1000, stablecoin_issuer, stablecoin_signer)
# print(payments_ops)

# try:
#     create_a_valid_blockchain_account(merchant_keypair.public_key)
# except Exception:
#     print("All account seems to be created")
# else:
#     create_a_valid_blockchain_account(general_keypair.public_key)

#     logging.info("********** Both account are created successfully **********")

#     add_trustline(allowed_asset, allowed_asset_issuer, general_keypair.secret)
#     add_trustline(license_token, license_token_issuer, general_keypair.secret)
#     add_trustline(stablecoin, stablecoin_issuer, general_keypair.secret)
#     add_trustline(staking_asset_code, staking_asset_issuer, general_keypair.secret)

#     logging.info("********** Trustlines added on the General account **********")

#     add_trustline(allowed_asset, allowed_asset_issuer, merchant_keypair.secret)
#     add_trustline(license_token, license_token_issuer, merchant_keypair.secret)
#     add_trustline(stablecoin, stablecoin_issuer, merchant_keypair.secret)
#     add_trustline(staking_asset_code, staking_asset_issuer, merchant_keypair.secret)

#     logging.info("********** Trustlines added on the merchant account **********")


    # payments_ops = send_payment(staking_asset_code, staking_asset_issuer,
    #                                 general_keypair.public_key, 1000, USDC_TESTING.public_key, USDC_TESTING.secret)


    # payments_ops_2 = send_payment(stablecoin, stablecoin_issuer,
    #                         general_keypair.public_key, 1000, stablecoin_issuer, stablecoin_signer)
    # print(payments_ops)




class TestSetUpClass(APITestCase):



    def setUp(self):
        self._data = {}
        self._data["bankName"] = "Wema"
        self._data["bankAccount"] = "9098989878"
        self._data["phoneNumber"] = "08054545454"
        self._data["email"] = "testman@gmail.com"
        self.merchant_keypair = merchant_keypair
        self.general_keypair = general_keypair
        self.server = Server("https://horizon-testnet.stellar.org")
        self._networkPassPhrase = Network.TESTNET_NETWORK_PASSPHRASE


        # creating a new user instance
        self.created_user = MerchantsTable.objects.create(email=self._data)
        self.created_user.blockchainAddress = self.merchant_keypair.public_key
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
            "blockchainAddress": self.general_keypair.public_key,
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
            "blockchainAddress": self.general_keypair.public_key
        }

        self.user_withdrawal = {
            "amount": 1000,
            "bank_name": "FBN",
            "account_number": 9078568456,
            "name_on_acct": "test man",
            "phone_number": "09067589358",
            "blockchain_address": self.general_keypair.public_key,
            "transaction_narration": "withdraw 7747"
        }


    def tearDown(self):
        pass

    def random_string(self, length):
        import random
        import string
        return ''.join(random.choice(string.ascii_lowercase) for i in range(length))

    def create_a_valid_blockchain_account(self):
        keypair = Keypair.random()
        pub_key = keypair.public_key
        url = "https://friendbot.stellar.org"

        response = requests.get(url, params={"addr": pub_key})
        if response.status_code == 200:
            return pub_key
        raise Exception("Error creating a valid blockchain account")

    def send_payment(self, asset_code: str, asset_issuer: str, destination_addr: str, amt: str, signer: str, _memo=None) -> str:
        _sender_keypair = Keypair.from_secret(signer)
        src_account = self.server.load_account(_sender_keypair.public_key)

        paymentOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=self._networkPassPhrase,
            base_fee=server.fetch_base_fee()
        ).add_text_memo(memo_text=_memo
        ).append_payment_op(destination=destination_addr, amount=str(amt), asset=Asset(code=asset_code, issuer=asset_issuer), source=_sender_keypair.public_key
                            ).set_timeout(30).build()
        paymentOp.sign(_sender_keypair)
        submitTx = server.submit_transaction(paymentOp)

        return submitTx

   
