from typing import Dict, TypeVar
from decouple import config
from stellar_sdk.keypair import Keypair
from stellar_sdk import Server, Asset, TransactionBuilder, Network, Signer, Claimant, ClaimPredicate, AuthorizationFlag, TrustLineFlags
from stellar_sdk.transaction_builder import TransactionBuilder
from stellar_sdk.exceptions import NotFoundError, BadRequestError, BadResponseError
from stellar_sdk.sep.exceptions import InvalidSep10ChallengeError

from stellar_sdk.transaction_envelope import TransactionEnvelope
import logging
logging.basicConfig(level=logging.INFO,  format="%(levelname)s %(message)s")
# from .utils import calculateTxFee, minimum_transaction_fee
from stellar_sdk.sep.stellar_web_authentication import (
    build_challenge_transaction,
    read_challenge_transaction,
    verify_challenge_transaction_signed_by_client_master_key,
    verify_challenge_transaction_threshold,
)
from stellar_sdk.operation.manage_data import ManageData
import jwt, os

XDR = TypeVar('XDR')

DOMAIN = config("COWRY_DEFAULT_DOMAIN")

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

SWAP_SIGNER = config("SWAP_ACCOUNT_PRIVATE_KEY")


def Mint_Token(recipient: str, amount: int, memo: str) -> bool:
    """
    Mint token to MA, Account
    """
    logging.critical(
        "need to handle if user address already maintain liability")
    check_trustline = is_Asset_trusted(address=recipient)
    if check_trustline[0] == True:
        # this is an existing address that already has a trustline to the issuer
        logging.info(
            "Minting to an existing address that already has a trustline to the issuer")
        mint_token_existing = send_and_authorize_allowed_and_license_token_existing_address(
            recipient=recipient, memo=memo, amount=str(amount), asset_signer=ALLOWED_AND_LICENSE_P_ADDRESS_SIGNER)
        return mint_token_existing
    else:
        # print("minting token to a new address")
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


def get_stellarActive_network(network_url:str):
    if "testnet" in network_url:
        return "Testnet"
    else:
        return "Public"


def is_account_valid(account_address: str) -> bool:
    try:
        check = get_horizon_server().accounts().account_id(account_address).call()
        if check:
            return True
        else:
            return False
    except Exception as e:
        # print(e)
        return False

# check if a given asset is trusted by an account


def is_Asset_trusted(address: str, asset_number=2, issuerAddress=ALLOWED_AND_LICENSE_P_ADDRESS, stableCoin=STABLECOIN_ISSUER) -> bool:
    try:
        _balances = get_horizon_server().accounts().account_id(address).call()
        balances = _balances["balances"]
        trustAssetList = []
        xlm_balance = []
        for i in balances:
            if i["asset_type"] == "native":
                xlm_balance.append(i["balance"])

            if i["asset_type"] != "native" and i["asset_type"] != "liquidity_pool_shares" and i["asset_issuer"] == issuerAddress:
                trustAssetList.append(i["asset_code"])
            elif i["asset_type"] != 'native' and i["asset_type"] != "liquidity_pool_shares" and i["asset_issuer"] == stableCoin:
                trustAssetList.append(i)

        if len(trustAssetList) >= int(asset_number):
            return [True, xlm_balance]
        else:
            return [False, 0.0]
    except Exception as e:
        print(e)
        return [False, 0.0]


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
    this burn allowed and license token from a merchant account and also un-stake the merchant staked token
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
    #user db needs to be update once transaction done, update the allowed token
    #Stablecoin address already has the allowed token used for swapping during deposit
    # possible solution
    # 1.during audit, the allowed token on the stablecoin account should be consider and removed from the supply
    # 2.include all this details when the total balance endpoint is called to give user idea of what 
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




# liquidity pool for protocol assets NGN - USDC or NGN - XLM
from decimal import Decimal
from typing import List, Any, Dict
from stellar_sdk.liquidity_pool_asset import LiquidityPoolAsset
# Returns the given asset pair in "protocol order."
def order_asset(a: Asset, b: Asset) -> List[Asset]:
    return [a, b] if LiquidityPoolAsset.is_valid_lexicographic_order(a, b) else [b, a]


# for trustline of liquidity pool assets, users are expected to already have trustlines for the protocols assets
# we check from the api before forwarding the transactions to the server
def add_trustline(asset:Asset, signer: str) -> Dict[str, Any]:
        """
        Function to add trustline to an account
        params - asset can be any stellar based asset type like liquiditypool asset, creditalphnum4 or 12
        """
        # stablecoin address adds trustline to ALLOWED NGN
        # protocol address adds trustline to NGN
        userKeyPair = Keypair.from_secret(signer)
        fee = get_horizon_server().fetch_base_fee()
        src_account = get_horizon_server().load_account(userKeyPair.public_key)
        trustlineOp = TransactionBuilder(
            source_account=src_account,
            network_passphrase=get_network_passPhrase(),
            base_fee=fee).append_change_trust_op(asset=asset).set_timeout(30).build()
        trustlineOp.sign(signer)

        submitted_trustlineOp = get_horizon_server().submit_transaction(trustlineOp)
        return submitted_trustlineOp
    
def add_liquidity(
        source: Keypair,
        pool_id: str,
        max_reserve_a: Decimal,
        max_reserve_b: Decimal,
) -> dict[str, Any]:


    exact_price = max_reserve_a / max_reserve_b
    min_price = exact_price - exact_price * Decimal("0.005") #
    max_price = exact_price + exact_price * Decimal("0.005")
    tx = (
        TransactionBuilder(
            source_account=source,
            network_passphrase=get_network_passPhrase(),
            base_fee=get_horizon_server().fetch_base_fee()).append_liquidity_pool_deposit_op(
            liquidity_pool_id=pool_id,
            max_amount_a=f"{max_reserve_a:.7f}",
            max_amount_b=f"{max_reserve_b:.7f}",
            min_price=min_price,
            max_price=max_price,
        )
            .build()
    )
    tx.sign(source)
    return get_horizon_server().submit_transaction(tx)



def remove_liquidity(
        source: Keypair, pool_id: str, shares_amount: Decimal
) -> dict[str, Any]:
    pool_info = get_horizon_server.liquidity_pools().liquidity_pool(pool_id).call()
    total_shares = Decimal(pool_info["total_shares"])
    min_reserve_a = (
            shares_amount
            / total_shares
            * Decimal(pool_info["reserves"][0]["amount"])
            * Decimal("0.95")
    ) #
    min_reserve_b = (
            shares_amount
            / total_shares
            * Decimal(pool_info["reserves"][1]["amount"])
            * Decimal("0.95")
    )
    tx = (
       TransactionBuilder(
            source_account=source,
            network_passphrase=get_network_passPhrase(),
            base_fee=get_horizon_server().fetch_base_fee())
            .append_liquidity_pool_withdraw_op(
            liquidity_pool_id=pool_id,
            amount=f"{shares_amount:.7f}",
            min_amount_a=f"{min_reserve_a:.7f}",
            min_amount_b=f"{min_reserve_b:.7f}",
        )
            .build()
    )
    tx.sign(source)
    return get_horizon_server().submit_transaction(tx)







# this function has not been testing yet, the swapping of asset rely heavily on the frontend and walletconnet, will be continued once we have the frontend setup
def calculateTxFee(amount:float) -> float:
    """used to calculate transaction fee for swap"""
    percentage = 0.1
    fee = float(amount) * percentage/100
    return round(fee, 4)

def minimum_transaction_fee() -> float:
    """minimum amount an account is willing to pay for fee, useful during a network surge"""
    BASE_FEE = 50000 #this is in XLM
    return BASE_FEE



# swap will be between any two assets
# Transaction fee from the swap will be paid in the sending Asset e.g NGN -> USDC fee in NGN
# Transaction fee is send to the protocol fee account
# return XDR to be sign and submitted by the client wallet

# RISK
# how will swap transaction be signed by the protocol? when using FeeBump
    # Sol
        # 1. Provide the feeBump transaction on a separate account that will be funded with XLM as need by the protocol.
        # This address doesn't need to be a signer and doesn't need any signer on him too. XLM will be add to the account when account Balance is believe to be low.
        # 1000 XLM will be able to process 10 Million transaction even when at a surge time for the network at 0.0001
        
def Swap_assets(
    user_secret_key,
    sending_currency,
    send_issuer,
    send_amount,
    receive_currency,
    receive_issuer,
    dest_amt,
    swap_path,
    swap_path_fee,
    memo,
):
    """Function used to swap between assets on stellar, This function also deduct transaction fee from the amount the User is swapping from"""
    # need to include handling of fee, we need to get the fee amount and path from the backend and process payment

    secret_keys = Keypair.from_secret(user_secret_key)
    source_key_load = secret_keys.public_key
    source_load = get_horizon_server().load_account(source_key_load)

    transaction_fee = calculateTxFee(send_amount)

    _sendingAsset = Asset(sending_currency, send_issuer)
    _destAsset = Asset(receive_currency, receive_issuer)
    _feeAsset = Asset.native()

    newAmt = float(send_amount) - float(transaction_fee)

    min_dest_amt = float(dest_amt) - float(dest_amt) * 0.05

    swap_transaction = (
        TransactionBuilder(
            source_account=source_load,
            network_passphrase=get_network_passPhrase,
            base_fee=minimum_transaction_fee(),
        )
        .add_text_memo(memo)
        .append_path_payment_strict_send_op(
            secret_keys.public_key,
            _sendingAsset,
            str(round(newAmt, 7)),
            _destAsset,
            str(round(min_dest_amt, 7)),
            swap_path,
            secret_keys.public_key,
        )
        .append_path_payment_strict_send_op(
            Keypair.from_secret(SWAP_SIGNER).public_key,
            _sendingAsset,
            str(round(float(transaction_fee), 7)),
            _feeAsset,
            str(0.0002),
            swap_path_fee,
        ).set_timeout(30)
        .build()
    )

    swap_transaction.sign(user_secret_key)

    signed_tx = swap_transaction.to_xdr()
    
    try:
        fee_bump_swap = submit_feeBump_transaction(signed_tx)
    except (BadRequestError, NotFoundError, BadResponseError) as errors:
        print(errors)
        raise Exception("error submitting swap Transaction on Horizon")
    else:
        # encrypt user private key back with their private key
        return fee_bump_swap



def submit_feeBump_transaction(transaction_xdr):
    transaction_to_submit = TransactionEnvelope.from_xdr(
        xdr=transaction_xdr, network_passphrase=get_network_passPhrase
    )
    """
    sign transaction and submit to the blockchain using feebump transaction, the source for feebump is from sentit.
    """

    transaction_key = SWAP_SIGNER #this is to be an independent account controlled by the protocol
    transaction_feeBump = TransactionBuilder.build_fee_bump_transaction(
        fee_source=Keypair.from_secret(transaction_key),
        base_fee=minimum_transaction_fee(),
        inner_transaction_envelope=transaction_to_submit,
        network_passphrase=get_network_passPhrase,
    )
    transaction_feeBump.sign(transaction_key)
    print("________________________")
    print(transaction_feeBump.hash().hex())
    print("________________________")

    sent_fee_block = get_horizon_server().submit_transaction(transaction_feeBump)
    return sent_fee_block


def build_challenge_tx(server_key:str,
        client_key:str,
        client_domain:str,
        _web_auth_domain=os.path.join(DOMAIN, "auth")):
    
    # Server builds challenge transaction
    challenge_tx = build_challenge_transaction(server_secret=server_key, client_account_id=client_key, home_domain=client_domain, web_auth_domain=_web_auth_domain, network_passphrase=get_network_passPhrase())
    print("this is chanllenge tx", challenge_tx)

    return challenge_tx


def server_verify_challenge(challenge:"XDR", home_domain:str, web_auth_domain:str, server_pub_key=Keypair.from_secret(DELEGATED_SIGNER_ADDRESS).public_key) -> str:
    server = get_horizon_server()
    network_pass=get_network_passPhrase()


    # Server verifies signed challenge transaction
    read_xdr = read_challenge_transaction(
        challenge_transaction=challenge,
        server_account_id=server_pub_key,
        home_domains=home_domain,
        web_auth_domain=web_auth_domain,
        network_passphrase=network_pass,

        )
    print("found xdr", read_xdr)

    
    client_domain = None
    for operation in read_xdr.transaction.transaction.operations:
        print("this is operation", operation)
      
        if (
            isinstance(operation, ManageData)
            and operation.data_name == "client_domain"
        ):
            print("this is operation", operation.data_name)
            print("this is operation", operation.data_value)
            print("*" * 20)
            client_domain = operation.data_value.decode()
            # break
    print(client_domain)
    requester_acct = read_xdr.transaction.transaction.operations[0].source.account_id

    client_account_exists = False
    horizon_client_account = None
    try:
        horizon_client_account = server.load_account(requester_acct)
        client_account_exists = True
    except NotFoundError:
        raise Exception("Valid account not found, you need to sign xdr with master key")
    
    print(client_domain)
    if client_account_exists:
        # gets list of signers from account
        signers = horizon_client_account.load_ed25519_public_key_signers()
        # chooses the threshold to require: low, med or high
        threshold = horizon_client_account.thresholds.med_threshold
        try:
            signed_transaction = verify_challenge_transaction_threshold(
                challenge,
                server_pub_key,
                home_domain,
                web_auth_domain,
                network_pass,
                threshold,
                signers,
            )
        except InvalidSep10ChallengeError as e:
            print("You should handle possible exceptions:")
            print(e)
            raise Exception(e)
        else:
            return signed_transaction, client_domain
    else:
        # verifies that master key has signed challenge transaction
        try:
            signed_transaction = verify_challenge_transaction_signed_by_client_master_key(
                challenge,
                server_pub_key,
                home_domain,
                web_auth_domain,
                network_pass,
            )
            print("Client Master Key Verified.")
            print("need to issue jwt token via endpoint")
            return signed_transaction, client_domain
        except InvalidSep10ChallengeError as e:
            print("You should handle possible exceptions:")
            print(e)


def generate_jwt(challenge, client_domain):
    from stablecoin import settings

       # Server verifies signed challenge transaction
    read_xdr = read_challenge_transaction(
        challenge,
        Keypair.from_secret(DELEGATED_SIGNER_ADDRESS).public_key,
        DOMAIN,
        os.path.join(DOMAIN, "auth"),
        get_network_passPhrase(),
    )

    if read_xdr.client_account_id.startswith("M") or not read_xdr.memo:
        sub = read_xdr.client_account_id
    else:
        sub = f"{read_xdr.client_account_id}:{read_xdr.memo}"
    issued_at = read_xdr.transaction.transaction.preconditions.time_bounds.min_time
    jwt_dict = {
        "iss": os.path.join(DOMAIN, "auth"),
        "sub": sub,
        "iat": issued_at,
        "exp": issued_at + 24 * 60 * 60,
        "jti": read_xdr.transaction.hash().hex(),
        "client_domain": client_domain,
    }
    return jwt.encode(jwt_dict, settings.SECRET_KEY, algorithm="HS256")

