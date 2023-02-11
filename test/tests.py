# import unittest
# from unittest.mock import patch
# import random
# from modelApp.models import TokenTable, TransactionsTable
# from Api.serializers import TokenTableSerializer, TransactionSerializer

# class TestMerchantsToProcessTransaction(unittest.TestCase):
#     @patch('modelApp.models.TokenTable.objects.exclude')
#     def test_all_merchant_token_bal(self, mock_exclude):
#         # setup mock return value for `TokenTable.objects.exclude`
#         mock_exclude.return_value = 'merchants'

#         result = all_merchant_token_bal('last_merchant', 'blockchainaddress')
#         self.assertEqual(result, 'merchants')
#         mock_exclude.assert_called_with(merchant='last_merchant', merchant__blockchainAddress='blockchainaddress')

#     @patch('myapp.models.TransactionsTable.objects.all')
#     @patch('random.choice')
#     def test_merchants_to_process_transaction(self, mock_choice, mock_all):
#         # setup mock return value for `TransactionsTable.objects.all`
#         mock_all.return_value = [{'created_at': '2022-01-01', 'merchant': ('merchant_name',)}]
#         # setup mock return value for `random.choice`
#         mock_choice.return_value = 'adc'

#         # deposit transaction type
#         result = merchants_to_process_transaction('recipient_block', 100, bank=None, transaction_type='deposit')
#         self.assertEqual(result, 'adc')
#         mock_all.assert_called_with().order_by('created_at')
#         mock_choice.assert_called_with(['merchant'])

#         # user_withdrawals transaction type
#         result = merchants_to_process_transaction('recipient_block', 100, bank=None, transaction_type='user_withdrawals')
#         self.assertEqual(result, 'adc')
#         mock_all.assert_called_with().order_by('created_at')
#         mock_choice.assert_called_with(['merchant'])

#     @patch('myapp.models.TransactionsTable.objects.all')
#     def test_merchants_to_process_transaction_no_merchants(self, mock_all):
#         # setup mock return value for `TransactionsTable.objects.all`
#         mock_all.return_value = [{'created_at': '2022-01-01', 'merchant': ('merchant_name',)}]

#         result = merchants_to_process_transaction('recipient_block', 100, bank=None, transaction_type='deposit')
#         self.assertEqual(result, False)
#         mock_all.assert_called_with().order_by('created_at')
