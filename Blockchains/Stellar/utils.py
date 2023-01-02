

from http import server
from stellar_sdk import Account
from django.core.exceptions import ValidationError
from stellar_sdk.server import Server
from decouple import config
from .operations import is_account_valid, STABLECOIN_CODE, ALLOWED_AND_LICENSE_P_ADDRESS, ALLOWED_TOKEN_CODE, STABLECOIN_ISSUER

horizon_server = Server(horizon_url=config("HORIZON_URL"))


def check_stellar_address(value):
    try:
        Account(account=value, sequence=0)
    except ValueError:
        raise ValidationError("Invalid Stellar Address")
    else:
        return value


def check__asset_code_For_stable(value: str):
    if value != STABLECOIN_CODE:
        raise ValidationError("Invalid asset code for protocol supported stablecoin")
    elif value == STABLECOIN_CODE:
        return value
    else:
        raise ValidationError("Invalid Stellar Address")
def check_address_balance(address:str, asset_issuer:str, asset_code:str, check_amt:float) -> bool:
    try:
        bal = horizon_server.accounts().account_id(address).call()
    except Exception as Err:
        return False
    else:
        for bal in bal['balances']:
            if bal["asset_type"] != "native" or bal["asset_type"] != "liquidity_pool_shares" and bal['asset_code'] == asset_code and bal['asset_issuer'] == asset_issuer:
                if float(bal['balance']) >= float(check_amt):
                    # print(bal["balance"])
                    return True
                else:
                    pass
    return False

def protocolAssetTotalSupply(assets:dict = {ALLOWED_AND_LICENSE_P_ADDRESS: ALLOWED_TOKEN_CODE,
            STABLECOIN_ISSUER: STABLECOIN_CODE}):
    """Use to get the total supply of protocol supply"""
    # accts = {
    #         ALLOWED_AND_LICENSE_P_ADDRESS: ALLOWED_TOKEN_CODE,
    #         STABLECOIN_ISSUER: STABLECOIN_CODE,
    #     }
    #include the total amount of stablecoin
    #include the total amount of allowed token
    #include total amount of protocol allowed token (Total supply of allowed token - stablecoin supply)
    
    _asset_supply = {}
    for i in range(len(assets)):
        _keys = list(assets.keys())[i]
        _values = list(assets.values())[i]
        try:
            bala = horizon_server.assets().for_code(_values).for_issuer(_keys).call()
            print("----------------")
            print(bala)
            for i in bala["_embedded"]["records"]:
                _asset_supply[_values] = {
                    "total_accounts": i["accounts"],
                    "total_balance": i["balances"],
                }

        except Exception as E:
            # print(E)
            raise Exception("error getting details from this endpoint")
    return _asset_supply










# print(check_address_balance(
#     "GDUOMP2S62CUUCR2ZP3IRCATCCTII77G7ES52K4QAHYPX63GDZJ3QUIP", "GC54NAZBATJECJIXV6VQ7UV2NUR5N33NA7FY5NDKSKEZRD57KSUUGXV3", "NGN", 1000))
    

    # if acct:
    #     return value
    # else:
    #     raise ValueError("This is not a valid Stellar address")



# def send_claimable_Payment_for_Allow_and_license(recipient_address: str, amount: int, memo="MA Onboarding") -> str:
#     """
#     If recipient address has no trustline for staking asset, we send claimable payment, with a time limit of 24hrs"""
#     try:
#         signer = Keypair.from_secret(PROTOCOL_SIGNER)

#         source_acct_load = get_horizon_server().load_account(signer.public_key)
#         base_fee = get_horizon_server().fetch_base_fee()
#         predicate = ClaimPredicate.predicate_before_relative_time(
#             seconds=86400)
#         _claimant = Claimant(
#             destination=recipient_address, predicate=predicate)

#         claimable_tx = TransactionBuilder(
#             source_account=source_acct_load,
#             base_fee=base_fee,
#             network_passphrase=get_network_passPhrase()
#         ).add_text_memo(memo_text=memo
#                         ).append_create_claimable_balance_op(Asset(code=LICENSE_TOKEN_CODE, issuer=LICENSE_TOKEN_ISSUER),
#                                                              str(amount), claimants=[_claimant]
#                                                              ).append_create_claimable_balance_op(Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS), amount=str(amount), claimants=[_claimant]
#                                                                                                   ).set_timeout(100).build()
#         claimable_tx.sign(signer)
#         submitted_tx = get_horizon_server().submit_transaction(claimable_tx)
#         return submitted_tx
#     except Exception as e:
#         # send notification to Admin
#         pass


# def add_authorization_to_account(signer: str, source_address: str):
#     """This add restriction to asset issue by the account"""
#     _keypair = Keypair.from_secret(signer)
#     baseFee = get_horizon_server().fetch_base_fee()
#     load_acct = get_horizon_server().load_account(source_address)

#     tx = TransactionBuilder(
#         source_account=load_acct,
#         base_fee=baseFee,
#         network_passphrase=get_network_passPhrase()

#     ).append_set_options_op(set_flags=AuthorizationFlag.AUTHORIZATION_REQUIRED | AuthorizationFlag.AUTHORIZATION_REVOCABLE | AuthorizationFlag.AUTHORIZATION_CLAWBACK_ENABLED).set_timeout(100).build()
#     tx.sign(_keypair)
#     submitted_tx = get_horizon_server().submit_transaction(tx)
#     return submitted_tx


# def transfer_Authorized_asset_btw_accounts(sender_key: str, source_Address: str, recipient_address: str, amount: int, memo: str, asset_code: str, asset_issuer: str, asset_signer: str) -> str:
#     """Use to transfer authorized asset from one account to another,
#     By default this uses the Protocol asset as the asset to transfer"""
#     source_acct = get_horizon_server().load_account(source_Address)
#     base_fee = get_horizon_server().fetch_base_fee()
#     sender_keypair = Keypair.from_secret(sender_key)
#     asset_signer = Keypair.from_secret(asset_signer)
#     _asset = Asset(code=asset_code, issuer=asset_issuer)
#     print(_asset)
#     amount = str(amount)

#     authorized_tx = TransactionBuilder(
#         source_account=source_acct,
#         base_fee=base_fee,
#         network_passphrase=get_network_passPhrase()
#     ).add_text_memo(memo_text=memo

#                     ).append_set_trust_line_flags_op(trustor=sender_keypair.public_key, asset=_asset,  clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, source=asset_signer.public_key

#                                                      ).append_set_trust_line_flags_op(trustor=recipient_address, asset=_asset, set_flags=TrustLineFlags.AUTHORIZED_FLAG, clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, source=asset_signer.public_key

#                                                                                       ).append_payment_op(destination=recipient_address, amount=amount, asset=_asset, source=sender_keypair.public_key

#                                                                                                           ).append_set_trust_line_flags_op(trustor=sender_keypair.public_key, asset=_asset, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG,  clear_flags=TrustLineFlags.AUTHORIZED_FLAG, source=asset_signer.public_key

#                                                                                                                                            ).append_set_trust_line_flags_op(trustor=recipient_address, asset=_asset, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, clear_flags=TrustLineFlags.AUTHORIZED_FLAG, source=asset_signer.public_key

#                                                                                                                                                                             ).set_timeout(100).build()

#     authorized_tx.sign(sender_keypair)
#     authorized_tx.sign(asset_signer)
#     submitted_tx = get_horizon_server().submit_transaction(authorized_tx)
#     return submitted_tx
