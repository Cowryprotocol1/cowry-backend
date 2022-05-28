
from typing import TypeVar, Union

from utils.utils import Id_generator, uidGenerator
from .models import MerchantsTable, TokenTable, TransactionsTable, TxHashTable,XdrGeneratedTransaction
# from rest_framework. import ObjectDoesNotExist
QuerySet = TypeVar('QuerySet')
# Get user by UID from the db and returns true if UID exists
def is_transaction_memo_valid(memo):
    ma_memo = MerchantsTable.objects.filter(UID=memo)
    if ma_memo:
        return True
    return False


# check if transaction hash has been processed before
def check_transaction_hash_if_processed(transaction_hash: str) -> bool:
    hash_check = TxHashTable.objects.filter(txHash=transaction_hash)
    # check if the hash has been processed before
    """
    true - transaction has been processed and store on the db
    false - transaction is not found on the db
    """
    if hash_check:
        return True
    else:
        return False
# This add a transaction hash to db and also update the hash_processed field to True
def add_and_update_transaction_hash(_hash:str, merchant_id:str) -> bool:
    merchant = TxHashTable.objects.get(merchant_id=merchant_id)
    merchant.txHash = _hash
    merchant.is_processed = True
    merchant.save()

def get_merchant_by_pubKey(merchant_pubKey:str) -> MerchantsTable:
    merchant = MerchantsTable.objects.get(blockchainAddress=merchant_pubKey)
    return merchant


# print(get_merchant_by_pubKey(
#     "GCIKDUYN2OW7GF25XOGTHPRKPTACEF5CQJR3QNFANWKCJWGFB2S6FA6J"))

def update_merchant_by_allowedLicenseAmount(merchant_id:str, allowedLicenseAmt:int, stakedAmt:int, exchangeRate:int) -> bool:
    # update allowed and license token balance on minting
    try:

        merchant_bal = TokenTable.objects.get(merchant_id=merchant_id)
        merchant_bal.allowedTokenAmount += float(allowedLicenseAmt)
        merchant_bal.licenseTokenAmount += float(allowedLicenseAmt)
        merchant_bal.stakedTokenAmount += float(stakedAmt)
        merchant_bal.stakedTokenExchangeRate = exchangeRate
        
        merchant_bal.save() 
        return True
    except Exception as e:
        print(e.args)
        # notify admin
        return e.args




def all_merchant_token_bal() -> list:
    merchants = TokenTable.objects.all().prefetch_related('merchant')
    return merchants
def get_all_merchant_object() -> list:
    merchants = MerchantsTable.objects.all()
    return merchants
def assign_transaction_to_merchant(transaction:object, merchant:str):
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    tx_add = transaction.merchant.add(merchant_obj)
    return tx_add

def get_transaction_By_Id(transaction_id:str) -> object:
    transaction = TransactionsTable.objects.get(id=transaction_id)
    return transaction


def get_list_of_all_register_merhants() -> list:
    pass

def merchant_transaction_status(merchant_id:str, status:str) -> str:
    merchant = MerchantsTable.objects.filter(UID=merchant_id)
    merchant.transaction_processing_status = status
    merchant.save()


def return_all_objects_for_a_merchants(merchant: str) -> QuerySet:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    merchant = TransactionsTable.objects.filter(merchant=merchant_obj)
    return merchant


def update_pending_transaction_model(merchant: str, transaction_amt: str, transaction_type: str, narration:str, transaction_hash=None, transaction_memo=None, user_block_address=None, phone_num=None, email=None, user_bank_account=None, bank_name=None):
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    if transaction_type == "deposit":
        a1 = TransactionsTable(users_address=user_block_address, transaction_hash=transaction_hash, transaction_type=transaction_type, transaction_amount=transaction_amt, transaction_narration=narration)
        a1.save()
        a1.merchant.add(merchant_obj)
        return a1

    elif transaction_type == "withdraw":
        a1 = TransactionsTable(users_address=user_block_address, transaction_type=transaction_type, transaction_amount=transaction_amt, transaction_hash=transaction_hash, transaction_memo=transaction_memo, user_phone=phone_num, user_email=email, user_bank_account=user_bank_account, user_bank_name=bank_name, transaction_narration=narration)
        
        a1.save()
        a1.merchant.add(merchant_obj)
        return a1
    else:
        raise Exception("Unknown Transaction type")


def update_PendingTransaction_Model(transaction_amt: str, transaction_type: str, narration: str, transaction_hash=None, transaction_memo=None, user_block_address=None, phone_num=None, email=None, user_bank_account=None, bank_name=None):
    """
    This add transaction and it details to the db, it does not assign it to a merchant
    """
   
    a1 = TransactionsTable(users_address=user_block_address, transaction_type=transaction_type, 
                            transaction_amount=transaction_amt, transaction_hash=transaction_hash,
                            transaction_memo=transaction_memo, user_phone=phone_num, user_email=email, 
                            user_bank_account=user_bank_account, user_bank_name=bank_name, 
                            transaction_narration=narration)

    a1.save()
    return a1
def update_xdr_table(transaction_type:str, tx_xdr:str, tx_status:str, merchant:str, transaction_Id:Union[str, None]) -> str:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    if transaction_type == "deposit":
        xdr = XdrGeneratedTransaction(
            status=tx_status, xdr_object=tx_xdr, transaction_id_from_tx_table=transaction_Id)
        xdr.save()
        xdr.merchant.add(merchant_obj)
    elif transaction_type == "withdraw":
        xdr = XdrGeneratedTransaction(
            status=tx_status, xdr_object=tx_xdr, transaction_id_from_tx_table=transaction_Id)
        xdr.save()
        xdr.merchant.add(merchant_obj)
    else:
        raise Exception("Unknown Transaction type")

def check_xdr_if_already_exist(xdr:str) -> bool:
    xdr_check = XdrGeneratedTransaction.objects.filter(xdr_object=xdr)
    if xdr_check:
        return True
    else:
        return False
def remove_transaction_from_merchants_model(merchant:str, transaction_id:str):
    try:
        merchant_obj = MerchantsTable.objects.get(UID=merchant)
        transaction_obj = TransactionsTable.objects.get(id=transaction_id)
        transaction_obj.merchant.remove(merchant_obj)
    except :
        #notify admin
        raise Exception("Transaction not found")
    # transaction_obj.delete() # delete the transaction from the db

    return "ok"
def update_xdr_transaction(merchant:object):
    merchant.TransactionTable.remove(merchant)

def update_cleared_uncleared_bal(merchant: object, status: str, amount: float):
    merchant_obj = TokenTable.objects.get(merchant=merchant)
    if status == "cleared":
        merchant_obj.unclear_bal -= amount
        merchant_obj.allowedTokenAmount += amount
        merchant_obj.save()

    elif status == "uncleared":
        merchant_obj.allowedTokenAmount -= amount
        merchant_obj.unclear_bal += amount
        merchant_obj.save()

def delete_merchant(merchant: str) -> bool:
    merchant_obj = MerchantsTable.objects.get(UID=merchant)
    merchant_obj.delete()
    return True

# merchants = MerchantsTable.objects.get(UID="8f9ee6190c5bb9ccb2f3")
# print(merchants)
# # adc = update_cleared_uncleared_bal(mercahnts, "cleared", 1000)
# adc = update_PendingTransaction_Model(transaction_amt=102, transaction_type="deposit", narration="testing002")
# print(adc)
# dcf = return_all_objects_for_a_merchants("af14143d764d9cfbe16e")
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
# print(hash_.is_processed)
# adc = remove_transaction_from_merchants_model("2377ae6f13a983b27047", 2)
# print(adc)


