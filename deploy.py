# from stellar_sdk import
import logging
from typing import TypeVar
from decouple import config
from stellar_sdk import Keypair, Asset, Signer, AuthorizationFlag, TransactionBuilder, Network, Server, Account, Transaction
from stellar_sdk.exceptions import BadRequestError, BaseHorizonError

XDR = TypeVar('XDR')
domain = config("COWRY_DEFAULT_DOMAIN")
print(domain)

class Deployment():
    """
    script to deploy to mainnet.
    1. Create all account
    2. Add trustlines to All accounts
    3. setup assets and their flags(NGN, ALLOWED, LICENSE)
    4. place manage buy/sell order for NGN
    5. set up domain using set_option
    6. Setup signature and their weight
    7. 
    """

    def __init__(self, _horizon_network, _genesis_signer="SAZ2I2EAO44MNY7OUBV2ONR22OSNWU2LW4AFVYLKFB2A7RZR7B5AJZHI",) -> None:
        self.Keys_to_create = {}
        self.NETWORK = _horizon_network
        self.Genesis_acct = _genesis_signer

      

        if self.NETWORK == "testnet":
            self.server = Server("https://horizon-testnet.stellar.org")
            self._networkPassPhrase = Network.TESTNET_NETWORK_PASSPHRASE
            self.Keys_to_create["STAKING_ADDRESS_SIGNER"] = config("STAKING_ADDRESS_SIGNER")
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"] = config("ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER")
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"] = config("STABLECOIN_ASSET_SIGNER")
            self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"] = config("DELEGATED_SIGNER_ADDRESS")
            self.Keys_to_create["PROTOCOL_SIGNER"] = config("PROTOCOL_SIGNER")
            self.Keys_to_create["USDC_TESTING"] = config("USDC_TESTING_SIGNER")
            # try:

            gen_pub = Keypair.from_secret(self.Genesis_acct)
            self.create_account_with_friendBot(gen_pub.public_key)
            # except 

        elif self.NETWORK == "mainnet":
            # self.Keys_to_create["STAKING_ADDRESS_SIGNER"] = Keypair.random().secret
            # self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"] = Keypair.random().secret
            # self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"] = Keypair.random().secret
            # self.Keys_to_create["PROTOCOL_SIGNER"] = Keypair.random().secret
            # self.Keys_to_create["STABLECOIN_ASSET_SIGNER"] = Keypair.random().secret
            # self.server = Server("https://horizon.stellar.org")
            # self._networkPassPhrase = Network.PUBLIC_NETWORK_PASSPHRASE
            logging.critical("This is a public network, you need to comment out some lines in the code")
            raise Exception("This is the mainnet, seems you forgot to comment out some lines in the code")
        elif self.NETWORK == "Testing":
            print("Testing")
            # self.server = Server("https://horizon-testnet.stellar.org")
            # self._networkPassPhrase = Network.TESTNET_NETWORK_PASSPHRASE
            # self.Keys_to_create["STAKING_ADDRESS_SIGNER"] = "SDFFBZUP3U2VCOI2LJN354GOSFCBL3ZVLGFWG4DDHUVL67XCZAD72TMB"
            # self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"] = "SC5HTPDFAYWCA23FDWG543WPQFYEKMIEBVWGZMI65GXLVQ3DMDXP2I4K"
            # self.Keys_to_create["STABLECOIN_ASSET_SIGNER"] = "SCHLSJTQI2XT2BUCBUNHY7BIXSUKSFY6ILR5DFWXBA7SDMRAY4VCQ7PO"
            # self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"] = "SDUJZ2YNADC6IJC4IB3AB63TDPQCMKX6RT622H3RG2NZWDXK6CIJWYDJ"
            # self.Keys_to_create["PROTOCOL_SIGNER"] = "SDQD6F7MFYGEIMH4SZZAV4E5FNQKTCPJ7FSXOIMRLN4AODEH4VWNBQDA"
            # self.Keys_to_create["USDC_TESTING"] = "SCYQ6OEGJJ4I44AZEYXZRSIGBYXGUNOIS3PSU53QGQ7LAWI67RYYKF6B"

        self.genesis_signer = Keypair.from_secret(
            self.Genesis_acct)

       

        # create account
        # set authorizationflags
        # add trustline of assets
        # create assets - send 100 to the protocol address
        
        print(self.Keys_to_create)


    def startSetUP(self):
        # setting up all accounts
        acct = self.create_account()
        print("All accounts have been created", acct)

        print("************************************************************************************************************************")
        # creating all assets for protocol
        ngn_asset = self.create_asset("NGN", Keypair.from_secret(
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"]).public_key)
        allowed_asset = self.create_asset("NGNALLOW",   Keypair.from_secret(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key)
        license_asset = self.create_asset("NGNLICENSE", Keypair.from_secret(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key)

        usdc_testing = self.create_asset("USDC", Keypair.from_secret(
            self.Keys_to_create["USDC_TESTING"]).public_key)

        print("All protocol asset created ", {"ngn_asset": {"code": ngn_asset.code, "issuer": ngn_asset.issuer}, "allowed_asset": {
                    "code": allowed_asset.code, "issuer": allowed_asset.issuer}, "license_asset": {"code": license_asset.code, "issuer": license_asset.issuer}, "usdc_testing": {"code": usdc_testing.code, "issuer": usdc_testing.issuer}})
        
        print("************************************************************************************************************************")
        # adding trustline to asset for both allowed on stablecoin_address and for stablecoin on protocol_address
        trustline_for_allowed_on_stablecoin = self.add_trustline(
            allowed_asset.code, allowed_asset.issuer, self.Keys_to_create["STABLECOIN_ASSET_SIGNER"])
        print("trustline for allowed on stablecoin created with this hash", trustline_for_allowed_on_stablecoin["hash"])

        trustline_for_ngn_on_protocol_addr = self.add_trustline(
            ngn_asset.code, ngn_asset.issuer, self.Keys_to_create["PROTOCOL_SIGNER"])
        print("trustline for ngn on protocol addr created with this hash ", trustline_for_ngn_on_protocol_addr["hash"])
        

        trustline_for_ngn_on_staking_address = self.add_trustline(
            usdc_testing.code, usdc_testing.issuer, self.Keys_to_create["STAKING_ADDRESS_SIGNER"])
        print("trustline for ngn on staking address created with this hash ", trustline_for_ngn_on_staking_address["hash"])


        print("************************************************************************************************************************")
        # adding trustline to genesis address
        ngn_trustline_genesis = self.add_trustline(
            ngn_asset.code, ngn_asset.issuer,  self.genesis_signer.secret)
        print("trustline for ngn on genesis addr created ", ngn_trustline_genesis["hash"])
        
        allowed_trustline_genesis = self.add_trustline(
            allowed_asset.code, allowed_asset.issuer, self.genesis_signer.secret)
        print("trustline for allowed on genesis addr ", allowed_trustline_genesis["hash"])

        license_trustline_genesis = self.add_trustline(
            license_asset.code, license_asset.issuer,  self.genesis_signer.secret)
        print("trustline for license on genesis addr ", license_trustline_genesis["hash"])
        

        usdc_trustline_genesis = self.add_trustline(
            usdc_testing.code, usdc_testing.issuer,  self.genesis_signer.secret)

        print("trustline for license on genesis addr ", usdc_trustline_genesis["hash"])

        print("************************************************************************************************************************")
        #creating assets by sending payment tx
        genesis_ngn_payment = self.send_payment(
            ngn_asset.code, ngn_asset.issuer,   self.genesis_signer.public_key, "10", self.Keys_to_create["STABLECOIN_ASSET_SIGNER"])
        print("payment for ngn on genesis addr ", genesis_ngn_payment["hash"])
        
        genesis_allow_payment = self.send_payment(allowed_asset.code, allowed_asset.issuer,
                                                self.genesis_signer.public_key, "10", self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"])
        print("payment for allowed on genesis addr ", genesis_allow_payment["hash"])
        
        genesis_ngnLicense_payment = self.send_payment(license_asset.code, license_asset.issuer,
                                                self.genesis_signer.public_key, "10", self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"])

        print("payment for license on genesis addr ", genesis_ngnLicense_payment["hash"])
        
        genesis_usdc_payment = self.send_payment(usdc_testing.code, usdc_testing.issuer,
                                                self.genesis_signer.public_key, "10", self.Keys_to_create["USDC_TESTING"])
        
        print("payment for USDC on genesis addr ", genesis_usdc_payment["hash"])


        print("************************************************************************************************************************")
        # clear payment send by sending payment back to respective issuers
        license_clear_payment = self.send_payment(license_asset.code, license_asset.issuer,    Keypair.from_secret(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key, "10", self.genesis_signer.secret)
        print("clear payment for license on genesis addr ", license_clear_payment["hash"])
        
        allowed_clear_payment = self.send_payment(allowed_asset.code, allowed_asset.issuer,    Keypair.from_secret(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key, "10", self.genesis_signer.secret)
        print("clear payment for allowed on genesis addr ", allowed_clear_payment["hash"])
        
        ngn_clear_payment = self.send_payment(ngn_asset.code, ngn_asset.issuer,            Keypair.from_secret(
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"]).public_key, "10", self.genesis_signer.secret)
        print("clear payment for ngn on genesis addr ", ngn_clear_payment["hash"])
        
        usdc_clear_payment = self.send_payment(usdc_testing.code, usdc_testing.issuer,            Keypair.from_secret(
            self.Keys_to_create["USDC_TESTING"]).public_key, "10", self.genesis_signer.secret)

        print("clear payment for USDC on genesis addr ", usdc_clear_payment["hash"])

        print("************************************************************************************************************************")
        # setting flags for NGNLICENSE and NGNALLOWED token
        flags_added = self.set_flags_authorization_on_an_address(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"])
        print("set flags on allowed and license token address", flags_added["hash"])

        print("************************************************************************************************************************")
        # place order for NGN-NGNALLOWED token
        order_transaction = self.place_buy_order_for_token_against_another_token(
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"], allowed_asset.code, allowed_asset.issuer, "922337203685", ngn_asset.code, ngn_asset.issuer, "1")
        print("order placed for ngn against allowed", order_transaction["hash"])

        print("************************************************************************************************************************")
        # adding domain to stellar 
        add_domain = self.add_domain_to_stellar()
        print(add_domain)
        logging.info("Asset Domain successfully added")

        print("************************************************************************************************************************")
        # setting up multisig on all addresses
        setup_dao_structure = self.setUp_signature_weight()
        print("setup dao structure", setup_dao_structure["hash"])



    def create_a_valid_blockchain_account(self, pub_key: str):
        signer_keypair = Keypair.from_secret(self.Genesis_acct)
        base_fee = self.server.fetch_base_fee()

        transaction = (TransactionBuilder(
            
            source_account=self.server.load_account(
                self.genesis_signer.public_key),
            base_fee=base_fee,
            network_passphrase=self._networkPassPhrase,
        ).add_text_memo("created Accounts"
        ).append_create_account_op(destination=pub_key, starting_balance="10", source=signer_keypair.public_key
        ).set_timeout(30).build())

        transaction.sign(signer_keypair)
        submitted_tx = self.server.submit_transaction(transaction)
        return submitted_tx
        # print(pub_key, "Has been successfully created")

    def create_account(self) -> XDR:
        """
        Function to create account on testnet
        The Genesis address is used to create these accounts
        Genesis address must be an already created address with at least 110 XLM
        """
        for i in range(len(self.Keys_to_create)):
            _value = list(self.Keys_to_create.values())[i]
            pub_key = Keypair.from_secret(_value).public_key
            try:
                create = self.create_a_valid_blockchain_account(pub_key)
            except BadRequestError:
                print("Address already created")
            # print(create)
            else:
                _keys = list(self.Keys_to_create.keys())[i]
                print({_keys:pub_key}, "Has been successfully created")
        # pass

    def set_flags_authorization_on_an_address(self, signer: str):
        """This add restriction to asset issue by the account, this is set on the allowed and license address"""
        _asset_issuer_keypair = Keypair.from_secret(signer)
        src_acct = self.server.load_account(_asset_issuer_keypair.public_key)

        tx = TransactionBuilder(
            source_account=src_acct,
            base_fee=self.server.fetch_base_fee(),
            network_passphrase=self._networkPassPhrase
        ).append_set_options_op(set_flags=AuthorizationFlag.AUTHORIZATION_REQUIRED | AuthorizationFlag.AUTHORIZATION_REVOCABLE | AuthorizationFlag.AUTHORIZATION_CLAWBACK_ENABLED, source=_asset_issuer_keypair.public_key).set_timeout(100).build()
        tx.sign(_asset_issuer_keypair)
        submitted_tx = self.server.submit_transaction(tx)
        return submitted_tx

    def create_asset(self, code, issuer) -> Asset:
        return Asset(code=code, issuer=issuer)

    def add_trustline(self, asset_code: str, asset_issuer: str, signer: str) -> XDR:
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
            base_fee=fee).append_change_trust_op(Asset(code=asset_code, issuer=asset_issuer)).set_timeout(30).build()
        trustlineOp.sign(signer)

        submitted_trustlineOp = self.server.submit_transaction(trustlineOp)
        return submitted_trustlineOp

    def send_payment(self, asset_code: str, asset_issuer: str, destination_addr: str, amt: str, signer: str) -> str:
        _sender_keypair = Keypair.from_secret(signer)
        src_account = self.server.load_account(_sender_keypair.public_key)
        paymentOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=self._networkPassPhrase,
            base_fee=self.server.fetch_base_fee()
        ).append_payment_op(destination=destination_addr, amount=str(amt), asset=Asset(code=asset_code, issuer=asset_issuer), source=_sender_keypair.public_key
                            ).set_timeout(30).build()
        paymentOp.sign(_sender_keypair)
        submitTx = self.server.submit_transaction(paymentOp)

        return submitTx

    def place_buy_order_for_token_against_another_token(self, signer_key: str, buying_asset_code, buying_asset_issuer, amount,
                                                        selling_asset_code, selling_asset_issuer, starting_price_per_unit,
                                                        offerId=0):

        base_fee = self.server.fetch_base_fee()
        keypair_sender = Keypair.from_secret(signer_key)
        source_acct = self.server.load_account(keypair_sender.public_key)

        buying_asset = Asset(code=buying_asset_code,
                             issuer=buying_asset_issuer)
        selling_asset = Asset(code=selling_asset_code,
                              issuer=selling_asset_issuer)
        str_amount = str(round(float(amount), 7))
        unit_price = str(round(float(starting_price_per_unit), 7))

        manage_buy_order_tx = TransactionBuilder(
            source_account=source_acct,
            base_fee=base_fee,
            network_passphrase=self._networkPassPhrase
        ).add_text_memo(memo_text="Manage buy order"
        ).append_manage_sell_offer_op(selling=selling_asset, buying=buying_asset,
        amount=str_amount, price=unit_price, offer_id=offerId,
        source=keypair_sender.public_key).build()

        # sign transaction
        manage_buy_order_tx.sign(keypair_sender)

        # submit transaction
        submitted_tx = self.server.submit_transaction(manage_buy_order_tx)
        return submitted_tx

    def setUp_signature_weight(self) -> XDR:

        protocol_signer_for_staking_address = Signer.ed25519_public_key(
            Keypair.from_secret(self.Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)
        protocol_signer_for_allowedLicense_address = Signer.ed25519_public_key(
            Keypair.from_secret(self.Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        protocol_signer_for_delegated_address = Signer.ed25519_public_key(
            Keypair.from_secret(self.Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        protocol_signer_for_stablecoin_address = Signer.ed25519_public_key(
            Keypair.from_secret(self.Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        delegated_signer_added_to_allowedLicense_address = Signer.ed25519_public_key(
            Keypair.from_secret(self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"]).public_key, weight=50)

        daoTransaction = (TransactionBuilder(
            source_account=self.server.load_account(
                Keypair.from_secret(self.Keys_to_create["PROTOCOL_SIGNER"]).public_key),
            base_fee=self.server.fetch_base_fee(),
            network_passphrase=self._networkPassPhrase
        ).add_text_memo(memo_text="dao setup"
                        # adding protocol address as the only signer for the staking address
                        ).append_set_options_op(
            low_threshold=50,
            med_threshold=60,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_staking_address,
            source=Keypair.from_secret(
                self.Keys_to_create["STAKING_ADDRESS_SIGNER"]).public_key
            # adding the protocol address as the master signer for the allowed and license address
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_allowedLicense_address,
            source=Keypair.from_secret(
                self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key
            # adding the DELEGATED_SIGNER_ADDRESS as a signer with weight of 50 to authorize transfer of allowed and license tokens
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=delegated_signer_added_to_allowedLicense_address,
            source=Keypair.from_secret(
                self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key
            # adding protocol address as the only signer for the  stablecoin issuing address
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_stablecoin_address,
            source=Keypair.from_secret(
                self.Keys_to_create["STABLECOIN_ASSET_SIGNER"]).public_key
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=50,
            signer=protocol_signer_for_delegated_address,
            source=Keypair.from_secret(
                self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"]).public_key
        ).set_timeout(30).build())

        daoTransaction.sign(Keypair.from_secret(
            self.Keys_to_create["PROTOCOL_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            self.Keys_to_create["STAKING_ADDRESS_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            self.Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            self.Keys_to_create["DELEGATED_SIGNER_ADDRESS"]))


        submitted_transaction = self.server.submit_transaction(daoTransaction)
        # print(submitted_transaction)
        return submitted_transaction

    def create_account_with_friendBot(self, pub_key: str):
        import requests
        url = "https://friendbot.stellar.org"
        response = requests.get(url, params={"addr": pub_key})
        if response.status_code == 200:
            return pub_key
        elif response.status_code == 500:
            raise BadRequestError("seems account has been created")
    
    def add_domain_to_stellar(self, domain=domain):
        acct = Keypair.from_secret(
            self.Keys_to_create["STABLECOIN_ASSET_SIGNER"])
        issuing_account = self.server.load_account(acct.public_key)
        transaction = TransactionBuilder(
            source_account=issuing_account,
            network_passphrase=self._networkPassPhrase,
            base_fee=100,
        ).append_set_options_op(
            home_domain=domain
        ).build()

        transaction.sign(acct.secret)
        adc = self.server.submit_transaction(transaction)
        return adc
    



if __name__ == "__main__":
    Deployment("testnet").startSetUP()
