# Used for reseting testing account 
# All merchants account should be created onchain
# 1.Merchants account shpuld have trustline for NGN, NGNALLOWED, LINCENSE tokens, USDC
# merchants account should be funded with test USDC for onboarding

# all users account should be created onchain
# all users account should have trusline for NGN

from decouple import config as env_getter
from stellar_sdk.server import Server
from stellar_sdk.network import Network
from stellar_sdk.keypair import Keypair
from stellar_sdk.transaction_builder import TransactionBuilder
from stellar_sdk.asset import Asset
class TestingAccountReset:
    """used to reset testnet testing account to on testnet"""
    Keys_to_create ={}

    STABLEASSET = Asset(env_getter("STABLECOIN_CODE"), env_getter("STABLECOIN_ISSUER"))
    ALLOWEDASSET = Asset(env_getter("ALLOWED_TOKEN_CODE"), env_getter("ALLOWED_AND_LICENSE_P_ADDRESS"))
    license_Asset = Asset(env_getter("LICENSE_TOKEN_CODE"), env_getter("ALLOWED_AND_LICENSE_P_ADDRESS"))
    USDC_ASSET = Asset(env_getter("STAKING_TOKEN_CODE"), env_getter("STAKING_TOKEN_ISSUER"))
    USDC_SIGNER = env_getter("USDC_TESTING_SIGNER")


    def __init__(self) -> None:

        self.server = Server("https://horizon-testnet.stellar.org")
        self._networkPassPhrase = Network.TESTNET_NETWORK_PASSPHRASE
        
        self.Keys_to_create["account1"] = env_getter("account1")
        self.Keys_to_create["account2"] = env_getter("account2")
        self.Keys_to_create["account3"] = env_getter("account3")
        self.Keys_to_create["users1"] = env_getter("users1")
        self.Keys_to_create["users2"] = env_getter("users2")
        self.Keys_to_create["users3"] = env_getter("users3")
        
        for i in range(len(self.Keys_to_create)):
            _keys = list(self.Keys_to_create.values())[i]
            pub_key = Keypair.from_secret(_keys).public_key
            print(pub_key)
            req = self.create_a_valid_blockchain_account(pub_key)
            print(f"{req} successfully created ")
        # add trustlines to accounts

        print("adding trustlines for Merchants")
        self.add_trustline(self.ALLOWEDASSET, self.Keys_to_create["account1"])
        self.add_trustline(self.ALLOWEDASSET, self.Keys_to_create["account2"])
        self.add_trustline(self.ALLOWEDASSET, self.Keys_to_create["account3"])
        print("Allowed Asset successfully added to merchant accounts")

        self.add_trustline(self.license_Asset, self.Keys_to_create["account1"])
        self.add_trustline(self.license_Asset, self.Keys_to_create["account2"])
        self.add_trustline(self.license_Asset, self.Keys_to_create["account3"])
        print("License Asset successfully added to merchant accounts")

        self.add_trustline(self.STABLEASSET, self.Keys_to_create["account1"])
        self.add_trustline(self.STABLEASSET, self.Keys_to_create["account2"])
        self.add_trustline(self.STABLEASSET, self.Keys_to_create["account3"])
        print("Stable Asset successfully added to merchant accounts")

        self.add_trustline(self.USDC_ASSET, self.Keys_to_create["account1"])
        self.add_trustline(self.USDC_ASSET, self.Keys_to_create["account2"])
        self.add_trustline(self.USDC_ASSET, self.Keys_to_create["account3"])
        print("Stable Asset successfully added to merchant accounts")

        print("adding assets to users account")
        self.add_trustline(self.STABLEASSET, self.Keys_to_create["users1"])
        self.add_trustline(self.STABLEASSET, self.Keys_to_create["users2"])
        self.add_trustline(self.STABLEASSET, self.Keys_to_create["users3"])
        print("Stable Asset successfully added to users accounts")

        print("sending testnet USDC to merchant")
        self.send_payment(self.USDC_ASSET, Keypair.from_secret(self.Keys_to_create["account1"]).public_key, str(1000), self.USDC_SIGNER)
        self.send_payment(self.USDC_ASSET, Keypair.from_secret(self.Keys_to_create["account2"]).public_key, str(1000), self.USDC_SIGNER)
        self.send_payment(self.USDC_ASSET, Keypair.from_secret(self.Keys_to_create["account3"]).public_key, str(1000), self.USDC_SIGNER)
        print("payment successfully send to merchants")




    def create_a_valid_blockchain_account(self, pub_key: str):
        import requests
        url = "https://friendbot.stellar.org"
        response = requests.get(url, params={"addr": pub_key})
        if response.status_code == 200:
            return pub_key
        elif response.status_code == 500:
            raise ValueError("seems account has been created")

    def add_trustline(self, _asset, signer: str):
        """
        Function to add trustline to an account
        """
        # stablecoin address adds trustline to ALLOWED NGN
        # protocol address adds trustline to NGN
        userKeyPair = Keypair.from_secret(signer)
        fee = self.server.fetch_base_fee()
        src_account = self.server.load_account(userKeyPair.public_key)
        trustlineOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=self._networkPassPhrase,
            base_fee=fee).append_change_trust_op(_asset).set_timeout(30).build()
        trustlineOp.sign(signer)

        submitted_trustlineOp = self.server.submit_transaction(trustlineOp)
        return submitted_trustlineOp


    def send_payment(self, _asset, destination_addr: str, amt: str, signer: str) -> str:
        _sender_keypair = Keypair.from_secret(signer)
        src_account = self.server.load_account(_sender_keypair.public_key)
        paymentOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=self._networkPassPhrase,
            base_fee=self.server.fetch_base_fee()
        ).append_payment_op(destination=destination_addr, amount=str(amt), asset=_asset, source=_sender_keypair.public_key
                            ).set_timeout(30).build()
        paymentOp.sign(_sender_keypair)
        submitTx = self.server.submit_transaction(paymentOp)

        return submitTx


        




if __name__ == "__main__":
    adc = TestingAccountReset()
    print(adc)
