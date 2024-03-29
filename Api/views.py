import logging
import os
from urllib.parse import urlparse

from decouple import config
from django.db import IntegrityError
from django.db.models import F
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.renderers import TemplateHTMLRenderer
from rest_framework.response import Response
from rest_framework.views import APIView
from stellar_sdk import TransactionEnvelope
from stellar_sdk.exceptions import (BadRequestError, BadResponseError,
                                    NotFoundError)

from Blockchains.Stellar.operations import (
    ALLOWED_AND_LICENSE_P_ADDRESS, ALLOWED_TOKEN_CODE, DOMAIN,
    LICENSE_TOKEN_CODE, LICENSE_TOKEN_ISSUER, STABLECOIN_CODE,
    STABLECOIN_ISSUER, STAKING_ADDRESS, OffBoard_Merchant_with_Burn,
    User_withdrawal_from_protocol, build_challenge_tx, generate_jwt,
    get_horizon_server, get_network_passPhrase, is_Asset_trusted,
    merchants_swap_ALLOWED_4_NGN_Send_payment_2_depositor,
    server_verify_challenge)
from Blockchains.Stellar.utils import (check_address_balance,
                                       check_stellar_address,
                                       getStellar_tx_fromMemo,
                                       protocolAssetTotalSupply)
from modelApp.models import MerchantsTable, TokenTable, TransactionsTable
from modelApp.utils import (delete_merchant, get_all_transaction_for_merchant,
                            get_merchant_by_pubKey, get_pending_transactions,
                            get_transaction_by_pubKey, insert_sep_transaction,
                            protocolAudit, update_cleared_uncleared_bal,
                            update_pending_transaction_model,
                            update_PendingTransaction_Model,
                            update_sep_transaction,
                            update_sep_transaction_no_ifp,
                            update_transaction_status, update_xdr_table)
from utils.utils import Id_generator, uidGenerator

from .serializers import (Fiat_Off_RampSerializer, Fiat_On_RampSerializer,
                          MerchantsTableSerializer,
                          OffBoard_A_MerchantSerializer, Sep6DepositSerializer,
                          Sep6WithdrawalSerializer, TransactionSerializer,
                          XdrGeneratedTransactionSerializer, XdrSerializer)
from .utils import (STAKING_TOKEN_ISSUER, Notifications, isTransaction_Valid,
                    merchants_to_process_transaction)


STAKING_TOKEN = config("STAKING_TOKEN_CODE")
STAKING_ADDRESS = config("STAKING_ADDRESS")
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")
PROTOCOL_DELEGATED_SIGNER = config("DELEGATED_SIGNER_ADDRESS")

SEP_INFO = {
    "deposit": {
        "NGN": {
            "enabled": True,
            "fee_fixed": GENERAL_TRANSACTION_FEE,
            "min_amount": 1000,
            "fields": {
                "asset_code": {
                    "description": "asset code for depositing, this should be NGN"
                },
                "account": {
                    "description": "stellar address to credit with the stable coin"
                },
                "amount": {"description": "amount in TZS that you plan to deposit"},
            },
        },
    },
    "withdraw": {
        "NGN": {
            "enabled": True,
            "fee_minimum": GENERAL_TRANSACTION_FEE,
            "min_amount": 1000,
            "max_amount": 5000000,
            "types": {
                "bank_account": {
                    "fields": {
                        "bank_name": {
                            "description": "name of the abnk eg GTB, Firstbank, FCMB, etc"
                        },
                        "account_number": {"description": "your account number"},
                        "amount": {"description": "Amount you intend to withdraw"},
                    }
                },
            },
        },
        "fee": {"enabled": True},
        "account_creation": {"enable": False},
        "transactions": {"enabled": False, "authentication_required": False},
        "transaction": {"enabled": True, "authentication_required": False},
    },
}


# need to add all nigeria banks, sorting code can be any random numbers, we only use them internally, they are not send to the bank

# print(banks["AccessBank"])

# @api_view(['GET'])
# def index(requests):
#     data = {"test": "test"}
#     return Response(data)


class IndexPage(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "Api/index.html"

    def get(self, requests):
        data = {"test": "ok"}
        return Response(data)


class OnBoardMA(APIView):
    """
    Endpoint to onboard a merchant
    IFP/Merchant are giving 90% minting right, this is calculated when they staked using the amount_to_naira function
    """

    def post(self, request):
        staking_address = config("STAKING_ADDRESS")
        is_asset_trusted = is_Asset_trusted(
            request.data.get("blockchainAddress"), asset_number=3
        )

        if is_asset_trusted[0] == True:
            _data = {}
            _data["blockchainAddress"] = request.data.get("blockchainAddress")
            _data["email"] = request.data.get("email")
            _data["bankName"] = request.data.get("bankName")
            _data["bankAccount"] = request.data.get("bankAccount")
            _data["phoneNumber"] = request.data.get("phoneNumber")
            _data["UID"] = uidGenerator()
            # _data ["nameOnAcct"] = request.data.get("nameOnAcct")

            serializeMA = MerchantsTableSerializer(data=_data)
            if serializeMA.is_valid():

                try:
                    merchant_saved = serializeMA.save()

                    TokenTable.objects.create(merchant=merchant_saved)
                    # TxHashTable.objects.create(merchant=merchant_saved)
                    # TransactionsTable.objects.create(merchant=merchant_saved)

                except Exception as e:
                    # send to admins
                    return Response(
                        {"error": "Something went wrong"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                else:
                    data = {
                        "msg": f"please send {STAKING_TOKEN} to the below details",
                        "memo": merchant_saved.UID,
                        "staking_address": staking_address,
                        "staking_asset_code": STAKING_TOKEN,
                        "staking_asset_issuer": STAKING_TOKEN_ISSUER,
                        "user_details": serializeMA.validated_data,
                    }
                    return Response(data, status=status.HTTP_201_CREATED)

            else:
                return Response(serializeMA.errors, status=status.HTTP_400_BAD_REQUEST)

        else:
            assets = [
                {"code": ALLOWED_TOKEN_CODE, "issuer": ALLOWED_AND_LICENSE_P_ADDRESS},
                {"code": LICENSE_TOKEN_CODE, "issuer": LICENSE_TOKEN_ISSUER},
                {"code": STABLECOIN_CODE, "issuer": STABLECOIN_ISSUER},
            ]

            return Response(
                {
                    "error": "your address must add trustline to the following assets",
                    "assets": assets,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )


# update merchants transaction table each time there is a pending transaction for onramp
# add a way to clean on processed transactions assign to a merchant from the db and free merchant balance
# we can provide an endpoint for merchant that exceed 30min - 1hr and has not been sent





class ON_RAMP_FIAT_USERS(APIView):
    """
    General endpoint for users deposits of fiat to get stablecoin

    """
    def post(self, request):
        
        """
        Endpoint returns an NGN deposit address, memo and the MA that wants to process, this will return bank details of the MA
        deposit intent endpoint, the following are required params
        amount,
        user_blockchain_address
        """
        if  request.data.get("memo") == None:
            amount = request.data.get("amount")
            bankType = request.data.get("bankType")
            blockchainAddress = request.data.get("blockchainAddress")
            transaction_narration = request.data.get("narration")
            transaction_source = request.data.get("transaction_source")
            check_data = Fiat_On_RampSerializer(data=request.data)
            # 12/sep/1995

            

            if check_data.is_valid():
                print(check_data.validated_data)
                # print()
                # check if the address has a trustline for the NGN asset
                is_asset_trusted = is_Asset_trusted( address =blockchainAddress, asset_number=1, issuerAddress=STABLECOIN_ISSUER)

                if is_asset_trusted[0] == True:
                    # merchants_list = TokenTableSerializer(
                    #     all_merchant_token_bal(), many=True
                    # )
                    try:
                        MA_selected = merchants_to_process_transaction(
                            blockchainAddress, amount, bankType
                        )
                    except Exception as e:
                        print(e)
                        return Response(
                                {
                                    "error": "this is an error from our end, the admin will be notified soon"
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    # add filtering process for deposit and check for multiple deposit option
                    # print(MA_selected)
                    if MA_selected:
                        transaction_src = request.data.get("transaction_source")
                        # if transaction_src != "sep" :
                        if transaction_src == None:
                            print("got inside protocol")
                            try:
                                print("inside trx")
                                update_pending_transaction_model(
                                    MA_selected["merchant"]["UID"],
                                    transaction_amt=str(
                                        float(amount) + float(GENERAL_TRANSACTION_FEE)
                                    ),
                                    transaction_type="deposit",
                                    narration=transaction_narration,
                                    transaction_memo=MA_selected["merchant"]["UID"],
                                    transaction_status="pending",
                                    phone_num=MA_selected["merchant"]["phoneNumber"],
                                    user_bank_account=MA_selected["merchant"]["bankAccount"],
                                    bank_name=MA_selected["merchant"]["bankName"],
                                    user_block_address=blockchainAddress,
                                )
                                print("done update")
                            except IntegrityError as e:
                                # if "UNIQUE constraint failed" in e.args:
                                return Response(
                                    {
                                        "error": "there is a pending payment with this narration, please update transaction narration"
                                    },
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                        # if transaction_src and transaction_src == "sep":
                        else:
                            print("inside sep")
                        
                            transactionId = request.data.get("transaction_Id")
                            print(transactionId)
                            if not transactionId or transactionId == None or transactionId == '':
                                transactionId = Id_generator()
                                # return Response({"error":"transaction_Id needed for this transaction"}, status=status.HTTP_400_BAD_REQUEST)
                                
                            try:
                                trx = TransactionsTable.objects.get(id=transactionId)
                            except (TransactionsTable.DoesNotExist):
                                try:
                                    update_pending_transaction_model(
                                            MA_selected["merchant"]["UID"],
                                            transaction_amt=str(
                                                float(amount) + float(GENERAL_TRANSACTION_FEE)
                                            ),
                                            transaction_type="deposit",
                                            narration=transaction_narration,
                                            transaction_memo=MA_selected["merchant"]["UID"],
                                            transaction_status="pending",
                                            phone_num=MA_selected["merchant"]["phoneNumber"],
                                            user_bank_account=MA_selected["merchant"]["bankAccount"],
                                            bank_name=MA_selected["merchant"]["bankName"],
                                            user_block_address=blockchainAddress,
                                        )
                                except IntegrityError as e:
                                    print("this endpoint",e)
                                # if "UNIQUE constraint failed" in e.args[0]:
                                    return Response(
                                        {
                                            "error": "there is a pending payment with this narration, please update transaction narration"
                                        },
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                                # return Response({"error":"transaction_Id not found"}, status=status.HTTP_400_BAD_REQUEST)

                            # print(trx)
                            else:
                                if trx.transaction_narration != ("sep"+transactionId):
                                    return Response({"error":"invalid transaction Id"}, status=status.HTTP_400_BAD_REQUEST)
                                #update the sep transaction
                                try:
                                    print("valide inside")
                                    update_sep_transaction(
                                        transaction_Id=transactionId,
                                        merchant_id=  MA_selected["merchant"]["UID"],
                                        transaction_amt=str(
                                            float(amount) + float(GENERAL_TRANSACTION_FEE)
                                        ),
                                        transaction_type="deposit",
                                        narration=transaction_narration,
                                        transaction_memo=MA_selected["merchant"]["UID"],
                                        transaction_status="pending",
                                        phone_num=MA_selected["merchant"]["phoneNumber"],
                                        user_bank_account=MA_selected["merchant"]["bankAccount"],
                                        bank_name=MA_selected["merchant"]["bankName"],
                                        user_block_address=blockchainAddress
                                        )
                                    print("validation pass")
                                except IntegrityError as e:
                                    return Response(
                                        {
                                            "error": "there is a pending payment with this narration, please update transaction narration"
                                        },
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                            pass
                        # else:
                        # IFPs should be able to cancel a pending transaction after a certain amount of time
                        # IFP should be able to specify the amount they receive with a particular transaction narration
                        transactionFeeAmt =  float(amount) + float(GENERAL_TRANSACTION_FEE)
                        update_cleared_uncleared_bal(
                            MA_selected["merchant"]["UID"], "uncleared", transactionFeeAmt
                        )
                        print("got outside")

                        s_data = {
                            "message": f"Send funds to account below with the following details, the correct amount to send is {float(amount) + float(GENERAL_TRANSACTION_FEE)}, please include your narration when making deposit in from your bank account",
                            "memo": MA_selected["merchant"]["UID"],
                            "amount": amount,
                            "fee": GENERAL_TRANSACTION_FEE,
                            "amount_to_pay":transactionFeeAmt,
                            "narration": transaction_narration,
                            "bank_name": MA_selected["merchant"]["bankName"],
                            "account_number": MA_selected["merchant"]["bankAccount"],
                            "phoneNumber": MA_selected["merchant"]["phoneNumber"],
                            "eta": "5 minutes",
                        }
                        print("return this data", s_data)
                        return Response(data=s_data, status=status.HTTP_200_OK)
                    else:
                        return Response(
                            data={
                                "error": "No merchant found",
                                "message": "All MA are occupied at the moment or you are entering a very high amount",
                            },
                            status=status.HTTP_404_NOT_FOUND,
                        )
                else:
                    assets = [{"code": STABLECOIN_CODE, "issuer": STABLECOIN_ISSUER}]
                    return Response(
                        {
                            "error": f"your address must add trustline to the following asset(s)",
                            "assets": assets,
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )
            else:

                print("this one",check_data.errors)
                return Response(
                    {"error": check_data.errors}, status=status.HTTP_400_BAD_REQUEST
                )


# # ==============================================================================
# # HANDLING MULTIPLE POST WITH A SINGLE CLASS BASED VIEW
# # ==============================================================================



        elif  request.data.get("memo") != None:

            """
            Endpoint Users called when deposits has been sent to the merchant, bank account
            Protocol notify merchant of a new pending transaction
            """
            # amount = request.data.get("amount")

            _data = {}
            _data["bank_name"] = request.data.get("bank_name")
            _data["account_number"] = request.data.get("account_number")
            _data["name_on_acct"] = None
            _data["phone_number"] = request.data.get("phone_number")
            _data["blockchain_address"] = request.data.get("blockchain_address")
            _data["transaction_narration"] = request.data.get("transaction_narration")
            _data["amount"] = request.data.get("amount")
            memo = request.data.get("memo")

            # if memo and acct_number and amount and phone_number and bank_name and narration and user_blockchain_address:
            check_args = Fiat_Off_RampSerializer(data=request.data)
            if check_args.is_valid() and memo:
                try:

                    pending_merchant_tx = get_pending_transactions(memo)
                except MerchantsTable.DoesNotExist:
                    return Response(
                        {"error": "invalid memo"}, status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    for i in pending_merchant_tx:
                        if i.transaction_type == "deposit":
                            if (
                                i.transaction_narration == _data["transaction_narration"]
                                and i.users_address == _data["blockchain_address"]
                                and float(i.transaction_amount) == float(_data["amount"])
                            ):
                                try:
                                    merchant_details = MerchantsTable.objects.get(UID=memo)
                                    Notifications(
                                        recipient_email=merchant_details.email,
                                        subject="Deposit Confirmation",
                                        message=f"You have a pending deposit of {_data['amount']} NGN to your account, please login to confirm the transaction",
                                    )
                                except Exception as e:
                                    # Notify admin
                                    print(e)
                                    return Response(
                                        {"error": "something went wrong"},
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                                else:
                                    return Response(
                                        data={
                                            "message": "Your Blockchain address will credited soon. Thank You"
                                        },
                                        status=status.HTTP_200_OK,
                                    )
                            else:
                                pass

                        else:
                            pass
                    return Response(
                        "Transaction not found", status=status.HTTP_400_BAD_REQUEST
                    )
            if check_args.errors:
                return Response(data=check_args.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response(
                    data={"error": "invalid memo params"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            #


class OFF_RAMP_FIAT(APIView):
    """
    General endpoint for users to withdraw stablecoin to their bank account
    """

    def post(self, request):
        # user call this endpoint
        # get merchant with allowed token  less than the license token
        # amount les than is equal to the amount the user want to withdrawal
        """
        Calling the GET endpoint will return an address for deposit and also a
        unique memo for the transaction. Transaction don't get assigned to Merchant first,
        they only get assigned to the Merchant after deposit has been made to the address,
        this is a design pattern to avoid merchant balance being locked up
        """

        _data = {}
        _data["bank_name"] = request.data.get("bank_name")
        _data["account_number"] = request.data.get("account_number")
        _data["name_on_acct"] = request.data.get("name_on_acct")
        _data["phone_number"] = request.data.get("phone_number")
        _data["blockchain_address"] = request.data.get("blockchain_address")
        _data["transaction_narration"] = request.data.get("transaction_narration")
        _data["amount"] = request.data.get("amount")
        serializer = Fiat_Off_RampSerializer(data=request.data)
        if serializer.is_valid():
            _data["expected_amount_with_fee"] = float(
                request.data.get("amount")
            ) + float(GENERAL_TRANSACTION_FEE)
            balance_check = check_address_balance(
                _data["blockchain_address"],
                STABLECOIN_ISSUER,
                STABLECOIN_CODE,
                _data["amount"],
            )
            if balance_check:
                # if any users has a balance, then their is a merchant with debt to the protocol
                # we can easily process payment just by checking a users balance
                # we should probably check with server to make sure there is a merchant with debt
                transaction_src = request.data.get("transaction_source")
                
                if transaction_src == None:
                    try:

                        transaction_p = update_PendingTransaction_Model(
                            transaction_amt=float(_data["amount"]) + float(GENERAL_TRANSACTION_FEE),
                            transaction_type="withdraw",
                            narration=_data["transaction_narration"],
                            transaction_hash=None,
                            user_block_address=_data["blockchain_address"],
                            phone_num=_data["phone_number"],
                            user_bank_account=_data["account_number"],
                            bank_name=_data["bank_name"],
                        )


                    except IntegrityError as e:
                        print("this endpoint",e)

                        # if "UNIQUE constraint failed" in e.args[0]:
                        return Response(
                            {
                                "error": "there is a pending payment with this narration, please update transaction narration"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                        # else:
                        #     # notify admin
                        #     return Response(
                        #         {"error": "something went wrong"},
                        #         status=status.HTTP_400_BAD_REQUEST,
                        #     )
                else:
                    transactionId = request.data.get("transaction_Id")
                    if not transactionId or transactionId == None or transactionId == '':
                        #accessing the widget directly without sep10 authorization
                        transactionId = Id_generator()
                        # return Response({"error":"transaction_Id needed for this transaction"}, status=status.HTTP_400_BAD_REQUEST)
                    try:
                        trx = TransactionsTable.objects.get(id=transactionId)
                    except (TransactionsTable.DoesNotExist):
                        #bushiness accessing widget without sep10
                        # new transaction from the widget
                        try:
                            transaction_p = update_PendingTransaction_Model(
                                transaction_amt=float(_data["amount"]) + float(GENERAL_TRANSACTION_FEE),
                                transaction_type="withdraw",
                                narration=_data["transaction_narration"],
                                transaction_hash=None,
                                user_block_address=_data["blockchain_address"],
                                phone_num=_data["phone_number"],
                                user_bank_account=_data["account_number"],
                                bank_name=_data["bank_name"],
                            )


                        except IntegrityError as e:
                            print("this endpoint",e)

                        # if "UNIQUE constraint failed" in e.args[0]:
                            return Response(
                                {
                                    "error": "there is a pending payment with this narration, please update transaction narration"
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        # return Response({"error":"transaction_Id not found"}, status=status.HTTP_400_BAD_REQUEST)
                    else:
                    # print(trx)
                        if trx.transaction_narration != ("sep"+transactionId):
                            return Response({"error":"invalid transaction Id"}, status=status.HTTP_400_BAD_REQUEST)
                        #update the sep transaction
                        try:
                            transaction_p = update_sep_transaction_no_ifp(
                                transaction_Id=transactionId,
                                transaction_amt=str(
                                    float(_data["amount"]) + float(GENERAL_TRANSACTION_FEE)
                                ),
                                transaction_type="withdraw",
                                narration=_data["transaction_narration"],
                                transaction_status="pending",
                                phone_num=_data["phone_number"],
                                user_bank_account=_data["account_number"],
                                bank_name=_data["bank_name"],
                                user_block_address=_data["blockchain_address"]
                                )
                            print("insert", transaction_p)
                            
                        except IntegrityError as e:
                            print(e)
                            return Response(
                                {
                                    "error": "there is a pending payment with this narration, please update transaction narration"
                                },
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                # else:
                _resp_data = {}
                _resp_data[
                    "message"
                ] = f"Please send Token to the address below, kindly note to add a transaction fee of {GENERAL_TRANSACTION_FEE} {STABLECOIN_CODE} to your transaction, \nOnce transaction is send to the below address, your account will be credited. Thank You"
                _resp_data["blockchain_address"] = STABLECOIN_ISSUER
                _resp_data["deposit_asset_code"] = STABLECOIN_CODE
                _resp_data["deposit_asset_issuer"] = STABLECOIN_ISSUER
                _resp_data["memo"] = f"{transaction_p.id}"
                _resp_data["user_details"] = _data
                _data["eta"] = "10min"

                # _resp_data["xdr"] = withdrawal_xdr

                return Response(_resp_data, status=status.HTTP_200_OK)
            # else:
            #     return Response(data={"message": "No merchant Available for Withdrawal at the moment, please check back later"}, status=status.HTTP_404_NOT_FOUND)

            else:
                return Response(
                    data={"message": "Insufficient Balance or error with your address"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            print("this error", serializer.errors)
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OFF_BOARDING_MA(APIView):
    def post(self, request):
        print("Need to handle api verifying users with both UID and pubkey")

        # ma thats want to offboard will call this endpoint with their UID and pub key
        # we need to check if the pub key is the same as the one in the database
        # check merchant allowed token to be sure they are not owing the protocol - if ALLOWToken is < than LICENCE_TOKEN they cant offboard, MA is holding fiat in their accty

        # if allowed and license token == dsame, they can offboard and we transfer their token back to their address within the protocol

        merchant_Id = request.data.get("merchant_Id")
        merchant_PubKey = request.data.get("merchant_PubKey")
        _data = {}
        _data["merchant_Id"] = merchant_Id
        _data["merchant_PubKey"] = merchant_PubKey
        serialized_obj = OffBoard_A_MerchantSerializer(data=_data)
        print(_data)
        if serialized_obj.is_valid():

            try:
                merchant_object = get_merchant_by_pubKey(merchant_PubKey)
            except MerchantsTable.DoesNotExist:
                return Response(
                    {"error": "Merchant does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                # mostly with passing in an incorrect combination of query
                print(e)
                return Response(
                    {"error": "You are passing in an incorrect combination of input, check and try again"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                # try:

                #     token_balance = TokenTable.objects.get(merchant=merchant_object)
                # except TokenTable.DoesNotExist:
                #     return Response(
                #         {"error": "Merchant Not found"},
                #         status=status.HTTP_404_NOT_FOUND,
                #     )
                # else:
                if merchant_object["account_id"] != merchant_Id:
                    return Response({
                        "status":"error",
                        "msg":"invalid account_id"
                    }, status=status.HTTP_400_BAD_REQUEST) 
                else:
                    if float(merchant_object["licenseTokenAmount"]) > 0:
                        if (
                            float(merchant_object["licenseTokenAmount"])
                            > float(merchant_object["allowedTokenAmount"])
                            and merchant_object['ifp_block_addr'] == merchant_PubKey
                        ):
                            response = {
                                "error": "You can't perform this transaction yet, you are holding some fiat in your account",
                                "outstanding_fiat": float(merchant_object["licenseTokenAmount"])
                                - float(merchant_object["allowedTokenAmount"]),
                            }
                            return Response(
                                response, status=status.HTTP_400_BAD_REQUEST
                            )
                        else:
                            print(
                                "Need to handle removing merchant before submission of transaction"
                            )
                            remove_merchant = delete_merchant(merchant_object["account_id"])
                            if remove_merchant == True:
                                try:
                                    raw_xdr = OffBoard_Merchant_with_Burn(
                                        recipient_pub_key=merchant_PubKey,
                                        amount=round(
                                            float(merchant_object["licenseTokenAmount"]), 7
                                        ),
                                        memo=merchant_Id,
                                        exchange_rate=round(
                                            float(
                                                merchant_object["stakedTokenExchangeRate"]
                                            ),
                                            7,
                                        ),
                                        total_staked_amt=round(
                                            float(merchant_object["stakedTokenAmount"]), 7
                                        ),
                                    )
                                except Exception as e:
                                    print(e)
                                    return Response(
                                        {"error": "something went wrong"},
                                        status=status.HTTP_400_BAD_REQUEST,
                                    )
                                else:
                                    logging.info(
                                        "We need to handle situations were merchant failed to submit the transaction, maybe by moving the merchant to a state that is  not accessible by the api"
                                    )
                                    MerchantsTable.objects.filter(
                                        UID=merchant_Id
                                    ).delete()


                                    
                                    _message = {}
                                    _message[
                                        "message"
                                    ] = "Please sign and submit the XDR below within 30min to complete the transaction"
                                    _message["raw_xdr"] = raw_xdr

                                    logging.info(
                                        f"Offboarding merchant {merchant_Id}, need to add interest calculation to the amount the merchant get"
                                    )
                                return Response(
                                    data=_message, status=status.HTTP_200_OK
                                )
                            else:
                                return Response(
                                    {"error": "Something went wrong"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                    elif float(merchant_object["licenseTokenAmount"])  <= 0:
                        return Response(
                            data={
                                "error": f"Merchant with public key {merchant_PubKey} is not fully register yet and so can't offBoard itself, please stake to the protocol address and try again"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                return Response(
                    {"error": "Merchant has no license token"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                {"error": serialized_obj.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    # def post(self, request):
    #     return Response(data={"ok"}, status=status.HTTP_200_OK)


class MerchantDepositConfirmation(APIView):
    """General endpoint for Merchants to confirm their deposit"""

    def get(self, request, *args, **kwargs):

        """
        Merchants use this endpoint to get list of all their pending transaction both for withdrawals and deposits
        this takes the merchant public key as arguments and return a list of pending transactions belonging  to the merchants
        """
        user_key = self.request.query_params.get("public_key")
        query_type =  self.request.query_params.get("query_type")
        if user_key and query_type == "ifp":
            try:
                all_transactions = get_all_transaction_for_merchant(
                    user_key
                    )
                print(all_transactions)
            except MerchantsTable.DoesNotExist:
                return Response(
                    {"error": "address not a merchant yet", 'status':"fail"}, status=status.HTTP_404_NOT_FOUND
                )
        elif user_key and query_type == "user":
            try:
                all_transactions =get_transaction_by_pubKey(user_key)
            except TransactionsTable.DoesNotExist:
                return Response(
                    {"error": "address has no transaction yet", 'status':"fail"}, status=status.HTTP_404_NOT_FOUND
                )
        else:
            return Response(
            data={"error": "Please provide a public key and query_type"},
            status=status.HTTP_400_BAD_REQUEST,
            )

        if all_transactions:

            for transaction in all_transactions:
                if transaction.transaction_type == "withdraw":
            #         # transaction.transaction_amount = float(transaction.transaction_amount) - float(GENERAL_TRANSACTION_FEE)
                    withdrawable_amount = float(transaction.transaction_amount) - float(GENERAL_TRANSACTION_FEE)
                    transaction.withdrawable_deposit_amount = withdrawable_amount
            #         print(transaction)
            #         print(transaction.transaction_amount)
                elif transaction.transaction_type == "deposit":
                    transaction.withdrawable_deposit_amount = transaction.transaction_amount

                    print(transaction.withdrawable_deposit_amount)
            return Response(
                {"all_transactions":TransactionSerializer(all_transactions, many=True).data, "msg":"for withdrawal transactions, deduct fee before sending to the User", 'status':"success"},
                status=status.HTTP_200_OK,
            )
        else:
            return Response(
                data={"error": "No transactions found", "status":"fail"},
                status=status.HTTP_404_NOT_FOUND,
            )


    def post(self, request):
        # to do
        print(
            "Merchant should be able to specify the amount they received in their bank acct, rather than we processing based on the expected amount"
        )
        # during a deposit confirmation, 
        # the total supply of stablecoin increase onchain 
        # and the total supply of allowed token increase ON THE STABLECOIN ACCT(THIS is what is used to swap NGNALLOW -> NGN) 
        # and the allowed token will be decrease on the IFP acct(to the tune of their license token)
        # Allowed token plus uncleared_bal should always equal to the amount of license token
        
        #uncleared column is used for updating total pending transaction
            # when a user query for deposit and is assigned an IFP(this will increase the IFP uncleared_Bal)
            # when IFP have Processed transaction, this will reduced the IFP uncleared_bal
            # ---------------
            # when a user query for withdrawals(nothing happens as this does not immediately assign an iFp to that user)
            # once protocol picks up transaction for a user's withdrawal and an IFP is assigned, The IFP unclear_bal increase
            # once the IFP process the transaction and notify the user, the IFP uncleared_bal decrease
            # allowed token increases
        # during a withdrawal transaction, IFP uncleared_bal will reduce and their allowed token balance will increase ny the amount of transaction
        """
        Merchants send transaction Id of a transaction that has been processed by the merchant
        endpoint for merchants to submit signed transaction to the blockchain
        Endpoint returns an xdr that needs to be signed and submitted to the blockchain by the merchants, we provide an endpoint to submit transactions
        """
        merchants_Id = request.data.get("merchant_id")
        deposit_withdrawal_Id = request.data.get("transaction_Id")
        merchant_pubKey = request.data.get("merchant_pubKey")
        # transaction_type = request.data.get("transaction_type")

        if merchants_Id and deposit_withdrawal_Id and merchant_pubKey:
            try:
                merchants_txs = get_pending_transactions(merchants_Id)
                merchant_table = MerchantsTable.objects.get(UID=merchants_Id)
            except (MerchantsTable.DoesNotExist, TransactionsTable.DoesNotExist):
                return Response(
                    {"error": f"Merchant with id {merchants_Id} not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            else:
                for transaction in merchants_txs:
                    if (
                        transaction.id == deposit_withdrawal_Id
                        and transaction.transaction_type == "deposit"
                        and merchant_pubKey == merchant_table.blockchainAddress
                    ):
                        # in a deposit transaction, this only rectify the unclear_bal, allowToken will be untouched
                        # Allowed token will be updated onchain through the transaction
                        depositor_address = transaction.users_address
                        amount_deposit = transaction.transaction_amount
                        # memo = transaction.transaction_narration
                        xdr_obj = merchants_swap_ALLOWED_4_NGN_Send_payment_2_depositor(
                            memo_text=str(deposit_withdrawal_Id),
                            amount=amount_deposit,
                            depositor_pubKey=depositor_address,
                            trustorPub=merchant_pubKey,
                        )

                        merchant_table = MerchantsTable.objects.get(UID=merchants_Id)
                        _data = {
                            "merchant": merchant_table,
                            "xdr_object": xdr_obj,
                            "id": transaction.id,
                        }
                        xdr_serializer = XdrGeneratedTransactionSerializer(data=_data)

                        if xdr_serializer.is_valid():
                            # xdr_serializer.save()
                            update_xdr_table(
                                transaction_type="deposit",
                                tx_xdr=xdr_obj,
                                tx_status="pending xdr generated",
                                merchant=merchants_Id,
                                transaction_Id=deposit_withdrawal_Id,
                            )

                            try:
                                update_cleared_uncleared_bal(merchants_Id, "deposit_cleared", transaction.transaction_amount)

                                # update the state of the transaction
                                update_transaction_status(transaction_id=deposit_withdrawal_Id, status='completed')
                            
                            except Exception as e:
                                # notify admin
                                print(e)
                                return Response(
                                    {"error": "Something went wrong"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                            else:
                                # need to update transaction table hash for future refrences
                                return Response(
                                    {
                                        "message": "please sign and submit the xdr below",
                                        "xdr": xdr_obj,
                                    },
                                    status=status.HTTP_200_OK,
                                )
                        else:
                            return Response(
                                {"error": xdr_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    elif (
                        transaction.id == deposit_withdrawal_Id
                        and transaction.transaction_type == "withdraw"
                        and merchant_pubKey == merchant_table.blockchainAddress
                    ):
                        print("withdrawal Transaction")
                        print("we need to specify the amount the IFP got in their back acct with that memo")
                        # once transaction has been processed, the uncleared_bal should decrease with the amount processed - fee
                        try:
                            withdrawal_xdr = User_withdrawal_from_protocol(
                                merchant_pubKey,
                                transaction.transaction_amount,
                                str(deposit_withdrawal_Id),
                                transaction.users_address,
                            )
                        except Exception as E:
                            # print(E)
                            # notify admin
                            return Response(
                                {"error": "Something went wrong"},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                        else:
                            merchant_table = MerchantsTable.objects.get(
                                UID=merchants_Id
                            )
                            _data = {
                                "merchant": merchant_table,
                                "xdr_object": withdrawal_xdr["hash"],
                                "id": transaction.id,
                            }
                        xdr_serializer = XdrGeneratedTransactionSerializer(data=_data)
                        if xdr_serializer.is_valid():
                            update_xdr_table(
                                transaction_type="withdraw",
                                tx_xdr=withdrawal_xdr["hash"],
                                tx_status="pending xdr generated",
                                merchant=merchants_Id,
                                transaction_Id=deposit_withdrawal_Id,
                            )
                            # ifp should see amount to send to user -fee
                            # and their allowed token should be -fee
                            try:
                                update_cleared_uncleared_bal(merchants_Id, "cleared", transaction.transaction_amount)
                        
                                update_transaction_status(deposit_withdrawal_Id, status='completed')
                            except Exception as e:
                                # notify admin
                                # print(e)
                                return Response(
                                    {"error": "Something went wrong"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                            else:
                                # need to update transaction table hash for future references
                                return Response(
                                    {
                                        "message": "ok",
                                        "transaction_hash": withdrawal_xdr["hash"],
                                    },
                                    status=status.HTTP_200_OK,
                                )
                        else:
                            return Response(
                                {"error": xdr_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST,
                            )
                    else:
                        print("Transaction not found")
                        pass
                return Response(
                    {
                        "message": f"Transaction with id {deposit_withdrawal_Id} not found with this merchant or merchant and public key not related or transaction has already been completed"
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

        else:
            return Response(
                data={"error": "Please provide all required params"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # add authentication for merchant
        # merchant sends an instruction to backend to contract the transaction
        # backend will construct the transaction and back to the merchant as xdr
        # merchant will sign and send the xdr to the blockchain
        # how do we know the merchants is the right person

        # swap allowAsset for NGN - src-acct = merchants
        # Send NGN payments to recipient or depositors acct - fees - merchants
        # credit merchants with fees in NGN - merchants
        # Credit protocol acct with NGN - merchants
        # wrap transaction in feebump - protocol acct
        # send to blockchain

    def delete(self, request):
        """Endpoint to cancel a pending transaction from a IFP list of pending transaction and release their uncleared bal"""
        # merchant should be authenticated before calling this endpoint to cancel transactions
        # once merchant query this endpoint with the right transactionID, if transaction still pending it should be cancel
        # transaction can only be cancel only after 30min after it was initiated and only the MA that owns the transaction
        # add sep10 authentication for all endpoint
        pass



class AllTokenTotalSupply(APIView):
    """
    Endpoint to get all token supply
    """

    def get(self, request):
        try:
            assets_list = protocolAssetTotalSupply()
        except Exception:
            return Response(
                {"error": f"error getting details for this endpoint"},
                status=status.HTTP_404_NOT_FOUND,
            )
        else:

            return Response(assets_list, status=status.HTTP_200_OK)

        # supply of allowed Token
        # supply of licxense token
        # supply of stablecoin
        # total amount in staking vault

        # token_supply = TokenSupply.objects.all()
        # serializer = TokenSupplySerializer(token_supply, many=True)
        # return Response("ok", status=status.HTTP_200_OK)


class AccountDetails(APIView):
    def get(self, request):
        """
        Endpoint returns details of a given address, initial it would support only merchant and then all protocol users
        """
        try:
            pub_key = check_stellar_address(request.query_params.get("account_id"))
        except Exception as _a:
            print(_a)
            return Response(
                {"msg": "Not a valid Stellar address", "status":"fail"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                merchant = get_merchant_by_pubKey(pub_key)
            except (MerchantsTable.DoesNotExist, IndexError):
                return Response(
                    {"msg": f"merchant with account id {pub_key} does not exist", "status":"fail"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            else:
                fiat_in_bank =  round(float(merchant["licenseTokenAmount"])
                    - (float(merchant["allowedTokenAmount"]) + float(merchant["unclear_bal"])),
                        7,
                    )

                data = {}
                data["Amount_staked"] = merchant["stakedTokenAmount"]
                data["value_in_stablecoin"] = merchant["licenseTokenAmount"]
                data["exchange_rate"] = merchant["stakedTokenExchangeRate"]
                data["pending_transaction"] = merchant["unclear_bal"]
                data["total_fiat_held_in_bank_acct"] = fiat_in_bank
                data["allowed_token"] = float(merchant["licenseTokenAmount"]) - (float(merchant["unclear_bal"]) + float(fiat_in_bank))
                data["image"] = f"https://id.lobstr.co/{pub_key}.png"
                data["status"] = "successful"
                merchant.update(data)

                return Response(merchant, status=status.HTTP_200_OK)

# Stellar Toml
class StellarToml(APIView):
    def get(self, requests):
        import toml

        toml_config = toml.load("Api/templates/Api/stellar.toml")
        req_toml_config = toml.dumps(toml_config)
        return HttpResponse(
            req_toml_config, headers={"Content-Type": "text/plain; charset=utf-8"}
        )


class SubmitAnXdr(APIView):
    def post(self, request):
        xdr_object = XdrSerializer(data=request.data)
        if xdr_object.is_valid():
            # submit
            server_ = get_horizon_server()

            str_xdr = xdr_object.data.get("signed_xdr")
            transactionEnvelop = TransactionEnvelope.from_xdr(
                str_xdr, get_network_passPhrase()
            )
            tx_signature = transactionEnvelop.signatures
            if len(tx_signature) < 1:
                return Response(
                    {"msg": "unsigned transaction"}, status=status.HTTP_400_BAD_REQUEST
                )
            elif len(tx_signature) >= 1:
                try:
                    tx_submit = server_.submit_transaction(
                    transactionEnvelop, skip_memo_required_check=True
                )
                except (NotFoundError, BadRequestError, BadResponseError) as tx_error:
                    # print(tx_error)
                    return Response({"msg":"there is an error with this transaction"}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    return Response(
                        {
                            "msg": "see transaction details below",
                            "transaction_response": tx_submit,
                        },
                        status.HTTP_200_OK,
                    )
        else:
            return Response(xdr_object.errors, status.HTTP_400_BAD_REQUEST)

@api_view(["GET"])
def auditProtocol(requests):
    protocol_audit = protocolAudit()
    return Response({"data":protocol_audit, "protocol_token_totalSupply":protocolAssetTotalSupply()}, status=status.HTTP_200_OK)



@api_view(["POST"])
def transactionStatus(requests):
    query_memo = requests.data.get("transactionId")
    msg = {"msg":"we are updating your balance right away", "status":"success"}
    if query_memo == None or query_memo == "":
        return Response({
            "msg":"transactionId must be provided or you have provided an transactionId",
            "status":"fail"
        }, status=status.HTTP_400_BAD_REQUEST)
    else:
        account = None
        if query_memo.startswith("500"):
            account = STAKING_ADDRESS
        elif query_memo.startswith("200"):
            account = STABLECOIN_ISSUER
        else:
            return Response({
                "msg":"unknown query error, notify admin",
                "status":"fail"
            }, status=status.HTTP_400_BAD_REQUEST)

        transaction = getStellar_tx_fromMemo(memo=query_memo, account=account)
        if len(transaction) >= 1:
            active_transaction =transaction[0]
            ledger_Id = active_transaction["ledger"]
            block_tx_id = active_transaction["paging_token"]

            kwargs = {
                "memo": query_memo,
                "ledger_tx": ledger_Id,
                "block_tx_id": block_tx_id
            }
            if account == STABLECOIN_ISSUER:
                kwargs.update({
                    "_address": STABLECOIN_ISSUER,
                    "_asset_code": STABLECOIN_CODE,
                    "_asset_issuer": STABLECOIN_ISSUER
                })

            isTransaction_Valid.delay(**kwargs)

            return Response(msg, status=status.HTTP_200_OK)
        else:
            return Response({
                "msg":"no transaction with this transactionId found yet on the protocol account, please try again later",
                "status":"fail"
            }, status=status.HTTP_400_BAD_REQUEST)




@api_view(["GET"])
def Sep6Deposit(requests):
    """
    Endpoint for sep6 deposit
    Payment transaction will be send with claimable balance during tranfer if the account has not
    """
    sep6Data = Sep6DepositSerializer(data=requests.query_params)
    if sep6Data.is_valid():
        is_asset_trusted = is_Asset_trusted(
            sep6Data.validated_data["account"], 1, STABLECOIN_ISSUER
        )
        if is_asset_trusted[0] == True:

            # merchants_list = TokenTableSerializer(all_merchant_token_bal(), many=True)
            amount = sep6Data.validated_data["amount"]
            account = sep6Data.validated_data["account"]
            transaction_narration = uidGenerator(
                15
            )  # This should be changed to random wordlist

            MA_selected = merchants_to_process_transaction(
                account, amount, bank=None
            )
            if MA_selected:
                try:
                    update_pending_transaction_model(
                        MA_selected["merchant"]["UID"],
                        transaction_amt=str(
                            float(amount) + float(GENERAL_TRANSACTION_FEE)
                        ),
                        transaction_type="deposit",
                        transaction_status="pending",
                        narration=transaction_narration,
                        transaction_memo=MA_selected["merchant"]["UID"],
                        phone_num=MA_selected["merchant"]["phoneNumber"],
                        user_bank_account=MA_selected["merchant"]["bankAccount"],
                        bank_name=MA_selected["merchant"]["bankName"],
                        user_block_address=account,
                    )
                except IntegrityError as e:
                    print(e)
                    if "UNIQUE constraint failed" in e.args[0]:
                        return Response(
                            {
                                "error": "there is a pending payment with this narration, please update transaction narration"
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    else:
                        # notify admin
                        return Response(
                            {"error": "something went wrong"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    update_cleared_uncleared_bal(
                        MA_selected["merchant"]["UID"], "uncleared", amount
                    )
                    data = {
                        "eta": "5 minutes",
                        "min_amount": 1000,
                        "fee": GENERAL_TRANSACTION_FEE,
                        "how": f"Please transfer your funds to the account number specified below. Your deposit reference is {transaction_narration}, please put this as your transfers remarks/memo.",
                        "extra_info": {
                            "bank_name": MA_selected["merchant"]["bankName"],
                            "account_number": MA_selected["merchant"]["bankAccount"],
                            "transaction_ref": transaction_narration,
                            "phoneNumber": MA_selected["merchant"]["phoneNumber"],
                        },
                    }
                return Response(data=data, status=status.HTTP_200_OK)

            else:
                return Response(
                    data={
                        "error": "No merchant found",
                        "message": "There might be no merchant found at the moment or you are entering a very high amount",
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            assets = {"code": STABLECOIN_CODE, "issuer": STABLECOIN_ISSUER}
            return Response(
                {
                    "error": "your address must add trustline to the following assets",
                    "assets": assets,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    else:
        return Response(sep6Data.errors, status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
def sepInfo(requests):
    return JsonResponse(SEP_INFO)


@api_view(["GET"])
def sep6Withdrawal(requests):
    _data = requests.query_params
    serializer_Data = Sep6WithdrawalSerializer(data=_data)
    if serializer_Data.is_valid():
        memo = uidGenerator(13)
        try:
            transaction_p = update_PendingTransaction_Model(
                transaction_amt=_data["amount"],
                transaction_type="withdraw",
                narration=memo,
                transaction_hash=None,
                user_block_address=_data["account"],
                phone_num=None,
                user_bank_account=_data["dest"],
                bank_name=_data["dest_extra"],
            )
        except Exception as Error:
            # print(Error)
            # Notify admin
            return Response(Error.args, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = {
                "account_id": STABLECOIN_ISSUER,
                "memo_type": "text",
                "memo": transaction_p.id,
                "eta": 120,
                "min_amount": 1000,
                "fee_fixed": GENERAL_TRANSACTION_FEE,
            }

        return Response(data, status=status.HTTP_200_OK)
    else:
        return Response(serializer_Data.errors, status=status.HTTP_400_BAD_REQUEST)


class WEBAUTHENDPOINT(APIView):
    """
    Web authentication endpoint for stellar sep10
    """
    #write a get view that check two params
    def get(self, request):
        #get query params
        query_params = request.query_params
        print(query_params.get("account"))
        print(query_params.get("memo"))
        print(query_params.get("home_domain"))
        
        account = query_params.get("account")
        home_domain = query_params.get("home_domain")
        memo = query_params.get("memo")
        if not account:
            return Response(
                {"error": "no 'account' provided"}, status=status.HTTP_400_BAD_REQUEST
            )

        if memo:

            try:
                memo = int(query_params["memo"])
            except ValueError:
                return Response(
                    {"error": "invalid 'memo' value. Expected a 64-bit integer."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if query_params["account"].startswith("M"):
                return Response(
                    {
                        "error": "'memo' cannot be passed with a muxed client account address (M...)"
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
                #add a check to check for valid domain 
        if home_domain:
            pass
        elif not home_domain:
            home_domain  = DOMAIN
        build_challenge = build_challenge_tx(PROTOCOL_DELEGATED_SIGNER, account, home_domain)

        return Response({"status":"successful",
                        "transaction":f"{build_challenge}",
                        "network_passphrase": get_network_passPhrase()},
                    status=status.HTTP_200_OK,
                )
    def post(self, request) -> Response:
        """
        Validate a signed transaction and generate a jwt sep10
        """

        envelope_xdr = request.data.get("transaction")
        if not envelope_xdr:
            return Response(
                "'transaction' is required",
                status=status.HTTP_400_BAD_REQUEST,
            )
        if envelope_xdr:
            try:
                auth_domain = os.path.join(DOMAIN, "auth")
                adc, client_domain = server_verify_challenge(challenge=envelope_xdr, home_domain=DOMAIN, web_auth_domain=DOMAIN)
            except Exception as error:
                print("this error")
                print(error.args[0])
                return Response({"error":"error verifying your transaction"}, status=status.HTTP_400_BAD_REQUEST)
            print("this is the verified response from the server", adc, client_domain)
            
            token = generate_jwt(challenge=envelope_xdr, client_domain=client_domain)
            return Response({
                "token":f"{token}"
            }, status=status.HTTP_200_OK)

class WidgetLinkDeposit(APIView):
    # get sep10 token
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "Api/widgetDeposit.html"
    def get(self, requests):
        data = {"test": "ok"}
        return Response(data)

class WidgetLinkWithdrawal(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = "Api/widgetWithdrawal.html"
    def get(self, requests):
        data = {"test": "ok"}
        return Response(data)
    
class Sep24DepositFlow(APIView):
    """
    endpoint post method handles deposit transaction
    """
    # renderer_classes = [TemplateHTMLRenderer]
    
    def post(self, request, *args, **kwargs):
        sep24data = Sep6DepositSerializer(data=request.data)
        if sep24data.is_valid():
            _id = Id_generator()
            url_= request.build_absolute_uri()
            pares_url = urlparse(url_)
            
            sep_url = pares_url.scheme + "://" + pares_url.netloc +"/widgetDeposit"
            data = insert_sep_transaction(_id, transaction_type="deposit", transaction_amt=0, narration=("sep" + str(_id)), transaction_status="Pending")
            data = {
                "type": "interactive_customer_info_needed",
                "url":f"{sep_url}/deposit?transaction_id={_id}&asset_code={STABLECOIN_CODE}&asset_issuer={STABLECOIN_ISSUER}&account={request.data.get('account')}",
                #this should then open up url to the widget model, from here we can stick to the flow for the deposit from the protocol endpoint
                "id": f"{_id}"
                }
            return Response(data, status=status.HTTP_200_OK)
            
        else:
            return Response({"error":sep24data.errors}, status.HTTP_400_BAD_REQUEST)
        
        # print(sep24data)
        # print("this is the endpoint that was called")
        # return Response(template_name = "Api/sep24.html")

class Sep24TransactionEndpoint(APIView):
    def get(self, request, *args, **kwargs):
        
        transactionId = self.request.query_params.get("id")
        ex_transactionId = self.request.query_params.get("stellar_transaction_id")
        in_transactionId = self.request.query_params.get("external_transaction_id")
        print(transactionId)

        if transactionId is None:
            return Response({ "error": "this query requires an 'id' "}, status=status.HTTP_400_BAD_REQUEST)
        try:

            transaction = TransactionsTable.objects.filter(id=transactionId)
        except TransactionsTable.DoesNotExist:
            return Response({"error":"invalid transaction Id "}, status=status.HTTP_400_BAD_REQUEST)
        
        # print(transaction)
        if transaction:
            transaction_data = transaction.values(
                transaction_id=F("id"),
                kind=F("transaction_type"),
                status=F("transaction_status"),
                started_at = F("created_at"),
                amount = F("transaction_amount")
            )
            
            transaction = transaction_data[0]
            _data = {}
            _data["eta"] = 3600
            _data["external_transaction_id"] = None
            _data["amount_fee"]= GENERAL_TRANSACTION_FEE
            transaction.update(_data)

            return  JsonResponse({"transaction":transaction}, safe=False, status=status.HTTP_200_OK)
        else:
            return Response({"error":"invalid transaction Id "}, status=status.HTTP_400_BAD_REQUEST)


class Sep24WithdrawalFlow(APIView):
    def post(self, request, *args, **kwargs):
        sep24data = Sep6DepositSerializer(data=request.data)
        if sep24data.is_valid():
            _id = Id_generator()
            url_= request.build_absolute_uri()
            pares_url = urlparse(url_)
            
            sep_url = pares_url.scheme + "://" + pares_url.netloc +"/widgetWithdrawal"
            data = insert_sep_transaction(_id, transaction_type="withdraw", transaction_amt=0, narration=("sep" + str(_id)), transaction_status="Pending")
            data = {
                "type": "interactive_customer_info_needed",
                "url":f"{sep_url}/withdrawal?transaction_id={_id}&asset_code={STABLECOIN_CODE}&asset_issuer={STABLECOIN_ISSUER}&account={request.data.get('account')}",
                #this should then open up url to the widget model, from here we can stick to the flow for the deposit from the protocol endpoint
                "id": f"{_id}"
                }
            return Response(data, status=status.HTTP_200_OK)
            
        else:
            return Response({"error":sep24data.errors}, status.HTTP_400_BAD_REQUEST)
        



# class TransactionExpire(APIView):
#     """
#     Endpoint for merchant to cancel a transaction after a specified time and the transaction has not been processed
#     """
#     def get(self, requests):
#         """
#         get a transaction status
#         endpoint used to check transaction status if pending, complete or fail
#         """
#         pass
#     def post(self, requests):
#         """
#         endpoint for canceling a transaction after a specific period of time 
#         endpoint takes only a valid transaction_id
#         """
#         transaction_id = requests.data.get("transaction_id")
#         if transaction_id == None:
#             return Response({"message":"transaction_id is a required params"}, status=status.HTTP_400_BAD_REQUEST)
        
#         else:
#             transaction = get_transaction_By_Id(transaction_id=transaction_id)
#             print(transaction.transaction_status)
#             # _data = TransactionSerializer(transaction).data
#             # the client is meant to monitor transaction for timeout, transaction with less than 1hrs should not be allow to be cancel
#             if transaction.transaction_status == "completed":
#                 _res_data = {"message":"this transaction has been completed"}
#                 return Response(_res_data, status=status.HTTP_400_BAD_REQUEST)
#             elif transaction.transaction_status == "pending":
#                 # PROBLEM
#                     # - Whats stopping anyone from calling the endpoint and just passing the transaction 
#                     #       id as parameter and cancelling the transaction without the IFP consent
#                 # SOL
#                     # 1. Enable Sep-10 for the endpoint
#                     # 2. create a transaction to be sign and send back to the protocol(almost sep-10 flow too)
#                 # change transaction status from IFP account to cancelled,
#                 # release IFP pending balance back to their account
#                 # when transaction is cancelled, the amount for the transaction needs to be added back to the IFP allowedToken balance
#                 # adc = update_transaction_status(transaction_id=transaction_id, status='cancel')
#                 print(transaction.merchantstable_id)
#                 _data ={"ok":"ok"}
#                 return Response(_data, status=status.HTTP_200_OK)



                




        # print(transaction)
        # print(_data)
        # return Response()
        # _data ={"ok":"ok"}
        # return Response(_data, status=status.HTTP_200_OK)
