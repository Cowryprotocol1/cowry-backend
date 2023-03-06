# from rest_framework.test import APITestCase
from .test_setup import TestSetUpClass
from modelApp.utils import update_PendingTransaction_Model

class TestUpdatePendingTransactionModel(TestSetUpClass):
    def test_update_PendingTransaction_Model(self):
        # Test with all required and optional parameters
        transaction_amt = "100.00"
        transaction_type = "credit"
        narration = "Test transaction"
        transaction_hash = "abc123"
        transaction_memo = "Test memo"
        user_block_address = "0x123"
        phone_num = "123-456-7890"
        email = "test@example.com"
        user_bank_account = "1234567890"
        bank_name = "Test Bank"
        result = update_PendingTransaction_Model(
            transaction_amt,
            transaction_type,
            narration,
            transaction_hash,
            transaction_memo,
            user_block_address,
            phone_num,
            email,
            user_bank_account,
            bank_name
        )
        self.assertIsNotNone(result)
        self.assertEqual(result.users_address, user_block_address)
        self.assertEqual(result.transaction_type, transaction_type)
        self.assertEqual(result.transaction_amount, transaction_amt)
        self.assertEqual(result.transaction_hash, transaction_hash)
        self.assertEqual(result.transaction_memo, transaction_memo)
        self.assertEqual(result.user_phone, phone_num)
        self.assertEqual(result.user_email, email)
        self.assertEqual(result.user_bank_account, user_bank_account)
        self.assertEqual(result.user_bank_name, bank_name)
        self.assertEqual(result.transaction_narration, narration)

    def test_update_PendingTransaction_Model_missing_parameter(self):
        # Test with only required parameters
        transaction_amt = "100.00"
        transaction_type = "credit"
        narration = "Test transaction"
        result = update_PendingTransaction_Model(transaction_amt, transaction_type, narration)
        print(result)
        self.assertIsNotNone(result)
        self.assertIsNone(result.users_address)
        self.assertEqual(result.transaction_type, transaction_type)
        self.assertEqual(result.transaction_amount, transaction_amt)
        self.assertIsNone(result.transaction_hash)
        self.assertIsNone(result.transaction_memo)
        self.assertIsNone(result.user_phone)
        self.assertIsNone(result.user_email)
        self.assertIsNone(result.user_bank_account)
        self.assertIsNone(result.user_bank_name)
        self.assertEqual(result.transaction_narration, narration)
