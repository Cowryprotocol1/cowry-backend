# testnet reset scripts
from stellar_sdk.keypair import Keypair
from stellar_sdk import TransactionBuilder, Signer
from typing import Dict

from Blockchains.Stellar.operations import get_horizon_server, get_network_passPhrase

# include function to place a sell order for allowed token against stablecoin
# include function to add trustline for assets
# include function to re-create all asset
# handle resetting of signature weight for adding new signers
# need model to holds all pending merchant off boarding XDR for signing by other signers
# add tie breaker to signers

Keys_to_create = {}
Keys_to_create["STAKING_ADDRESS_SIGNER"] = "SCS7KACYXP24Z6UDVSJVTASTGFHNBFZ4PWZJG3GMXKRWAWK7V5IIXTQZ"
Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"] = "SCQDO2WYMJNPULBVXE5FF5A4GTJ4OMLBI5YSZ5F27LP4IBJP2SKKOP55"
Keys_to_create["STABLECOIN_ASSET_SIGNER"] = "SDSFQBN5YCCM3SQWBFLLFTSSAXND5YXSICXGGGN7RFOPKLFCWQDZEB3D"
Keys_to_create["DELEGATED_SIGNER_ADDRESS"] = "SBQO5TAQIRB4E2SDOHEDGQFF66UXASUNRECRLZX53NE64QRSGLOS2K63"
Keys_to_create["PROTOCOL_SIGNER"] = "SAOO3ZHXMI53DKEA5K5RRNAHUTKZ24WLV22FMPGLYOKO2BGYWQQVJW3O"


first_address = "SCCDLNNTMPGTLFRXLIS6QO4X7UGXBR6FSD5HAQJ47NQA6F24HWYF46CE"
second = "SB52Q2NZMFGYJ3BXMSTFVQP2QHOCCSKRLH354OOF7NQOIDUVUHFHU4RF"

# print(Keypair.from_secret(first_address).public_key)


def create_a_valid_blockchain_account(pub_key: str):
    import requests
    url = "https://friendbot.stellar.org"
    response = requests.get(url, params={"addr": pub_key})
    if response.status_code == 200:
        return pub_key
    else:
        pass

    
# uncommet this part to recreate those account on testnet

# for i in range(len(Keys_to_create)):
#     _keys = list(Keys_to_create.values())[i]
#     pub_key = Keypair.from_secret(_keys).public_key
#     create = create_a_valid_blockchain_account(pub_key)

#     print(list(Keys_to_create.values())[i], "Has been successfully created")



def add_signer_to_acct(signer: str, account_address: str, memo="added signer to account") -> Dict:
    """
    Function to add signer to an address
    change an account to multisig
    multisig allow an address to be control by multiple addresses

    """
    signer_keypair = Keypair.from_secret(signer)
    server = get_horizon_server()
    base_fee = server.fetch_base_fee()
    account = server.load_account(signer_keypair.public_key)
    delegated_signer = Signer.ed25519_public_key(account_address, weight=2)
    transaction = (TransactionBuilder(
        source_account=account,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo).append_set_options_op(
        low_threshold=1,
        med_threshold=1,
        high_threshold=2,
        master_weight=0,
        signer=delegated_signer
    ).set_timeout(30).build())
    transaction.sign(signer_keypair)
    submitted_transaction = server.submit_transaction(transaction)
    return submitted_transaction




class DAO_SETUP():
    """
    This class is used to setup the DAO, the dao structure changes the protocol account to a mulitisig account
    It also adds the protocol address to other address manage by the protocol.
    Protocol account will have a max threshold of 100 which will have max DAO member of 20 giving every member equal right of 5 weight
    For all addresses that the protocol is a signer for, the low threshold will be 50%, medium will be 60% while high threshold will be 80% of the max threshold of the DAO which is 100
    60% of 100 = 60, so the minimum threshold is 60. which will require a minimum of 12 dao member to sign the transaction
    """

    def __init__(self) -> None:
        self.load_src = get_horizon_server().load_account(Keypair.from_secret(
            Keys_to_create["PROTOCOL_SIGNER"]).public_key)
        pass
    def add_protocol_to_address(self):

        protocol_signer_for_staking_address = Signer.ed25519_public_key(
            Keypair.from_secret(Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)
        protocol_signer_for_allowedLicense_address = Signer.ed25519_public_key(
            Keypair.from_secret(Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        protocol_signer_for_delegated_address = Signer.ed25519_public_key(
            Keypair.from_secret(Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        protocol_signer_for_stablecoin_address = Signer.ed25519_public_key(
            Keypair.from_secret(Keys_to_create["PROTOCOL_SIGNER"]).public_key, weight=100)

        delegated_signer_added_to_allowedLicense_address = Signer.ed25519_public_key(
            Keypair.from_secret(Keys_to_create["DELEGATED_SIGNER_ADDRESS"]).public_key, weight=50)
        
       
        daoTransaction = (TransactionBuilder(
            source_account=self.load_src,
            base_fee=get_horizon_server().fetch_base_fee(),
            network_passphrase=get_network_passPhrase()
        ).add_text_memo(memo_text="dao setup"
                        # adding protocol address as the only signer for the staking address
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=60,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_staking_address,
            source=Keypair.from_secret(Keys_to_create["STAKING_ADDRESS_SIGNER"]).public_key
            # adding the protocol address as the master signer for the allowed and license address
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_allowedLicense_address,
            source=Keypair.from_secret(Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key
            # adding the DELEGATED_SIGNER_ADDRESS as a signer with weight of 50 to authorize transfer of allowed and license tokens
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=delegated_signer_added_to_allowedLicense_address,
            source=Keypair.from_secret(Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]).public_key
            # adding protocol address as the only signer for the  stablecoin issuing address
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=0,
            signer=protocol_signer_for_stablecoin_address,
            source=Keypair.from_secret(Keys_to_create["STABLECOIN_ASSET_SIGNER"]).public_key
        ).append_set_options_op(
            low_threshold=50,
            med_threshold=50,
            high_threshold=80,
            master_weight=50,
            signer=protocol_signer_for_delegated_address,
            source=Keypair.from_secret(
                Keys_to_create["DELEGATED_SIGNER_ADDRESS"]).public_key
        ).set_timeout(30).build())

        daoTransaction.sign(Keypair.from_secret(Keys_to_create["PROTOCOL_SIGNER"]))
        
        daoTransaction.sign(Keypair.from_secret(
            Keys_to_create["STAKING_ADDRESS_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            Keys_to_create["ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            Keys_to_create["STABLECOIN_ASSET_SIGNER"]))

        daoTransaction.sign(Keypair.from_secret(
            Keys_to_create["DELEGATED_SIGNER_ADDRESS"]))

        submitted_transaction = get_horizon_server().submit_transaction(daoTransaction)
        # print(submitted_transaction)
        return submitted_transaction








# print("starting dao setup")
# dao_step_1 = DAO_SETUP()
# print(dao_step_1.add_protocol_to_address())
