# from unittest import mock
# from django.urls import reverse
# from test_setup import TestSetUpClass
# from modelApp.models import TransactionsTable, MerchantsTable
# from Api.utils import uidGenerator
# from utils.utils import Id_generator

# class MerchantDepositConfirmationTest(TestSetUpClass):
#     def setUp(self):
#         self.user_key = '12345'
#         self.query_type = 'ifp'
#         self.url = reverse('merchants')
#         # merchants_list = MerchantsTable.objects.bulk_create([
#         #     MerchantsTable()
#         # ])
#         transaction_list = TransactionsTable.objects.bulk_create([
#             TransactionsTable(
#             id=Id_generator(),
#             users_address="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO1CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_hash="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO1CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_type="deposit",
#             transaction_amount="5000",
#             transaction_narration="testing 001",
#             transaction_status="pending",
#             ),
#             TransactionsTable(
#             id=Id_generator(),
#             users_address="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO2CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_hash="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO2CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_type="deposit",
#             transaction_amount="5000",
#             transaction_narration="testing 002",
#             transaction_status="pending",
#             ),
#             TransactionsTable(
#             id=Id_generator(),
#             users_address="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO3CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_hash="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO3CEM4CPYGAMTUNBQ4ZZA6KI",
#             transaction_type="deposit",
#             transaction_amount="5000",
#             transaction_narration="testing 003",
#             transaction_status="pending",
#             ),
#         ])
#         for transaction in transaction_list:
#             transaction.merchant.add(uidGenerator())
        
#         # a1.merchant.add(merchant_obj)
#         # return a1
#         # transactions_list = [
#         # a1 =TransactionsTable(id=uidGenerator(), transaction_amount=100.50, transaction_type='credit', user_email='user1@example.com'),
#         # b1 =TransactionsTable(id=uidGenerator(12), transaction_amount=50.25, transaction_type='debit', user_email='user2@example.com'),
#         # c1 = TransactionsTable(id=uidGenerator(13), transaction_amount=200.75, transaction_type='transfer', user_email='user3@example.com')
#         #     # ]
        
#         # t1 = TransactionsTable.objects.create(a1)
#         # t2 = TransactionsTable.objects.create(b1)
#         # t3 = TransactionsTable.objects.create(c1)
#         # print(TransactionsTable.objects.)
#         tx_new = TransactionsTable.objects.get(users_address="GDLSMOYAN5ITM2LBNB5226D7NOTVALIDOO1CEM4CPYGAMTUNBQ4ZZA6KI")
#         print(tx_new)
#         print(tx_new.users_address)
#         print(tx_new.transaction_hash)
#         print(tx_new.id)
#         print(tx_new.merchant)
#         # ----------------------------
#         print(MerchantsTable.objects.all())
#         # MerchantsTable.objects.add(t1)
            

#         # print(transactions_list)
#         # MerchantsTable.set(transactions_list)


#         # self.default_mock_data = transactions_list




#     @mock.patch('Api.views.get_all_transaction_for_merchant')
#     def test_get_all_transaction_for_merchant(self, mock_get_all_transaction_for_merchant):
#         mock_get_all_transaction_for_merchant.return_value = self.default_mock_data

#         response = self.client.get(self.url, {'public_key': self.user_key, 'query_type': self.query_type})
#         print(response.json())
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data['status'], 'success')
#         self.assertEqual(response.data['all_transactions'], self.default_mock_data["all_transactions"])
#         mock_get_all_transaction_for_merchant.assert_called_with(self.user_key)

#     @mock.patch('path.to.get_transaction_by_pubKey')
#     def test_get_transaction_by_pubKey(self, mock_get_transaction_by_pubKey):
#         mock_get_transaction_by_pubKey.return_value = []

#         response = self.client.get(self.url, {'public_key': self.user_key, 'query_type': 'user'})

#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data['status'], 'success')
#         self.assertEqual(response.data['all_transactions'], [])
#         mock_get_transaction_by_pubKey.assert_called_with(self.user_key)
        
#     def test_no_public_key(self):
#         response = self.client.get(self.url)

#         self.assertEqual(response.status_code, 400)
#         self.assertEqual(response.data['error'], 'Please provide a public key and query_type')
        
#     def test_not_merchant(self):
#         with mock.patch('path.to.get_all_transaction_for_merchant') as mock_get_all_transaction_for_merchant:
#             mock_get_all_transaction_for_merchant.side_effect = MerchantsTable.DoesNotExist
#             response = self.client.get(self.url, {'public_key': self.user_key, 'query_type': self.query_type})

#             self.assertEqual(response.status_code, 404)
#             self.assertEqual(response.data['error'], 'address not a merchant yet')
#             self.assertEqual(response.data['status'], 'fail')
            
#     @mock.patch('path.to.get_all_transaction_for_merchant')
#     def test_get_transactions_for_merchant(self, mock_get_all_transactions):
#     # set up mock data to be returned by the function
#         mock_get_all_transactions.return_value = [{'id': 1, 'amount': 100}, {'id': 2, 'amount': 200}]
#             # call the endpoint with the public key and query_type as arguments
#         url = reverse('merchant_deposit_confirmation')
#         data = {'public_key': 'xyz', 'query_type': 'ifp'}
#         response = self.client.get(url, data)

#         # assert that the response is successful and the correct data is returned
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, {'all_transactions': [{'id': 1, 'amount': 100}, {'id': 2, 'amount': 200}], 'msg': 'for withdrawal transactions, deduct fee before sending to the User', 'status': 'success'})
#         mock_get_all_transactions.assert_called_once_with('xyz')

#     @mock.patch('path.to.get_transaction_by_pubKey')
#     def test_get_transactions_for_user(self, mock_get_transactions_by_pubkey):
#         # set up mock data to be returned by the function
#         mock_get_transactions_by_pubkey.return_value = [{'id': 1, 'amount': 100}, {'id': 2, 'amount': 200}]

#         # call the endpoint with the public key and query_type as arguments
#         url = reverse('merchant_deposit_confirmation')
#         data = {'public_key': 'xyz', 'query_type': 'user'}
#         response = self.client.get(url, data)

#         # assert that the response is successful and the correct data is returned
#         self.assertEqual(response.status_code, 200)
#         self.assertEqual(response.data, {'all_transactions': [{'id': 1, 'amount': 100}, {'id': 2, 'amount': 200}], 'msg': 'for withdrawal transactions, deduct fee before sending to the User', 'status': 'success'})
#         mock_get_transactions_by_pubkey.assert_called_once_with('xyz')
