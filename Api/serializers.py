# from Api.utils import amount_to_naira
from modelApp.models import MerchantsTable, TokenTable, TxHashTable, TransactionsTable, XdrGeneratedTransaction

from rest_framework import serializers
from Blockchains.Stellar.utils import check_stellar_address, check__asset_code_For_stable
from django.core.exceptions import ValidationError

# print(check_stellar_address("FGHJKJHGFDDFGHJ"))
# def validate_blockchainAddress(value):
#         if not is_account_valid(value):
#             raise serializers.ValidationError("Invalid Blockchain Address or Account not Created")
#         return value
def transaction_source_types(value):
        transaction_source_choice = ['sep']
        if value not in transaction_source_choice:
            raise serializers.ValidationError("invalid 'transaction_source', this can either be sep or protocol")
        return value

def check_account_numberLen(value):
    if len(value) == 10:
        return value
    else:
        raise ValidationError("Invalid bank account number, len should be equal 10")

class MerchantsTableSerializer(serializers.ModelSerializer):
    # blockchainAddress = serializers.CharField(
    #     max_length=128, validators=[validate_blockchainAddress])

    class Meta:
        model = MerchantsTable
        fields = ['email', 'bankName', 'bankAccount', 'phoneNumber',
                'blockchainAddress', 'UID', 'transaction_processing_status']
        # Custom validation for address field



   
class TokenTableSerializer(serializers.ModelSerializer):
    merchant = MerchantsTableSerializer(read_only=True)
    class Meta:
        model = TokenTable
        fields = '__all__'


class TxHashTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = TxHashTable
        fields = '__all__'

class EventSerializer(serializers.Serializer):
    hash = serializers.CharField(max_length=150)
    memo = serializers.CharField(max_length=50)
    event_type = serializers.CharField(max_length=50)


    


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TransactionsTable
        fields = '__all__'


class XdrGeneratedTransactionSerializer(serializers.ModelSerializer):
    merchant = MerchantsTableSerializer(read_only=True, many=True)
    class Meta:
        model = XdrGeneratedTransaction
        fields = '__all__'

class OffBoard_A_MerchantSerializer(serializers.Serializer):
    merchant_Id = serializers.CharField(max_length=128)
    merchant_PubKey = serializers.CharField(min_length=56, max_length=56)


class Fiat_Off_RampSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=1000, required=True)
    bank_name = serializers.CharField(max_length=128)
    account_number = serializers.CharField(max_length=10)
    name_on_acct = serializers.CharField(max_length=128, allow_null=True, required=False)
    phone_number = serializers.CharField(max_length=128)
    blockchain_address = serializers.CharField(validators=[check_stellar_address])
    transaction_narration = serializers.CharField(max_length=128)
    data_created = serializers.DateTimeField(read_only=True)
    data_updated = serializers.DateTimeField(read_only=True)
    transaction_Id = serializers.CharField(max_length=20, min_length=10, allow_null=False, required=False)
    transaction_source = serializers.CharField(max_length=10, allow_null=True, required=False, validators=[transaction_source_types], error_messages={"required":"transaction_source is a required field"})



class Fiat_On_RampSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=1000.0)
    bankType = serializers.CharField(max_length=128)
    blockchainAddress = serializers.CharField(
        validators=[check_stellar_address])
    narration = serializers.CharField(max_length=128)
    transaction_source = serializers.CharField(max_length=10, allow_null=True, required=False, validators=[transaction_source_types], error_messages={"required":"transaction_source is a required field"})
    transaction_Id = serializers.CharField(max_length=20, min_length=10, allow_null=False, required=False)
        



class Sep6DepositSerializer(serializers.Serializer):
    asset_code = serializers.CharField(
        max_length=20, min_length=3, required=True, allow_null=False, validators=[check__asset_code_For_stable])
    
    asset_issuer = serializers.CharField(
        max_length=56, min_length=56, required=False, validators=[check_stellar_address])
    account = serializers.CharField(
        min_length=56, max_length=56, required=False, allow_null=False)
    amount = serializers.FloatField(allow_null=True, required=False, error_messages={"min_value":"minimum amount for withdrawal is 1000", "required":"this is a required field"}, min_value=1000.0)
    memo_type = serializers.CharField(allow_blank=True,
        max_length=56, min_length=2, required=False)
    memo = serializers.CharField(allow_blank=True, required=False,
        max_length=56, min_length=2)
    email = serializers.EmailField(allow_blank=True, required=False)
    wallet_name = serializers.CharField(allow_null=True, required=False, min_length=1, max_length=100)
    wallet_url = serializers.CharField(allow_null=True, required=False, min_length=1, max_length=100)
    lang = serializers.CharField(allow_null=True, required=False, min_length=1, max_length=100)
    claimable_balance_supported = serializers.BooleanField(required=False)
    

class Sep6WithdrawalSerializer(serializers.Serializer):
    asset_code = serializers.CharField(
        max_length=20, min_length=3, required=True, validators=[check__asset_code_For_stable])
    account=serializers.CharField(required = True, validators=[check_stellar_address])
    amount = serializers.FloatField(allow_null=True, required=False, min_value=1000.0)
    dest = serializers.CharField(required=True, validators=[check_account_numberLen])
    dest_extra = serializers.CharField(min_length=2, max_length=20, required=True)


class XdrSerializer(serializers.Serializer):
    signed_xdr = serializers.CharField(required=True)