from Api.utils import amount_to_naira
from modelApp.models import MerchantsTable, TokenTable, TxHashTable, TransactionsTable, XdrGeneratedTransaction
from modelApp.utils import all_merchant_token_bal
from rest_framework import serializers
from Blockchains.Stellar.utils import check_stellar_address

# print(check_stellar_address("FGHJKJHGFDDFGHJ"))
# def validate_blockchainAddress(value):
#         if not is_account_valid(value):
#             raise serializers.ValidationError("Invalid Blockchain Address or Account not Created")
#         return value

class MerchantsTableSerializer(serializers.ModelSerializer):
    # blockchainAddress = serializers.CharField(
    #     max_length=128, validators=[validate_blockchainAddress])

    class Meta:
        model = MerchantsTable
        fields = ['email', 'bankName', 'bankAccount', 'phoneNumber',
                'blockchainAddress', 'UID', 'transaction_processing_status']
        # Custome validation for address field



   
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
    amount = serializers.FloatField()
    bank_name = serializers.CharField(max_length=128)
    account_number = serializers.CharField(max_length=10)
    name_on_acct = serializers.CharField(max_length=128, allow_null=True)
    phone_number = serializers.CharField(max_length=128)
    blockchain_address = serializers.CharField(validators=[check_stellar_address])
    transaction_narration = serializers.CharField(max_length=128)
    data_created = serializers.DateTimeField(read_only=True)
    data_updated = serializers.DateTimeField(read_only=True)

class Fiat_On_RampSerializer(serializers.Serializer):
    amount = serializers.FloatField(min_value=1000.0)
    bankType = serializers.CharField(max_length=128)
    blockchainAddress = serializers.CharField(
        validators=[check_stellar_address])
    narration = serializers.CharField(max_length=128)
