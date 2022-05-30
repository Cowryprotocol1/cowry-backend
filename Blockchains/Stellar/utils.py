

from http import server
from stellar_sdk.exceptions import Ed25519PublicKeyInvalidError
from stellar_sdk import Account
from django.core.exceptions import ValidationError
from stellar_sdk.server import Server
from decouple import config


horizon_server = Server(horizon_url=config("HORIZON_URL"))


def check_stellar_address(value):
    try:
        Account(account=value, sequence=0)
    except ValueError:
        raise ValidationError("Invalid Stellar Address")
    else:
        return value

def check_address_balance(address:str, asset_issuer:str, asset_code:str, check_amt:float) -> bool:
    bal = horizon_server.accounts().account_id(address).call()
    for bal in bal['balances']:
        if bal["asset_type"] != "native" and bal['asset_code'] == asset_code and bal['asset_issuer'] == asset_issuer:
            if float(bal['balance']) >= float(check_amt):
                return True
            else:
                pass
    return False



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