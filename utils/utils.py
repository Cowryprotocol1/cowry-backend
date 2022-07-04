from random import randint
import secrets
from stellar_sdk.keypair import Keypair



def uidGenerator(size=10):
    return ''.join(secrets.token_hex(size))

    
def createStellarAddress():
    keys = Keypair.random()
    return {"pubKey": keys.public_key, "privKey": keys.secret}

# to be used inside model before saving


def Id_generator():
    range_start = 10**(8-1)
    range_end = (10**8)-1
    numbers = randint(range_start, range_end)
    return "200"+str(numbers)
   

# print(Id_generator())
# def createOnchainAsset(asset_code, asset_issuer) -> Asset:
#     asset_obj = Asset(code=asset_code, issuer=asset_issuer)

#     return asset_obj.code, asset_obj.issuer, asset_obj.type


# def IssuerSendPayments(recipient_address: str, amt: int, asset_code: str, asset_issuer: str, memo: str, sender_key: str, source_acct: str) -> str:
#     userKeyPair = Keypair.from_secret(sender_key)
#     fee = get_horizon_server().fetch_base_fee()
#     src_account = get_horizon_server().load_account(source_acct)
#     builder = (TransactionBuilder(
#         source_account=src_account,
#         network_passphrase=get_network_passPhrase(),
#         base_fee=fee
#     ).add_text_memo(memo).append_payment_op(destination=recipient_address, amount=str(amt), asset=Asset(code=asset_code, issuer=asset_issuer)
#                                             ).set_timeout(100).build())
#     builder.sign(userKeyPair)
#     submitted_tx = get_horizon_server().submit_transaction(builder)
#     return submitted_tx


# def addAssetTrustLine(asset_code: str, asset_issuer: str, signer: str) -> str:
#     userKeyPair = Keypair.from_secret(signer)
#     fee = get_horizon_server().fetch_base_fee()
#     src_account = get_horizon_server().load_account(userKeyPair.public_key)
#     trustlineOp = TransactionBuilder(
#         source_account=src_account,
#         network_passphrase=get_network_passPhrase(),
#         base_fee=fee).append_change_trust_op(Asset(code=asset_code, issuer=asset_issuer)).set_timeout(100).build()
#     trustlineOp.sign(signer)
#     submitted_trustlineOp = get_horizon_server().submit_transaction(trustlineOp)
#     return submitted_trustlineOp


# def send_Allowed_and_license_token(recipient_address: str, amount: int, memo="MA Onboarding") -> str:
#     """
#     Function to send normal payment
#     """
#     try:
#         signer = Keypair.from_secret(PROTOCOL_SIGNER)

#         base_fee = get_horizon_server().fetch_base_fee()
#         src_load = get_horizon_server().load_account(license_token.public_key)

#         payment_tx = TransactionBuilder(
#             source_account=src_load,
#             base_fee=base_fee,
#             network_passphrase=get_network_passPhrase()
#         ).add_text_memo(memo_text=memo
#                         ).append_payment_op(recipient_address, amount, Asset(code=LICENSE_TOKEN_CODE, issuer=LICENSE_TOKEN_ISSUER), source=signer.public_key
#                                             ).append_payment_op(recipient_address, amount, Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS), source=signer.public_key).set_timeout(100).build()
#         payment_tx.sign(signer)
#         submitted_payment_tx = get_horizon_server().submit_transaction(payment_tx)
#         return submitted_payment_tx
#     except Exception as e:
#         # send notification to group
#         pass


# def send_authoried_burn_payments(source_acct: str, memo: str, amount: str, sender_key: str, asset_signer: str):
#     """This is used to send authorized payments to the issuer's account,
#     this technically burn the asset, and take it out of the total supply
#     """
#     base_fee = get_horizon_server().fetch_base_fee()
#     sender_keypair = Keypair.from_secret(sender_key)
#     _asset_signer = Keypair.from_secret(asset_signer)

#     src_acct = get_horizon_server().load_account(source_acct)

#     burn_auth_payment = TransactionBuilder(
#         source_account=src_acct,
#         base_fee=base_fee,
#         network_passphrase=get_network_passPhrase()
#     ).add_text_memo(memo_text=memo
#                     ).append_set_trust_line_flags_op(trustor=sender_keypair.public_key, asset=Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS),  clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, source=_asset_signer.public_key

#                                                      ).append_payment_op(destination=ALLOWED_AND_LICENSE_P_ADDRESS, amount=str(amount), asset=Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS), source=sender_keypair.public_key

#                                                                          ).append_set_trust_line_flags_op(trustor=sender_keypair.public_key, asset=Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS),  set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, clear_flags=TrustLineFlags.AUTHORIZED_FLAG, source=_asset_signer.public_key

#                                                                                                           ).set_timeout(100).build()
#     burn_auth_payment.sign(sender_keypair)
#     burn_auth_payment.sign(_asset_signer)
#     submitted_tx = get_horizon_server().submit_transaction(burn_auth_payment)
#     return submitted_tx


# def full_authorization_new_address(signer, asset_code, asset_issuer, memo_text, trustorPub):
#     base_fee = get_horizon_server().fetch_base_fee()
#     keypair_sender = Keypair.from_secret(signer)
#     source_acct = get_horizon_server().load_account(keypair_sender.public_key)

#     authorized_asset = Asset(code=asset_code, issuer=asset_issuer)

#     authorized_asset_tx = TransactionBuilder(
#         source_account=source_acct,
#         base_fee=base_fee,
#         network_passphrase=get_network_passPhrase()
#     ).add_text_memo(memo_text=memo_text
#                     ).append_set_trust_line_flags_op(set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=trustorPub, asset=authorized_asset, source=keypair_sender.public_key
#                                                      ).build()

#     # sign transaction
#     authorized_asset_tx.sign(keypair_sender)

#     # submit transaction
#     submitted_tx = get_horizon_server().submit_transaction(authorized_asset_tx)
#     return submitted_tx


# def authorization_address_with_maintain_liability_flag_to_buy_Flag_asset(
#         signer, asset_code, asset_issuer, memo_text, trustorPub,
#         buying_asset_code, buying_asset_issuer, selling_asset_code,
#         selling_asset_issuer, amount, starting_price_per_unit, seller_signer, offerId=0):
#     """
#     Authorized an existing address to buy a regulated asset. address need to already have 
#     a trustline with AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG set to use this function.
#     """
#     base_fee = get_horizon_server().fetch_base_fee()
#     keypair_sender = Keypair.from_secret(signer)
#     source_acct = get_horizon_server().load_account(keypair_sender.public_key)
#     seller_keypair = Keypair.from_secret(seller_signer)

#     authorized_asset = Asset(code=asset_code, issuer=asset_issuer)
#     buying_asset = Asset(code=buying_asset_code, issuer=buying_asset_issuer)
#     selling_asset = Asset(code=selling_asset_code, issuer=selling_asset_issuer)
#     str_amount = str(round(float(amount), 7))
#     unit_price = str(round(float(starting_price_per_unit), 7))

#     authorized_asset_tx = TransactionBuilder(
#         source_account=source_acct,
#         base_fee=base_fee,
#         network_passphrase=get_network_passPhrase()
#     ).add_text_memo(memo_text=memo_text
#                     ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG,
#                                                      set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=trustorPub, asset=authorized_asset,
#                                                      source=keypair_sender.public_key
#                                                      ).append_manage_sell_offer_op(selling=selling_asset, buying=buying_asset,
#                                                                                    amount=str_amount, price=unit_price, offer_id=offerId,
#                                                                                    source=seller_keypair.public_key
#                                                                                    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG,
#                                                                                                                     set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG,
#                                                                                                                     trustor=trustorPub, asset=authorized_asset,
#                                                                                                                     source=keypair_sender.public_key
#                                                                                                                     ).build()

#     # sign transaction
#     authorized_asset_tx.sign(keypair_sender)
#     authorized_asset_tx.sign(seller_keypair)

#     # submit transaction
#     submitted_tx = get_horizon_server().submit_transaction(authorized_asset_tx)
#     return submitted_tx
