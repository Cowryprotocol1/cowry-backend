from typing import Dict, TypeVar
from decouple import config
from stellar_sdk.keypair import Keypair
from stellar_sdk import Server, Asset, TransactionBuilder, Network, Signer, Claimant, ClaimPredicate, AuthorizationFlag, TrustLineFlags
import logging
logging.basicConfig(level=logging.INFO,  format="%(levelname)s %(message)s")

XDR = TypeVar('XDR')

STAKING_ADDRESS = config("STAKING_ADDRESS")
STAKING_ADDRESS_SIGNER = config("STAKING_ADDRESS_SIGNER")
STAKING_TOKEN_CODE = config("STAKING_TOKEN_CODE")
STAKING_TOKEN_ISSUER = config("STAKING_TOKEN_ISSUER")

LICENSE_TOKEN_CODE = config("LICENSE_TOKEN_CODE")
LICENSE_TOKEN_ISSUER = config("ALLOWED_AND_LICENSE_P_ADDRESS")

ALLOWED_TOKEN_CODE = config("ALLOWED_TOKEN_CODE")
ALLOWED_AND_LICENSE_P_ADDRESS = config("ALLOWED_AND_LICENSE_P_ADDRESS")
ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER = config(
    "ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER")

PROTOCOL_SIGNER = config("PROTOCOL_SIGNER")
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")
PROTOCOL_COMMISSION = config("PROTOCOL_COMMISSION")
STABLECOIN_CODE = config("STABLECOIN_CODE")
STABLECOIN_ISSUER = config("STABLECOIN_ISSUER")
STABLECOIN_SIGNER_ADDRESS = config("STABLECOIN_ASSET_SIGNER")
PROTOCOL_FEE_ACCOUNT = config("PROTOCOL_FEE_ACCOUNT")
DELEGATED_SIGNER_ADDRESS = config("DELEGATED_SIGNER_ADDRESS")


def Mint_Token(recipient: str, amount: int, memo: str) -> bool:
    """
    Mint token to MA, Account
    """
    logging.critical(
        "need to handle if user address already maintain liability")
    check_trustline = is_Asset_trusted(address=recipient)
    if check_trustline == True:
        # this is an existing address that already has a trustline to the issuer
        logging.info(
            "Minting to an existing address that already has a trustline to the issuer")
        mint_token_existing = send_and_authorize_allowed_and_license_token_existing_address(
            recipient=recipient, memo=memo, amount=str(amount), asset_signer=ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER)
        return mint_token_existing
    else:
        print("minting token to a new address")
        logging.info(
            "Minting to a new address")

        token_mint = send_and_authorize_allowed_and_license_token_new_address(
            recipient, memo, str(amount), ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER)
        # Protocol update MA allowed and license token balance for matching during on and off ramp
        return token_mint


def get_horizon_server():
    return Server(horizon_url=config("HORIZON_URL"))


def get_network_passPhrase(horizon_url=config("HORIZON_URL")) -> Network:
    if "testnet" in horizon_url:
        return Network.TESTNET_NETWORK_PASSPHRASE
    else:
        return Network.PUBLIC_NETWORK_PASSPHRASE


def is_account_valid(account_address: str) -> bool:
    try:
        check = get_horizon_server().accounts().account_id(account_address).call()
        if check:
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False

# check if a given asset is trusted by an account


def is_Asset_trusted(address: str, asset_number=2, issuerAddress=ALLOWED_AND_LICENSE_P_ADDRESS, stableCoin=STABLECOIN_ISSUER) -> bool:
    try:
        _balances = get_horizon_server().accounts().account_id(address).call()
        balances = _balances["balances"]
        trustAssetList = []
        for i in balances:
            if i["asset_type"] != "native" and i["asset_issuer"] == issuerAddress:
                trustAssetList.append(i["asset_code"])
            elif i["asset_type"] != 'native' and i["asset_issuer"] == stableCoin:
                trustAssetList.append(i)

        if len(trustAssetList) >= int(asset_number):
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


def send_and_authorize_allowed_and_license_token_new_address(recipient: str, memo: str, amount: str, asset_signer: str):
    """ This is used to send payments from the issuers account to an MA account,
        This is only expected to be called when onboarding an MA, it handles both minting and authorizing 
        license and allowed token
    """
    base_fee = get_horizon_server().fetch_base_fee()
    authorizer_of_tx = Keypair.from_secret(
        DELEGATED_SIGNER_ADDRESS)
    # sender_keypair = Keypair.from_secret(sender_key)
    _asset_signer = Keypair.from_secret(asset_signer)

    src_acct = get_horizon_server().load_account(_asset_signer.public_key)
    allow_asset = Asset(code=ALLOWED_TOKEN_CODE,
                        issuer=ALLOWED_AND_LICENSE_P_ADDRESS)
    license_asset = Asset(code=LICENSE_TOKEN_CODE,
                          issuer=LICENSE_TOKEN_ISSUER)

    burn_auth_payment = TransactionBuilder(
        source_account=src_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo
    ).append_set_trust_line_flags_op(set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient, asset=allow_asset, source=_asset_signer.public_key
    ).append_set_trust_line_flags_op(set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient, asset=license_asset, source=_asset_signer.public_key
    ).append_payment_op(destination=recipient, amount=str(amount), asset=allow_asset, source=_asset_signer.public_key
    ).append_payment_op(destination=recipient, amount=str(amount), asset=license_asset, source=_asset_signer.public_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient, asset=allow_asset, source=_asset_signer.public_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient, asset=license_asset, source=_asset_signer.public_key
    ).set_timeout(1800).build()
    burn_auth_payment.sign(authorizer_of_tx)
    submitted_tx = get_horizon_server().submit_transaction(burn_auth_payment)
    return submitted_tx


def send_and_authorize_allowed_and_license_token_existing_address(recipient: str, memo: str, amount: str, asset_signer: str):
    base_fee = get_horizon_server().fetch_base_fee()
    authorizer_of_tx = Keypair.from_secret(
        DELEGATED_SIGNER_ADDRESS)  # DELEGATED_SIGNER_ADDRESS has the required weight to authorise the transaction
    _asset_signer = Keypair.from_secret(asset_signer)

    src_acct = get_horizon_server().load_account(_asset_signer.public_key)
    allow_asset = Asset(code=ALLOWED_TOKEN_CODE,
                        issuer=ALLOWED_AND_LICENSE_P_ADDRESS)
    license_asset = Asset(code=LICENSE_TOKEN_CODE,
                          issuer=LICENSE_TOKEN_ISSUER)

    burn_auth_payment = TransactionBuilder(
        source_account=src_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo
                    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient, asset=allow_asset, source=_asset_signer.public_key
                                                     ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient, asset=license_asset, source=_asset_signer.public_key
                                                                                      ).append_payment_op(destination=recipient, amount=str(amount), asset=allow_asset, source=_asset_signer.public_key
                                                                                                          ).append_payment_op(destination=recipient, amount=str(amount), asset=license_asset, source=_asset_signer.public_key
                                                                                                                              ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient, asset=allow_asset, source=_asset_signer.public_key
                                                                                                                                                               ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient, asset=license_asset, source=_asset_signer.public_key
                                                                                                                                                                                                ).set_timeout(100).build()
    burn_auth_payment.sign(authorizer_of_tx)
    submitted_tx = get_horizon_server().submit_transaction(burn_auth_payment)
    return submitted_tx

# adc = get_horizon_server().accounts().for_asset(asset=Asset(code=ALLOWED_TOKEN_CODE, issuer=ALLOWED_AND_LICENSE_P_ADDRESS)).call()

# print(adc)

# all you need to place a buy order on stellar Dex


def manage_buy_order(signer_key: str, buying_asset_code, buying_asset_issuer, amount,
                    selling_asset_code, selling_asset_issuer, starting_price_per_unit,
                    offerId=0):

    base_fee = get_horizon_server().fetch_base_fee()
    keypair_sender = Keypair.from_secret(signer_key)
    source_acct = get_horizon_server().load_account(keypair_sender.public_key)

    buying_asset = Asset(code=buying_asset_code, issuer=buying_asset_issuer)
    selling_asset = Asset(code=selling_asset_code, issuer=selling_asset_issuer)
    str_amount = str(round(float(amount), 7))
    unit_price = str(round(float(starting_price_per_unit), 7))

    manage_buy_order_tx = TransactionBuilder(
        source_account=source_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text="Manage buy order"
    ).append_manage_sell_offer_op(selling=selling_asset, buying=buying_asset,
    amount=str_amount, price=unit_price, offer_id=offerId,
    source=keypair_sender.public_key).build()

    # sign transaction
    manage_buy_order_tx.sign(keypair_sender)

    # submit transaction
    submitted_tx = get_horizon_server().submit_transaction(manage_buy_order_tx)
    return submitted_tx


def merchants_swap_ALLOWED_4_NGN_Send_payment_2_depositor(
    signer=ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER, asset_code=ALLOWED_TOKEN_CODE, asset_issuer=ALLOWED_AND_LICENSE_P_ADDRESS, memo_text=None, trustorPub=None,
        buying_asset_code=STABLECOIN_CODE, buying_asset_issuer=STABLECOIN_ISSUER, selling_asset_code=ALLOWED_TOKEN_CODE,
        selling_asset_issuer=ALLOWED_AND_LICENSE_P_ADDRESS, amount=None, starting_price_per_unit=1, offerId=0, depositor_pubKey=None):
    """
    Authorized an existing address to buy a regulated asset. address need to already have 
    a trustline with AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG set to use this function.
    """
    base_fee = get_horizon_server().fetch_base_fee()
    keypair_sender = Keypair.from_secret(signer)
    authorizer_of_tx = Keypair.from_secret(
        DELEGATED_SIGNER_ADDRESS)  # The delegated signer can authorize tx
    source_acct = get_horizon_server().load_account(keypair_sender.public_key)
    # seller_keypair = Keypair.from_secret(seller_signer)

    authorized_asset = Asset(code=asset_code, issuer=asset_issuer)
    buying_asset = Asset(code=buying_asset_code, issuer=buying_asset_issuer)
    selling_asset = Asset(code=selling_asset_code, issuer=selling_asset_issuer)
    str_amount = str(round(float(amount), 7))
    unit_price = str(round(float(starting_price_per_unit), 7))
    amount_minus_fee = str(
        round(float(amount) - float(GENERAL_TRANSACTION_FEE), 7))
    protocol_fee = float(GENERAL_TRANSACTION_FEE) * float(PROTOCOL_COMMISSION)
    merchant_fee = float(GENERAL_TRANSACTION_FEE) - protocol_fee

    authorized_asset_tx = TransactionBuilder(
        source_account=source_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo_text
).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG,
set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=trustorPub, asset=authorized_asset,
source=keypair_sender.public_key
).append_manage_sell_offer_op(selling=selling_asset, buying=buying_asset,
amount=str_amount, price=unit_price, offer_id=offerId,
source=trustorPub
).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG,
set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG,
trustor=trustorPub, asset=authorized_asset,
source=keypair_sender.public_key
).append_payment_op(destination=depositor_pubKey, asset=buying_asset, amount=amount_minus_fee, source=trustorPub
            ).append_payment_op(destination=PROTOCOL_FEE_ACCOUNT, asset=buying_asset, amount=str(round(protocol_fee, 7)), source=trustorPub
                                ).build()

    # sign transaction
    authorized_asset_tx.sign(authorizer_of_tx)
    xdr_obj = authorized_asset_tx.to_xdr()
    return xdr_obj


def OffBoard_Merchant_with_Burn(recipient_pub_key: str, amount: str, memo: str, exchange_rate: str, total_staked_amt:str, allowed_license_token_signer=ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER) -> XDR:
    """
    this burn allowed and license token from a merchant account and also unstake the merchant staked token
    """
    base_fee = get_horizon_server().fetch_base_fee()
    # sender_keypair = Keypair.from_secret(sender_key)
    authorizer_of_tx = Keypair.from_secret(DELEGATED_SIGNER_ADDRESS)
    _regulated_asset_signer = Keypair.from_secret(allowed_license_token_signer)
    _staking_address_signer = Keypair.from_secret(
        PROTOCOL_SIGNER)  # protocol address is a major signer

    src_acct = get_horizon_server().load_account(_regulated_asset_signer.public_key)
    allow_asset = Asset(code=ALLOWED_TOKEN_CODE,
                        issuer=ALLOWED_AND_LICENSE_P_ADDRESS)
    license_asset = Asset(code=LICENSE_TOKEN_CODE,
                        issuer=LICENSE_TOKEN_ISSUER)
    staked_asset = Asset(code=STAKING_TOKEN_CODE, issuer=STAKING_TOKEN_ISSUER)

    if exchange_rate == 0.0:
        exchange_rate = 1.0
    else:
        exchange_rate = exchange_rate

    allowed_license_amt = round(float(amount) / float(exchange_rate), 7)
    held_amt = float(total_staked_amt) - allowed_license_amt
    # total_held_currency = allowed_license_amt + held_percentage
    amount_to_unstake = float(allowed_license_amt) + float(held_amt)

    burn_auth_payment = TransactionBuilder(
        source_account=src_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient_pub_key, asset=allow_asset, source=_regulated_asset_signer.public_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=recipient_pub_key, asset=license_asset, source=_regulated_asset_signer.public_key
    ).append_payment_op(destination=ALLOWED_AND_LICENSE_P_ADDRESS, amount=str(amount), asset=allow_asset, source=recipient_pub_key
    ).append_payment_op(destination=ALLOWED_AND_LICENSE_P_ADDRESS, amount=str(amount), asset=license_asset, source=recipient_pub_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient_pub_key, asset=allow_asset, source=_regulated_asset_signer.public_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=recipient_pub_key, asset=license_asset, source=_regulated_asset_signer.public_key
    ).append_payment_op(destination=recipient_pub_key, amount=str(amount_to_unstake), asset=staked_asset, source=STAKING_ADDRESS
    ).set_timeout(1800).build()
    burn_auth_payment.sign(authorizer_of_tx)
    burn_auth_payment.sign(_staking_address_signer)

    return burn_auth_payment.to_xdr()


def User_withdrawal_from_protocol(merchant_pub_key: str, amount: str, memo: str, user_withdrawing_from_protocol_address: str, allowed_license_token_signer=ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER) -> XDR:
    """
    Function used to off ramp a user deposited fiat asset,
    User send payment to the protocol address and the protocol address will use this function to send payment between protocol and merchant for minting allowed and stablecoin

    """
    base_fee = get_horizon_server().fetch_base_fee()
    # sender_keypair = Keypair.from_secret(sender_key)
    authorizer_of_tx = Keypair.from_secret(DELEGATED_SIGNER_ADDRESS)
    _regulated_asset_signer = Keypair.from_secret(allowed_license_token_signer)
    _stablecoin_signer = Keypair.from_secret(STABLECOIN_SIGNER_ADDRESS)
    # protocol address is a major signer on the stablecoin address
    protocol_signer = Keypair.from_secret(PROTOCOL_SIGNER)

    src_acct = get_horizon_server().load_account(_regulated_asset_signer.public_key)
    allow_asset = Asset(code=ALLOWED_TOKEN_CODE,
                        issuer=ALLOWED_AND_LICENSE_P_ADDRESS)

    stablecoin = Asset(code=STABLECOIN_CODE, issuer=STABLECOIN_ISSUER)
    amount_minus_protocol_fee = str(
        round(float(amount) - float(GENERAL_TRANSACTION_FEE), 7))
    protocol_fee = float(GENERAL_TRANSACTION_FEE) * float(PROTOCOL_COMMISSION)

    merchant_fee = float(GENERAL_TRANSACTION_FEE) - float(protocol_fee)
    # transaction show be send to protocol account 4 withdrawal and to deposit

    burn_auth_payment = TransactionBuilder(
        source_account=src_acct,
        base_fee=base_fee,
        network_passphrase=get_network_passPhrase()
    ).add_text_memo(memo_text=memo
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, set_flags=TrustLineFlags.AUTHORIZED_FLAG, trustor=merchant_pub_key, asset=allow_asset, source=_regulated_asset_signer.public_key
    ).append_payment_op(destination=merchant_pub_key, amount=str(amount_minus_protocol_fee), asset=allow_asset, source=_regulated_asset_signer.public_key
    ).append_set_trust_line_flags_op(clear_flags=TrustLineFlags.AUTHORIZED_FLAG, set_flags=TrustLineFlags.AUTHORIZED_TO_MAINTAIN_LIABILITIES_FLAG, trustor=merchant_pub_key, asset=allow_asset, source=_regulated_asset_signer.public_key

    ).append_payment_op(destination=merchant_pub_key, amount=str(merchant_fee), asset=stablecoin, source=_stablecoin_signer.public_key
    ).append_payment_op(destination=PROTOCOL_FEE_ACCOUNT, amount=str(protocol_fee), asset=stablecoin, source=_stablecoin_signer.public_key
    ).set_timeout(1200).build()
    burn_auth_payment.sign(authorizer_of_tx)
    burn_auth_payment.sign(protocol_signer)
    submit_transaction = get_horizon_server().submit_transaction(burn_auth_payment)

    return submit_transaction
