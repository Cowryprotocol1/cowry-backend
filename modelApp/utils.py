from typing import TypeVar, Union
from utils.utils import Id_generator, uidGenerator
from .models import (
    MerchantsTable,
    TokenTable,
    TransactionsTable,
    TxHashTable,
    XdrGeneratedTransaction,
)
from decouple import config
from django.db.models import Sum, F



QuerySet = TypeVar("QuerySet")
GENERAL_TRANSACTION_FEE = config("GENERAL_TRANSACTION_FEE")


# Get user by UID from the db and returns true if UID exists
def is_transaction_memo_valid(memo):
    ma_memo = MerchantsTable.objects.filter(UID=memo)
    if ma_memo:
        return True
    return False


# check if transaction hash has been processed before
def check_transaction_hash_if_processed(transaction_hash: str) -> bool:
    """
    true - transaction has been processed and store on the db
    false - transaction is not found on the db
    """
    # try:
    hash_check = TxHashTable.objects.filter(txHash=transaction_hash)
    if hash_check:
        return True
    else:
        return False


# This add a transaction hash to db and also update the hash_processed field to True
def add_and_update_transaction_hash(_hash: str, merchant_id: str) -> bool:
    # try:
    try:
        merchant = TxHashTable.objects.get(txHash=_hash)
    except TxHashTable.DoesNotExist:
        TxHashTable.objects.create(
            merchant_id=merchant_id, txHash=_hash, is_processed=True
        )
        return True
    else:
        if merchant:
            if merchant.is_processed == False:
                merchant.txHash = _hash
                merchant.is_processed = True
                merchant.save()
                return True
            elif merchant.is_processed == True:
                # print("merchant Tx already processed")
                # print(merchan)
                # merchant found but hash already processed
                return False
            else:
                return False


def get_merchant_by_pubKey(merchant_pubKey: str) -> MerchantsTable:
    merchant = MerchantsTable.objects.get(blockchainAddress=merchant_pubKey)
    return merchant


# print(get_merchant_by_pubKey(
#     "GCIKDUYN2OW7GF25XOGTHPRKPTACEF5CQJR3QNFANWKCJWGFB2S6FA6J"))


def update_merchant_by_allowedLicenseAmount(
    merchant_id: str, allowedLicenseAmt: int, stakedAmt: int, exchangeRate: int, stakingHash:str
) -> bool:
    # update allowed and license token balance on minting
    try:

        merchant_bal = TokenTable.objects.get(merchant_id=merchant_id)
        merchant_bal.allowedTokenAmount += float(allowedLicenseAmt)
        merchant_bal.licenseTokenAmount += float(allowedLicenseAmt)
        merchant_bal.stakedTokenAmount += float(stakedAmt)
        merchant_bal.stakedTokenExchangeRate = exchangeRate
        merchant_bal.stakingTx_hash = stakingHash

        merchant_bal.save()
        return True
    except Exception as e:
        print("nah inside update merchant allowed")
        print(e.args)
        # notify admin
        return False


def all_merchant_token_bal() -> list:
    merchants = TokenTable.objects.all().prefetch_related("merchant")
    return merchants


def get_all_merchant_object() -> list:
    merchants = MerchantsTable.objects.all()
    return merchants


def assign_transaction_to_merchant(transaction: object, merchant: str, amount: str):
    """Assign a withdrawal transaction to a merchant to process withdrawals, this is also used to update the uncleared_bal"""
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    tx_add = transaction.merchant.add(merchant_obj)
    merchant_token_obj = TokenTable.objects.get(merchant=merchant)
    merchant_token_obj.allowedTokenAmount -= amount
    merchant_token_obj.unclear_bal += amount

    merchant_token_obj.save()
    return tx_add


def get_transaction_By_Id(transaction_id: str) -> object:
    transaction = TransactionsTable.objects.get(id=transaction_id)
    return transaction


def merchant_transaction_status(merchant_id: str, status: str) -> str:
    merchant = MerchantsTable.objects.filter(UID=merchant_id)
    merchant.transaction_processing_status = status
    merchant.save()


def get_pending_transactions(merchant: str) -> QuerySet:
    """This is used to return just the list of pending transaction for a specific IFP"""
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    merchant_tx = TransactionsTable.objects.filter(merchant=merchant_obj)
    if merchant_tx:
        merchant = merchant_tx.filter(transaction_status="pending")
        return merchant

def get_all_transaction_for_merchant(merchant:object) -> QuerySet:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    transaction_list = TransactionsTable.objects.filter(merchant=merchant_obj).order_by("-created_at") #using the - before the colum name means descending order
    return transaction_list

def get_transaction_by_pubKey(pubKey: str) -> QuerySet:
    """
    Used to get transaction by public key
    """
    transaction_ = TransactionsTable.objects.filter(users_address=pubKey).order_by('-created_at')
    return transaction_




def update_pending_transaction_model(
    merchant: str,
    transaction_amt: str,
    transaction_type: str,
    narration: str,
    transaction_status:str,
    transaction_hash=None,
    transaction_memo=None,
    user_block_address=None,
    phone_num=None,
    email=None,
    user_bank_account=None,
    bank_name=None,
):
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    if transaction_type == "deposit":
        a1 = TransactionsTable(
            id=Id_generator(),
            users_address=user_block_address,
            transaction_hash=transaction_hash,
            transaction_type=transaction_type,
            transaction_amount=transaction_amt,
            transaction_narration=narration,
            transaction_status = "pending"
        )
        a1.save()
        a1.merchant.add(merchant_obj)
        return a1

    elif transaction_type == "withdraw":
        a1 = TransactionsTable(
            users_address=user_block_address,
            transaction_type=transaction_type,
            transaction_amount=transaction_amt,
            transaction_hash=transaction_hash,
            transaction_memo=transaction_memo,
            user_phone=phone_num,
            user_email=email,
            user_bank_account=user_bank_account,
            user_bank_name=bank_name,
            transaction_narration=narration,
        )

        a1.save()
        a1.merchant.add(merchant_obj)
        return a1
    else:
        raise Exception("Unknown Transaction type")


def update_PendingTransaction_Model(
    transaction_amt: str,
    transaction_type: str,
    narration: str,
    transaction_hash=None,
    transaction_memo=None,
    user_block_address=None,
    phone_num=None,
    email=None,
    user_bank_account=None,
    bank_name=None,
):
    """
    This add transaction and it details to the db, it does not assign it to a merchant
    """

    a1 = TransactionsTable(
        id=Id_generator(),
        users_address=user_block_address,
        transaction_type=transaction_type,
        transaction_amount=transaction_amt,
        transaction_hash=transaction_hash,
        transaction_memo=transaction_memo,
        user_phone=phone_num,
        user_email=email,
        user_bank_account=user_bank_account,
        user_bank_name=bank_name,
        transaction_narration=narration,
    )

    a1.save()
    return a1


def update_xdr_table(
    transaction_type: str,
    tx_xdr: str,
    tx_status: str,
    merchant: str,
    transaction_Id: Union[str, None],
) -> str:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    if transaction_type == "deposit":
        xdr = XdrGeneratedTransaction(
            status=tx_status,
            xdr_object=tx_xdr,
            transaction_id_from_tx_table=transaction_Id,
        )
        xdr.save()
        xdr.merchant.add(merchant_obj)
    elif transaction_type == "withdraw":
        xdr = XdrGeneratedTransaction(
            status=tx_status,
            xdr_object=tx_xdr,
            transaction_id_from_tx_table=transaction_Id,
        )
        xdr.save()
        xdr.merchant.add(merchant_obj)
    else:
        raise Exception("Unknown Transaction type")


def check_xdr_if_already_exist(xdr: str) -> bool:
    xdr_check = XdrGeneratedTransaction.objects.filter(xdr_object=xdr)
    if xdr_check:
        return True
    else:
        return False

def update_transaction_status(transaction_id:str, status:str) -> bool:
    try:
        transaction = TransactionsTable.objects.get(id=transaction_id)
        transaction.transaction_status = status
        transaction.save()
    except Exception as unknownError:
        #notify admin
        print(unknownError)
        return False
    else:
        return True

    pass

def remove_transaction_from_merchants_model(
    merchant: str, transaction_id: str, amount: float
):
    """used to remove an assigned transaction from the IFP account and also update the IFP uncleared balance"""
    try:
        merchant_obj = MerchantsTable.objects.get(UID=merchant)
        transaction_obj = TransactionsTable.objects.get(id=transaction_id)
        transaction_obj.merchant.remove(merchant_obj)
        merchant_token_obj = TokenTable.objects.get(merchant=merchant)
        merchant_token_obj.unclear_bal -= amount
        merchant_token_obj.save()
    except Exception as error:
        print(error)
        # notify admin
        raise Exception("Transaction not found")
    # transaction_obj.delete() # delete the transaction from the db

    return "ok"


def update_xdr_transaction(merchant: object):
    merchant.TransactionTable.remove(merchant)


def update_cleared_uncleared_bal(merchant: object, status: str, amount: float):
    print(
        "Needs to update merchant balances in cases where the user expected to send payment has not send payment after a specific time"
    )
    merchant_obj = TokenTable.objects.get(merchant=merchant)
    if status == "cleared":
        merchant_obj.unclear_bal -= amount
        merchant_obj.allowedTokenAmount += float(amount) - float(
            GENERAL_TRANSACTION_FEE
        )
        merchant_obj.save()

    elif status == "uncleared":
        merchant_obj.allowedTokenAmount -= amount
        merchant_obj.unclear_bal += amount
        merchant_obj.save()

    elif status == "deposit_cleared":
        # IFPs has received user deposit in their bank account
        # their uncleared balance can truly be reduced now
        merchant_obj.unclear_bal -= amount
        merchant_obj.save()



def delete_merchant(merchant: str) -> bool:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    merchant_obj.delete()
    return True




def protocolAudit():
    all_merchants = TokenTable.objects.all()
    _edited = all_merchants.values(ifp_blockchain_addr=F("merchant_id__blockchainAddress")).annotate(
        staked_token_hash = F('stakingTx_hash'),
        total_staked_usdc = F('stakedTokenAmount'),
        exchange_rate = F('stakedTokenExchangeRate'),
        total_mint_right = F('licenseTokenAmount'),
        pending_unclear_amt = F('unclear_bal'),
        fiat_in_acct = F('total_mint_right') - (F('allowedTokenAmount') + F('unclear_bal')),
        allowed_token_left =  F("total_mint_right") - F('pending_unclear_amt') + F('fiat_in_acct'),
    )

    return _edited






# adc = protocolAudit()


# print(adc)

# merchants = MerchantsTable.objects.get(UID="8f9ee6190c5bb9ccb2f3")
# print(merchants)
# # adc = update_cleared_uncleared_bal(mercahnts, "cleared", 1000)
# adc = update_PendingTransaction_Model(transaction_amt=102, transaction_type="deposit", narration="testing002")
# print(adc)
# dcf = get_pending_transactions("d2f7df8d2dd036aca1cf")
# print(dcf)


# print(adc.amount)
# merchant = MerchantsTable.objects.get(merchant_id=merchant_id)
# merchant.merchant_name = data.get("merchant_name")
# merchant.merchant_address = data.get("merchant_address")
# merchant.save()
# return True

# hash_ = check_transaction_hash_if_processed(
#     "1bb201a3cf0e43ace1676d807aab8d01f4918399d9286f5be18c4823f83de4cc")
# print(hash_)
# print(hash_)
# adc = remove_transaction_from_merchants_model("2377ae6f13a983b27047", 2)
# print(adc)


# add_hash = add_and_update_transaction_hash(
#     "1bb201a3cf0e43ace1676d807aab8d01f4918399d9286f5be18c4823f83de4cc", "99e28b45764cbf5d0f5a")
# print(add_hash)
# print(type(add_hash))
# adc = get_merchant_by_pubKey(
#     "GCO7CVQOZ73FJS2EWG5G7INJJM2X2CZMRM572WL22AX2VUCFKTYJXK3V")
# print(adc)


# adc = update_transaction_status(transaction_id="20031483445", status="completed")
# print(adc)