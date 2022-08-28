import logging
import re

from Blockchains.Stellar.operations import (
    ALLOWED_AND_LICENSE_P_ADDRESS,
    ALLOWED_TOKEN_CODE,
    LICENSE_TOKEN_CODE,
    LICENSE_TOKEN_ISSUER,
    PROTOCOL_FEE_ACCOUNT,
    STABLECOIN_CODE,
    STABLECOIN_ISSUER,
    STAKING_ADDRESS,
    OffBoard_Merchant_with_Burn,
    User_withdrawal_from_protocol,
    get_network_passPhrase,
    is_Asset_trusted,
    get_horizon_server,
    merchants_swap_ALLOWED_4_NGN_Send_payment_2_depositor,
)
from Blockchains.Stellar.utils import check_address_balance, check_stellar_address
from decouple import config
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse
from modelApp.models import MerchantsTable, TokenTable, TransactionsTable, TxHashTable
from modelApp.utils import (
    all_merchant_token_bal,
    assign_transaction_to_merchant,
    check_xdr_if_already_exist,
    delete_merchant,
    get_merchant_by_pubKey,
    is_transaction_memo_valid,
    remove_transaction_from_merchants_model,
    return_all_objects_for_a_merchants,
    update_cleared_uncleared_bal,
    update_pending_transaction_model,
    update_PendingTransaction_Model,
    update_xdr_table,
)
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView
from stellar_sdk import TransactionEnvelope, TrustLineFlags

from utils.utils import uidGenerator

from .serializers import (
    EventSerializer,
    Fiat_Off_RampSerializer,
    XdrSerializer,
    Fiat_On_RampSerializer,
    MerchantsTableSerializer,
    OffBoard_A_MerchantSerializer,
    TokenTableSerializer,
    TransactionSerializer,
    XdrGeneratedTransactionSerializer,
    Sep6DepositSerializer,
    Sep6WithdrawalSerializer,
)
from .utils import (
    PROTOCOL_COMMISSION,
    STAKING_TOKEN_ISSUER,
    Notifications,
    isTransaction_Valid,
    merchants_to_process_transaction,
)
from rest_framework.renderers import TemplateHTMLRenderer

# from .renderers import TomlRenderer
STAKING_TOKEN = config("STAKING_TOKEN_CODE")
STAKING_ADDRESS = config("STAKING_ADDRESS")
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")


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
        "transactions": {"enabled": True, "authentication_required": False},
        "transaction": {"enabled": False, "authentication_required": False},
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
                        "msg": f"please send {STABLECOIN_CODE} to the below details",
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

        amount = request.data.get("amount")
        bankType = request.data.get("bankType")
        blockchainAddress = request.data.get("blockchainAddress")
        transaction_narration = request.data.get("narration")
        check_data = Fiat_On_RampSerializer(data=request.data)
        if check_data.is_valid():
            # check if the address has a trustline for the NGN asset
            is_asset_trusted = is_Asset_trusted(blockchainAddress, 1, STABLECOIN_ISSUER)

            if is_asset_trusted[0] == True:
                merchants_list = TokenTableSerializer(
                    all_merchant_token_bal(), many=True
                )

                MA_selected = merchants_to_process_transaction(
                    merchants_list.data, amount, bankType
                )
                # add filtering process for deposit and check for multiple deposit option
                if MA_selected:
                    try:
                        update_pending_transaction_model(
                            MA_selected["merchant"]["UID"],
                            transaction_amt=str(
                                float(amount) + float(GENERAL_TRANSACTION_FEE)
                            ),
                            transaction_type="deposit",
                            narration=transaction_narration,
                            transaction_memo=MA_selected["merchant"]["UID"],
                            phone_num=MA_selected["merchant"]["phoneNumber"],
                            user_bank_account=MA_selected["merchant"]["bankAccount"],
                            bank_name=MA_selected["merchant"]["bankName"],
                            user_block_address=blockchainAddress,
                        )
                    except IntegrityError as e:
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
                            "message": f"Send funds to account below with the following details, the correct amount to send is {float(amount) + float(GENERAL_TRANSACTION_FEE)}, please include your narration when making deposit in from your bank account",
                            "memo": MA_selected["merchant"]["UID"],
                            "amount": amount,
                            "fee": GENERAL_TRANSACTION_FEE,
                            "amount_to_pay": float(amount)
                            + float(GENERAL_TRANSACTION_FEE),
                            "narration": transaction_narration,
                            "Bank Name": MA_selected["merchant"]["bankName"],
                            "account_number": MA_selected["merchant"]["bankAccount"],
                            "phoneNumber": MA_selected["merchant"]["phoneNumber"],
                            "eta": "5 minutes",
                        }

                        return Response(data=data, status=status.HTTP_200_OK)
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
                        "error": f"your address must add trustline to the following assets and also have enough balance for {STAKING_TOKEN}",
                        "assets": assets,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            return Response(
                {"error": check_data.errors}, status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request):
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
        check_args = Fiat_Off_RampSerializer(data=_data)
        if check_args.is_valid() and memo:
            try:

                pending_merchant_tx = return_all_objects_for_a_merchants(memo)
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
                        # print(i)
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

    def get(self, request):
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
        serializer = Fiat_Off_RampSerializer(data=_data)
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
                try:

                    transaction_p = update_PendingTransaction_Model(
                        transaction_amt=_data["amount"],
                        transaction_type="withdraw",
                        narration=_data["transaction_narration"],
                        transaction_hash=None,
                        user_block_address=_data["blockchain_address"],
                        phone_num=_data["phone_number"],
                        user_bank_account=_data["account_number"],
                        bank_name=_data["bank_name"],
                    )

                except IntegrityError as e:
                    # print(e)
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
                    # update_cleared_uncleared_bal(
                    #     selected_ma["merchant"]["UID"], "uncleared", _data["amount"])
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
            return Response(data=serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OFF_BOARDING_MA(APIView):
    def get(self, request):
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
        if serialized_obj.is_valid():

            try:
                merchant_object = get_merchant_by_pubKey(merchant_PubKey)
            except MerchantsTable.DoesNotExist:
                return Response(
                    {"error": "Merchant does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            except Exception as e:
                # print(e)
                return Response(
                    {"error": "something went wrong"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                try:

                    token_balance = TokenTable.objects.get(merchant=merchant_object)
                except TokenTable.DoesNotExist:
                    return Response(
                        {"error": "Merchant Not found"},
                        status=status.HTTP_404_NOT_FOUND,
                    )
                else:
                    if token_balance.licenseTokenAmount > 0:
                        if (
                            token_balance.licenseTokenAmount
                            > token_balance.allowedTokenAmount
                            and merchant_object.blockchainAddress == merchant_PubKey
                        ):
                            response = {
                                "error": "You can't perform this transaction yet, you are holding some fiat in your account",
                                "outstanding_fiat": token_balance.licenseTokenAmount
                                - token_balance.allowedTokenAmount,
                            }
                            return Response(
                                response, status=status.HTTP_400_BAD_REQUEST
                            )
                        else:
                            print(
                                "Need to handle removing merchant before submission of transaction"
                            )
                            remove_merchant = delete_merchant(merchant_object.UID)
                            if remove_merchant == True:
                                try:
                                    raw_xdr = OffBoard_Merchant_with_Burn(
                                        recipient_pub_key=merchant_PubKey,
                                        amount=round(
                                            float(token_balance.licenseTokenAmount), 7
                                        ),
                                        memo=merchant_Id,
                                        exchange_rate=round(
                                            float(
                                                token_balance.stakedTokenExchangeRate
                                            ),
                                            7,
                                        ),
                                        total_staked_amt=round(
                                            float(token_balance.stakedTokenAmount), 7
                                        ),
                                    )
                                except Exception as e:
                                    # print(e)
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
                    elif token_balance.licenseTokenAmount == 0:
                        return Response(
                            data={
                                "error": f"Merchant with public key {merchant_PubKey} is not fully register yet and so can offBoard itself, please stake to the protocol address and try again"
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

    def post(self, request):
        return Response(data={"ok"}, status=status.HTTP_200_OK)


class MerchantDepositConfirmation(APIView):
    """General endpoint for Merchants to confirm their deposit"""

    def get(self, request, *args, **kwargs):

        """
        Merchants use this endpoint to get list of all their pending transaction both for withdrawals and deposits
        this takes the merchant public key as arguments and return a list of pending transactions belonging  to the merchants
        """
        merchant_public_key = self.request.query_params.get("merchant_public_key")
        if merchant_public_key:
            try:
                merchant_details = get_merchant_by_pubKey(
                    merchant_pubKey=merchant_public_key
                )
            except MerchantsTable.DoesNotExist:
                return Response(
                    {"error": "Merchant not found"}, status=status.HTTP_404_NOT_FOUND
                )
            pending_transactions = return_all_objects_for_a_merchants(
                merchant_details.UID
            )
            if pending_transactions:
                return Response(
                    TransactionSerializer(pending_transactions, many=True).data,
                    status=status.HTTP_200_OK,
                )
            else:
                return Response(
                    data={"error": "No pending transactions found"},
                    status=status.HTTP_404_NOT_FOUND,
                )
        else:
            return Response(
                data={"error": "Please provide merchant public key"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def post(self, request):
        # to do
        print(
            "Merchant should be able to specify the amount they recieved in their bank acct, rather than we processing based on the expected amount"
        )
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
                merchants_txs = return_all_objects_for_a_merchants(merchants_Id)
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
                                remove_transaction_from_merchants_model(
                                    merchants_Id, deposit_withdrawal_Id
                                )
                            except Exception as e:
                                # notify admin
                                # print(e)
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

                            try:
                                remove_transaction_from_merchants_model(
                                    merchants_Id, deposit_withdrawal_Id
                                )
                            except Exception as e:
                                # notify admin
                                # print(e)
                                return Response(
                                    {"error": "Something went wrong"},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )
                            else:
                                # need to update transaction table hash for future refrences
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
                        "message": f"Transaction with id {deposit_withdrawal_Id} not found with this merchant or merchant and public key not related"
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

        pass


class AllTokenTotalSupply(APIView):
    """
    Endpoint to get all token supply
    """

    def get(self, request):
        server = get_horizon_server()

        accts = {
            ALLOWED_AND_LICENSE_P_ADDRESS: ALLOWED_TOKEN_CODE,
            STABLECOIN_ISSUER: STABLECOIN_CODE,
        }

        _asset_supply = {}
        for i in range(len(accts)):
            _keys = list(accts.keys())[i]
            _values = list(accts.values())[i]
            try:
                bala = server.assets().for_code(_values).for_issuer(_keys).call()
                for i in bala["_embedded"]["records"]:
                    _asset_supply[_values] = {
                        "total_accounts": i["accounts"],
                        "total_balance": i["balances"],
                    }

            except Exception as E:
                # print(E)
                return Response(
                    {"error": f"getting details for this endpoint"},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(_asset_supply, status=status.HTTP_200_OK)

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
            pub_key = check_stellar_address(request.data.get("account_id"))
        except Exception as _a:
            # print(_a)
            return Response(
                {"msg": "Not a valid Stellar address"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            try:
                merchant = get_merchant_by_pubKey(pub_key)
                # print(merchant)
                # print(merchant.UID)

                # print(".")

            except MerchantsTable.DoesNotExist:
                return Response(
                    {"msg": f"merchant with account id {pub_key} does not exist"},
                    status=status.HTTP_404_NOT_FOUND,
                )
            else:

                try:
                    merchant_bal = TokenTable.objects.get(merchant=merchant)
                except TokenTable.DoesNotExist:
                    return Response(
                        {"msg": "Merchant not found"}, status=status.HTTP_404_NOT_FOUND
                    )
                else:
                    data = {}
                    data["Amount_staked"] = merchant_bal.stakedTokenAmount
                    data["value_in_stablecoin"] = merchant_bal.licenseTokenAmount
                    data["exchange_rate"] = merchant_bal.stakedTokenExchangeRate
                    data["total_fiat_held_in_bank_acct"] = round(
                        float(merchant_bal.licenseTokenAmount)
                        - float(merchant_bal.allowedTokenAmount),
                        7,
                    )
                    data[
                        "msg"
                    ] = "the total_fiat_held_in_bank_acct is not final, pending transaction are also added to the amount"

                    return Response(data, status=status.HTTP_200_OK)


class EventListener(APIView):
    def post(self, request):
        serializeEvent = EventSerializer(data=request.data)
        if serializeEvent.is_valid():
            check_memo = is_transaction_memo_valid(request.data.get("memo"))
            if check_memo == True:
                event_type = serializeEvent.validated_data.get("event_type")
                if event_type == "merchant_staking":
                    isTransaction_Valid.delay(
                        transaction_hash=request.data.get("hash"),
                        memo=request.data.get("memo"),
                        _address=config("STAKING_ADDRESS"),
                        _asset_code=STAKING_TOKEN,
                        _asset_issuer=STAKING_TOKEN_ISSUER,
                        event_transaction_type="merchant_staking",
                    )
                    return Response(
                        serializeEvent.validated_data, status=status.HTTP_200_OK
                    )

                elif event_type == "user_withdrawals":
                    isTransaction_Valid.delay(
                        request.data.get("hash"),
                        request.data.get("memo"),
                        _address=STABLECOIN_ISSUER,
                        _asset_code=STABLECOIN_CODE,
                        _asset_issuer=STABLECOIN_ISSUER,
                        event_transaction_type="user_withdrawals",
                    )
                    return Response(
                        serializeEvent.validated_data, status=status.HTTP_200_OK
                    )

                else:
                    pass
            else:
                return Response(
                    {"error": "Invalid memo"}, status=status.HTTP_400_BAD_REQUEST
                )

        return Response(serializeEvent.errors, status.HTTP_400_BAD_REQUEST)


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
            elif len(tx_signature) > 1:
                tx_submit = server_.submit_transaction(
                    transactionEnvelop, skip_memo_required_check=True
                )
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

            merchants_list = TokenTableSerializer(all_merchant_token_bal(), many=True)
            amount = sep6Data.validated_data["amount"]
            account = sep6Data.validated_data["account"]
            transaction_narration = uidGenerator(
                15
            )  # This should be changed to random wordlist

            MA_selected = merchants_to_process_transaction(
                merchants_list.data, amount, bank=None
            )
            if MA_selected:
                try:
                    update_pending_transaction_model(
                        MA_selected["merchant"]["UID"],
                        transaction_amt=str(
                            float(amount) + float(GENERAL_TRANSACTION_FEE)
                        ),
                        transaction_type="deposit",
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
    return Response(SEP_INFO)


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
