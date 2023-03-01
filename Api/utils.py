import logging
import random
import secrets, time

from typing import List

# from stablecoin.celery import app as celery_app
from celery import shared_task

import requests
from Blockchains.Stellar.operations import (
    STABLECOIN_ISSUER,
    Mint_Token,
    get_horizon_server,
)
from decouple import config
from modelApp.utils import (
    add_and_update_transaction_hash,
    all_merchant_token_bal,
    all_merchant_token_bal_no_filter,
    assign_transaction_to_merchant,
    check_transaction_hash_if_processed,
    get_all_merchant_object,
    get_transaction_By_Id,
    update_merchant_by_allowedLicenseAmount,
)
from .serializers import TokenTableSerializer, TransactionSerializer
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
    memo: str =None,
    ledger_tx:str =None,
    block_tx_id:str =None,
    _address=STAKING_ADDRESS,
    _asset_code=STAKING_TOKEN_CODE,
    _asset_issuer=STAKING_TOKEN_ISSUER,
) -> bool:
    # check transaction status and return needed data using
    # Check transaction hash has not been processed before
    server = get_horizon_server()

    try:
        tx = server.payments().for_ledger(ledger_tx).cursor(block_tx_id).call()
    except Exception as e:
        print(e)
        pass
    else:
        print("celery has picked up tx")

        amt = round(float(tx["_embedded"]["records"][0]["amount"]), 7)
        recipient_add = tx["_embedded"]["records"][0]["to"]
        sender = tx["_embedded"]["records"][0]["from"]
        asset_code = tx["_embedded"]["records"][0]["asset_code"]
        asset_issuer = tx["_embedded"]["records"][0]["asset_issuer"]
        transaction_hash =  tx["_embedded"]["records"][0]['transaction_hash']
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
            print(hash_check)
            if hash_check == True:
                print("Hash already processed")
                pass
            elif hash_check == False:
                try:
                    if recipient_add == STAKING_ADDRESS:
                        print("got inside")
                        try:
                            [mint_amt, price] = amount_to_naira(amt)
                            update_balance_details = (
                                        update_merchant_by_allowedLicenseAmount(
                                            memo, mint_amt, amt, price, transaction_hash
                                        )
                                    )

                            if update_balance_details == True:
                                    Mint_Token(
                                        sender, round(float(mint_amt), 7), str(memo)
                                    )
                            else:
                                print("Transaction failed")
                                # Transaction failed, send notification to admin group
                        except Exception as error:
                            print("mah this place we dey")
                            print(error)
                            print("this is a critical error")
                            pass

                    elif recipient_add == STABLECOIN_ISSUER:
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
                            
                            # merchants_list = TokenTableSerializer(
                            #     all_merchant_token_bal(), many=True
                            # )
                            selected_ma = merchants_to_process_transaction(
                                sender,
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
                                    # because this is a withdrawal transaction, we just update the user uncleared_bal
                                    # update_cleared_uncleared_bal(
                                    #     merchant=selected_ma["merchant"]["UID"],
                                    #     status="uncleared",
                                    #     amount=amt,
                                    # )
                                    #this also update the IFP uncleared bal
                                    assign_transaction_to_merchant(
                                        transaction=tx_obj,
                                        merchant=selected_ma["merchant"]["UID"],
                                        amount=amt
                                        
                                    )
                                    Notifications(
                                        selected_ma["merchant"]["email"],
                                        "Pending Transaction",
                                        "You have a pending transaction",
                                    )
                                else:
                                    pass

                            elif not selected_ma:
                                print(selected_ma)
                                # notify admin
                                pass
                            # else:
                            #     print("user sent an invalid amount")

                    else:
                        logging.info(
                            f"Transaction recipient address unknown"
                        )
                except Exception as e:
                    # notify_admin(e)
                    print(e)
                    pass
        else:
            # print("addresses", recipient_add, _address)
            # print("codes", asset_code, _asset_code)
            # print("issuers", asset_issuer, _asset_issuer)
            print("this is the pass")
            pass


def first_time_transaction(
    merchants: List, tx_amount: int, bank=None, transaction_type="deposit"
) -> str:
    """
    used for the initial transaction for when the protocol is initailized
    """
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



def merchants_to_process_transaction(
    recipient_block:str, tx_amount: int, bank=None, transaction_type="deposit"
) -> str:
    # merchant_list = []
    #Get last processed Transaction
    # transactions = TransactionsTable.objects.all().order_by("created_at")
    # print(transactions)

    # if len(transactions) < 1:
    #     print("no tranasaction was found")
        #used to initialize the protocol
        # merchants = get_all_merchant_object()
    merchants_list = TokenTableSerializer(
                    all_merchant_token_bal_no_filter(), many=True
            )

    return_merchant = first_time_transaction(merchants=merchants_list.data, tx_amount=tx_amount, bank=None, transaction_type=transaction_type)
    return return_merchant
    # else:
    
    #     tx_serializer = TransactionSerializer(transactions, many=True)
    
    #     try:
    #         # getting the last transaction processed
    #         last_tx = tx_serializer.data[-1]
    #     except IndexError:
    #         #No transaction founc in the protocol, this should only happen initially
    #         last_tx = None
    #         # raise Exception("No transaction found at the moment")
    #     else:
    #         print(last_tx)
    #         print(last_tx["merchant"])
    #         if len(transactions) == 1:
    #             #if len of transaction is 1, no need to filter for last merchant that process transaction
    #             merchants = all_merchant_token_bal_no_filter()
    #         else:
    #             # filter list of merchant, using the last transaction and also who is send the present request
    #             merchants = all_merchant_token_bal(last_tx["merchant"][0], blockchainaddress=recipient_block)
    #         #serializer the return value
            

    #         print("this is mercahnts", merchants)

    #         all_merchant = TokenTableSerializer(merchants, many=True).data

    #         if transaction_type == "deposit":

    #             for merchant in all_merchant:
    #                 # Getting list of merchants to process transaction
    #                 if merchant["allowedTokenAmount"] >= tx_amount:
    #                     merchant_list.append(merchant)
    #                 else:
    #                     pass
    #         elif transaction_type == "user_withdrawals":
    #             for merchant in merchants:

    #                 # if license token - allowed token > amount to withdraw

    #                 if (
    #                     merchant["licenseTokenAmount"] - merchant["allowedTokenAmount"]
    #                 ) >= tx_amount:
    #                     merchant_list.append(merchant)
    #                 # Getting list of merchants to process transaction
    #                 else:
    #                     pass

    #         if len(merchant_list) > 0:
    #             adc = random.choice(merchant_list)
    #             return adc
    #         else:
    #             return False
    


def Notifications(recipient_email, subject, message):
    """
    Use to notify an email about the status of a transaction
    """
    import os
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail
    from decouple import config as env
    print(env('SENDGRID_API_KEY'))

    message = Mail(
        from_email='admin@cowryprotocol.io',
        to_emails=recipient_email,
        subject=subject,
        html_content=message)
    try:
        sg = SendGridAPIClient(env('SENDGRID_API_KEY'))
        response = sg.send(message)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e.message)
    # return requests.post(
    #     "https://api.mailgun.net/v3/sentit.io/messages",
    #     auth=("api", config("MAILGUN_API_KEY")),
    #     data={
    #         "from": "<noreply@sentit.io>",
    #         "to": [f"{recipient_email}", "sentit.io"],
    #         "subject": subject,
    #         "text": message,
    #     },
    # )


# mail = Notifications("sundayafolabi992@gmail.com")
# print(mail.status_code)
# print(mail.content.decode("utf-8"))

# # print(get_all_merchant_object())
# acc = isTransaction_Valid("202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22", "3506927921b2d889e956", _asset_code="NGN", _asset_issuer="GCYROSEOTQR6J5ROTCCLZ36X5ZSUEMNMB2BOZEYXUWQH3IW32E3VDORJ", event_transaction_type="merchant_staking")

# print(acc)


