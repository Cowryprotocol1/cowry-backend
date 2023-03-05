from test_setup  import TestSetUpClass
from django.urls import reverse
from unittest.mock import patch
from modelApp.models import TransactionsTable
from model_bakery import baker
from utils.utils import Id_generator


class TestInfoEndpointSep24(TestSetUpClass):
    base_url = reverse("Sep Transaction Info")


    def test_1_successInfo(self):
        """
        Test for transaction endpoint pulling for pending transaction
        """
        _id = Id_generator()
        trx = baker.make(TransactionsTable, id=_id, transaction_narration=("sep"+_id), transaction_type="deposit", transaction_amount=5000)
        print(trx)
        print(trx.transaction_status)
        print(trx.id)
        # mock_transaction.get.return_value = trx
        response = self.client.get(self.base_url, {"id":_id})
        print(response.status_code)
        json_response = response.json()
        self.assertTrue(response.headers["Content-Type"] == "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response["transaction"]["transaction_id"] == trx.id)
        self.assertTrue(json_response["transaction"]["kind"] == "deposit")
        self.assertTrue(json_response["transaction"]["status"] == "pending")
        self.assertTrue(json_response["transaction"]["eta"] == 3600)


    def test_2_successInfo(self):
        """
        Test for transaction endpoint pulling for confirm transaction
        """
        _id = Id_generator()
        trx = baker.make(TransactionsTable, id=_id, transaction_narration=("sep"+_id), transaction_type="deposit", transaction_amount=5000, transaction_status="confirm")
        response = self.client.get(self.base_url, {"id":_id})
        json_response = response.json()
        self.assertTrue(response.headers["Content-Type"] == "application/json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(json_response["transaction"]["transaction_id"] == trx.id)
        self.assertTrue(json_response["transaction"]["kind"] == "deposit")
        self.assertTrue(json_response["transaction"]["status"] == "confirm")
        self.assertTrue(json_response["transaction"]["eta"] == 3600)




    def test_3_successInfo(self):
        """
        failed transaction with no query params
        """
        response = self.client.get(self.base_url)
        self.assertTrue(response.headers["Content-Type"] == "application/json")
        self.assertEqual(response.status_code, 400)
        self.assertTrue("error" in response.json())
        
