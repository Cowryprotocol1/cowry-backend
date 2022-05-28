import secrets, requests, random
from typing import List
from decouple import config
from Blockchains.Stellar.operations import STABLECOIN_CODE, STABLECOIN_ISSUER, Mint_Token
from modelApp.utils import all_merchant_token_bal, assign_transaction_to_merchant, check_transaction_hash_if_processed, add_and_update_transaction_hash, get_all_merchant_object, get_transaction_By_Id, update_merchant_by_allowedLicenseAmount

from Blockchains.Stellar.operations import get_horizon_server


STAKING_ADDRESS = config("STAKING_ADDRESS")
STAKING_ADDRESS_SIGNER = config("STAKING_ADDRESS_SIGNER")
STAKING_TOKEN_CODE = config("STAKING_TOKEN_CODE")
STAKING_TOKEN_ISSUER = config("STAKING_TOKEN_ISSUER")


GOVERNANCE_TOKEN_CODE = "GToken"
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")
PROTOCOL_COMMISSION = config("PROTOCOL_COMMISSION")

PROTOCOL_FEE =  float(GENERAL_TRANSACTION_FEE) * float(PROTOCOL_COMMISSION)
# in naira



# Generate a random string of length n
def uidGenerator(size=10):
    return ''.join(secrets.token_hex(size))


def amount_to_naira(amount):
    # Convert amount to Naira
    # Using binance API
    # we might need to add a qoute column to db to store the qoute price an MA naira was minted
    price_url = "https://api.binance.com/api/v3/avgPrice?symbol=USDTNGN"
    response = requests.get(price_url)
    if response.status_code == 200:
        price = round(float(response.json()["price"]), 7)
        naira_amount = round(float(amount) * float(price), 7)

        to_mint_amt = naira_amount / 2
        return [to_mint_amt, price]
    return


# to be used inside model before saving

def isTransaction_Valid(transaction_hash: str, memo: str, _address=STAKING_ADDRESS, _asset_code=STAKING_TOKEN_CODE, _asset_issuer=STAKING_TOKEN_ISSUER, event_transaction_type="merchant_staking") -> bool:
    # check transaction status and return needed data using 
    # Check transaction hash has not been processed before

    try:
        server = get_horizon_server()
        tx = server.payments().for_transaction(transaction_hash).call()

        amt = round(float(tx["_embedded"]["records"][0]["amount"]), 7)
        recipient_add = tx["_embedded"]["records"][0]["to"]
        sender = tx["_embedded"]["records"][0]["from"]
        asset_code = tx["_embedded"]["records"][0]["asset_code"]
        asset_issuer = tx["_embedded"]["records"][0]["asset_issuer"]

        if recipient_add == _address and asset_code == _asset_code and asset_issuer == _asset_issuer:
            if event_transaction_type == "merchant_staking":
                hash_check = check_transaction_hash_if_processed(transaction_hash)
                # If above conditions are met, then the transaction is valid and we have not processed it before

                if hash_check == True:
                    # This means transaction has been process before and should be ignore
                    pass
                elif hash_check == False:
                    add_and_update_transaction_hash(transaction_hash, memo) #add transaction hash to db and update the merchant txhash table
                #    Determin how much to mint using the value Naira to USD
                    try:
                        # determine the amount of allowed and license token to mint to the merchant
                        [mint_amt, price] = amount_to_naira(amt)
                        update_balance_details = update_merchant_by_allowedLicenseAmount(memo, mint_amt, amt, price)
                        if update_balance_details == True:
                            Mint_Token(sender, round(float(mint_amt),7), str(memo))
                        else:
                            print("Transaction failed")
                            # Transaction failed, send notification to admin group
                    except Exception as e:
                        # Critical error, need to send to admin
                        print(e)
                        print("this is a critical error")
                        pass
                else:
                    pass
            elif event_transaction_type == "user_withdrawals":
                # print("user_withdrawals")

                # merchant_list = get_all_merchant_object()
                # print(merchant_list[0])
                # # _merchant_obj = {}
                # # _merchant_obj["id"] =
                # for i in merchant_list:
                #     print(i)

                return True, amt
                
                # try:
                #     adc = merchants_to_process_transaction(
                #         merchants=merchant_list, tx_amount=amt, bank=None, transaction_type="user_withdrawals")
                #     # add the transaction to a merchant pending tx
                #     # notify merchant
                #     # end of tx
                #     print(memo)
                # except Exception as e:
                #     print(e)
                #     #Notify admin
                #     print("this is a critical error")
                #     pass
                # else:
                #     # assign_transaction_to_merchant
                #     transaction = get_transaction_By_Id(memo)
                #     assign_transaction_to_merchant(
                #         transaction=transaction, merchant=memo)
                #     # notify merchant
                #     Notifications(adc.email, "Pending Transaction", "You have a pending transaction")
            else:
                pass
                

        else:
            pass
    except Exception as e:
        print(e)
        # // Add a way to send notification for error to admin group
        return


# def is_user_withdrawal_memo_valid(hash:str, tx_memo):
def merchants_to_process_transaction(merchants: List, tx_amount: int, bank: str, transaction_type="deposit") -> str:
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
           
            if (merchant["licenseTokenAmount"] - merchant["allowedTokenAmount"]) >= tx_amount:
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
        data={"from": "<noreply@sentit.io>",
            "to": [f"{recipient_email}", "sentit.io"],
            "subject": subject,

            "text": message})


# mail = Notifications("sundayafolabi992@gmail.com")
# print(mail.status_code)
# print(mail.content.decode("utf-8"))

# # print(get_all_merchant_object())
# acc = isTransaction_Valid("5de5bc0f18ec40d39d75293d13eb081807ee2ad231542571cff22827c5c484a6", "200525514585", _address=STABLECOIN_ISSUER,
#                           _asset_code=STABLECOIN_CODE, _asset_issuer=STABLECOIN_ISSUER, event_transaction_type="user_withdrawals")

# print(acc)
