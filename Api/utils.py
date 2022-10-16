import logging
import random
import secrets, time

from typing import List

# from stablecoin.celery import app as celery_app
from celery import shared_task

import requests
from Blockchains.Stellar.operations import (
    STABLECOIN_CODE,
    STABLECOIN_ISSUER,
    Mint_Token,
    get_horizon_server,
)
from decouple import config
from modelApp.utils import (
    add_and_update_transaction_hash,
    all_merchant_token_bal,
    assign_transaction_to_merchant,
    check_transaction_hash_if_processed,
    get_all_merchant_object,
    get_transaction_By_Id,
    update_merchant_by_allowedLicenseAmount,
)
from .serializers import TokenTableSerializer
from modelApp.models import TransactionsTable
from modelApp.utils import update_cleared_uncleared_bal

STAKING_ADDRESS = config("STAKING_ADDRESS")
STAKING_TOKEN_CODE = config("STAKING_TOKEN_CODE")
STAKING_TOKEN_ISSUER = config("STAKING_TOKEN_ISSUER")


GOVERNANCE_TOKEN_CODE = "GToken"
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")
PROTOCOL_COMMISSION = config("PROTOCOL_COMMISSION")

IFP_STAKE_MINT_VALUE = 0.9  # 90%

PROTOCOL_FEE = float(GENERAL_TRANSACTION_FEE) * float(PROTOCOL_COMMISSION)
# in naira


# Generate a random string of length n
def uidGenerator(size=10):
    return "".join(secrets.token_hex(size))


def amount_to_naira(amount):
    # Convert amount to Naira
    # Using binance API
    # we might need to add a qoute column to db to store the qoute price an MA naira was minted
    price_url = "https://api.binance.com/api/v3/avgPrice?symbol=USDTNGN"
    response = requests.get(price_url)
    if response.status_code == 200:
        price = round(float(response.json()["price"]), 7)
        naira_amount = round(float(amount) * float(price), 7)

        to_mint_amt = naira_amount * IFP_STAKE_MINT_VALUE
        return [to_mint_amt, price]
    return


# to be used inside model before saving
@shared_task
def isTransaction_Valid(
    transaction_hash: str,
    memo: str,
    _address=STAKING_ADDRESS,
    _asset_code=STAKING_TOKEN_CODE,
    _asset_issuer=STAKING_TOKEN_ISSUER,
    event_transaction_type="merchant_staking",
) -> bool:
    # check transaction status and return needed data using
    # Check transaction hash has not been processed before
    server = get_horizon_server()

    try:
        tx = server.payments().for_transaction(transaction_hash).call()
    except Exception as e:
        print(e)
        pass
    else:

        amt = round(float(tx["_embedded"]["records"][0]["amount"]), 7)
        recipient_add = tx["_embedded"]["records"][0]["to"]
        sender = tx["_embedded"]["records"][0]["from"]
        asset_code = tx["_embedded"]["records"][0]["asset_code"]
        asset_issuer = tx["_embedded"]["records"][0]["asset_issuer"]
        # print("addresses", recipient_add, _address)
        # print("codes", asset_code, _asset_code)
        # print("issuers", asset_issuer, _asset_issuer)

        if (
            recipient_add == _address
            and asset_code == _asset_code
            and asset_issuer == _asset_issuer
        ):
            hash_check = check_transaction_hash_if_processed(transaction_hash)
            # If above conditions are met, then the transaction is valid and we have not processed it before
            if hash_check == True:
                print("Hash already processed")
                pass
            elif hash_check == False:
                try:
                    if event_transaction_type == "merchant_staking":
                        print("got inside")
                        update_hash = add_and_update_transaction_hash(
                            transaction_hash, memo
                        )  # add transaction hash to db and update the merchant txhash table
                        #    Determin how much to mint using the value Naira to USD
                        print("update_hash")
                        print(update_hash)
                        if update_hash == True:
                            try:
                                # determine the amount of allowed and license token to mint to the merchant
                                [mint_amt, price] = amount_to_naira(amt)
                                update_balance_details = (
                                    update_merchant_by_allowedLicenseAmount(
                                        memo, mint_amt, amt, price
                                    )
                                )
                                if update_balance_details == True:
                                    Mint_Token(
                                        sender, round(float(mint_amt), 7), str(memo)
                                    )
                                else:
                                    print("Transaction failed")
                                    # Transaction failed, send notification to admin group
                            except Exception as e:
                                # Critical error, need to send to admin
                                print(e)
                                print("this is a critical error")
                                pass
                        elif update_hash == False:
                            print(
                                "Transaction hash already processed or merchant with the memo not found"
                            )
                            pass

                    elif event_transaction_type == "user_withdrawals":
                        try:
                            tx_obj = TransactionsTable.objects.get(id=memo)
                        except TransactionsTable.DoesNotExist:
                            print("memo does not exist")
                            pass
                        except Exception:
                            #notify admin
                            pass
                        else:
                            tx_obj.transaction_amount = amt
                            tx_obj.save()
                            # if amt >= float(tx_obj.transaction_amount):
                            merchants_list = TokenTableSerializer(
                                all_merchant_token_bal(), many=True
                            )
                            selected_ma = merchants_to_process_transaction(
                                merchants_list.data,
                                tx_amount=amt,
                                bank=None,
                                transaction_type="user_withdrawals",
                            )
                            if selected_ma:
                                # add transaction hash to db and update the merchant txhash table
                                update_hash = add_and_update_transaction_hash(
                                    transaction_hash, selected_ma["merchant"]["UID"]
                                )
                                if update_hash == True:
                                    update_cleared_uncleared_bal(
                                        merchant=selected_ma["merchant"]["UID"],
                                        status="uncleared",
                                        amount=amt,
                                    )
                                    assign_transaction_to_merchant(
                                        transaction=tx_obj,
                                        merchant=selected_ma["merchant"]["UID"],
                                        
                                    )
                                    Notifications(
                                        selected_ma["merchant"]["email"],
                                        "Pending Transaction",
                                        "You have a pending transaction",
                                    )
                                else:
                                    pass

                            elif not selected_ma:
                                # notify admin
                                pass
                            # else:
                            #     print("user sent an invalid amount")

                    else:
                        logging.info(
                            f"Transaction type of {event_transaction_type} not supported"
                        )
                except Exception as e:
                    # notify_admin(e)
                    print(e)
                    pass
        else:
            print("addresses", recipient_add, _address)
            print("codes", asset_code, _asset_code)
            print("issuers", asset_issuer, _asset_issuer)
            print("this is the pass")
            pass


# def is_user_withdrawal_memo_valid(hash:str, tx_memo):
def merchants_to_process_transaction(
    merchants: List, tx_amount: int, bank=None, transaction_type="deposit"
) -> str:
    merchant_list = []
    if transaction_type == "deposit":
        for merchant in merchants:
            # Getting list of merchants to process transaction
            if merchant["allowedTokenAmount"] >= tx_amount:
                merchant_list.append(merchant)
            else:
                pass
    elif transaction_type == "user_withdrawals":
        for merchant in merchants:

            # if license token - allowed token > amount to withdraw

            if (
                merchant["licenseTokenAmount"] - merchant["allowedTokenAmount"]
            ) >= tx_amount:
                merchant_list.append(merchant)
            # Getting list of merchants to process transaction
            else:
                pass

    if len(merchant_list) > 0:
        adc = random.choice(merchant_list)
        return adc
    else:
        return False


def Notifications(recipient_email, subject, message):
    """
    Use to notify an email about the status of a transaction
    """
    return requests.post(
        "https://api.mailgun.net/v3/sentit.io/messages",
        auth=("api", config("MAILGUN_API_KEY")),
        data={
            "from": "<noreply@sentit.io>",
            "to": [f"{recipient_email}", "sentit.io"],
            "subject": subject,
            "text": message,
        },
    )


# mail = Notifications("sundayafolabi992@gmail.com")
# print(mail.status_code)
# print(mail.content.decode("utf-8"))

# # print(get_all_merchant_object())
# acc = isTransaction_Valid("202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22", "3506927921b2d889e956", _asset_code="NGN", _asset_issuer="GCYROSEOTQR6J5ROTCCLZ36X5ZSUEMNMB2BOZEYXUWQH3IW32E3VDORJ", event_transaction_type="merchant_staking")

# print(acc)
