

from stellar_sdk import TransactionEnvelope, Network, SetTrustLineFlags, Payment
from Api.test.test_setup import TestSetUpClass
from Blockchains.Stellar.operations import Mint_Token


class StellarFunctions(TestSetUpClass):

    def test_1_minting_token_to_addr_with_trustline(self):
        memo = "test"
        send_amt = 1.5
        mint = Mint_Token(self.created_user.blockchainAddress, send_amt, memo)
        destruct = TransactionEnvelope.from_xdr(
            mint["envelope_xdr"], network_passphrase=Network.TESTNET_NETWORK_PASSPHRASE)

        operations = destruct.transaction.operations
        self.assertEquals(len(operations), 6)
        self.assertTrue(mint['memo'] == memo)
        self.assertTrue(type(operations[0]) == SetTrustLineFlags)
        self.assertTrue(type(operations[1]) == SetTrustLineFlags)
        self.assertTrue(type(operations[2]) == Payment)
        self.assertTrue(type(operations[3]) == Payment)
        self.assertTrue(type(operations[4]) == SetTrustLineFlags)
        self.assertTrue(type(operations[5]) == SetTrustLineFlags)
        self.assertTrue(float(operations[2].amount) ==
                        send_amt)
        self.assertTrue(float(operations[3].amount) ==
                        send_amt)
        self.assertTrue(operations[2].asset.code == "NGNALLOW")
        self.assertTrue(operations[2].asset.issuer ==
                        "GDCPU5EEMTHDBJ4OUUBYS2OC4YZAO2YCF5AVXIU6CNCFOTAI67NQRIC5")

        self.assertTrue(operations[3].asset.code == "NGNLICENSE")
        self.assertTrue(operations[3].asset.issuer == "GDCPU5EEMTHDBJ4OUUBYS2OC4YZAO2YCF5AVXIU6CNCFOTAI67NQRIC5")
