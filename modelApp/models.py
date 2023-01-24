from django.db import models
from utils.utils import uidGenerator
from Blockchains.Stellar.operations import is_account_valid
from rest_framework import serializers
from utils.utils import Id_generator
from django.utils import timezone

# Create your models here.


def validate_blockchainAddress(value):
    if not is_account_valid(value):
        raise serializers.ValidationError(
            "Invalid Blockchain Address or Account not Created"
        )
    return value


def acct_num_min(value):
    if len((value)) < 10:
        raise serializers.ValidationError("Account Number should be atleast 10 digits")
    return value


class MerchantsTable(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    UID = models.CharField(
        max_length=128,
        unique=True,
        primary_key=True,
        auto_created=True,
        default=uidGenerator(),
    )

    email = models.EmailField(max_length=254, unique=True)
    bankName = models.CharField(max_length=128)
    bankAccount = models.CharField(
        max_length=15, unique=True, validators=[acct_num_min]
    )
    phoneNumber = models.CharField(max_length=128, unique=True)
    blockchainAddress = models.CharField(
        max_length=128, unique=True, validators=[validate_blockchainAddress]
    )
    transaction_processing_status = models.CharField(
        max_length=20, blank=True, default="Available"
    )


# Some fields should be read only to avoid users from modifying them.


class TokenTable(models.Model):
    merchant = models.OneToOneField(
        MerchantsTable, on_delete=models.CASCADE, primary_key=True
    )
    stakedTokenAmount = models.FloatField(default=0, blank=True)
    allowedTokenAmount = models.FloatField(default=0, blank=True)
    licenseTokenAmount = models.FloatField(default=0, blank=True)
    stakedTokenExchangeRate = models.FloatField(default=0, blank=True)
    unclear_bal = models.FloatField(default=0, blank=True)
    stakingTx_hash = models.CharField(max_length=128, blank=True, default=0)


class TxHashTable(models.Model):
    merchant = models.ForeignKey(MerchantsTable, on_delete=models.CASCADE)
    txHash = models.CharField(max_length=128, blank=True, default=0)
    is_processed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class TransactionsTable(models.Model):
    # This would hold details about a merchant and the amount of transaction to merchant has in pending
    # details should include the recipient address, the merchants object, amount pending
    merchant = models.ManyToManyField(MerchantsTable)
    id = models.CharField(max_length=128, primary_key=True, default=Id_generator())
    users_address = models.CharField(max_length=128, blank=True, null=True)
    user_phone = models.CharField(max_length=128, blank=True, null=True)
    user_email = models.CharField(max_length=128, blank=True, null=True)
    transaction_memo = models.CharField(max_length=128, blank=True, null=True)
    transaction_hash = models.CharField(max_length=128, blank=True, null=True)
    transaction_type = models.CharField(max_length=128, blank=True, null=True)
    user_bank_account = models.CharField(max_length=128, blank=True, null=True)
    user_bank_name = models.CharField(max_length=128, blank=True, null=True)
    transaction_status = models.CharField(
        max_length=20, blank=True, default="pending"
    )

    transaction_amount = models.FloatField(default=0, blank=True, null=True)
    transaction_narration = models.CharField(
        max_length=128, default=uidGenerator(), null=False, unique=True
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True)

class XdrGeneratedTransaction(models.Model):
    merchant = models.ManyToManyField(MerchantsTable)
    status = models.CharField(
        max_length=128, default="submitted", blank=True, null=True
    )
    xdr_object = models.CharField(max_length=2000, default="", blank=True, null=True)
    transaction_id_from_tx_table = models.CharField(
        max_length=128, default=0, blank=True, null=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class PeriodicTaskRun(models.Model):
    task_id = models.CharField(max_length=200)
    task_name = models.CharField(max_length=200, verbose_name="Task Name")
    created_at = models.DateTimeField(auto_now_add=True)
