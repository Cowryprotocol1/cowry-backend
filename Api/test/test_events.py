import json, time
from unittest.mock import patch
from .test_setup import TestSetUpClass
from django.urls import reverse
from modelApp.utils import uidGenerator


class EventTest(TestSetUpClass):

    @patch("Api.views.is_transaction_memo_valid")
    def test_events_for_merchant_staking_pass(self, mock_memo):
        mock_memo.return_value = True
        data = {
                "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
                "memo": uidGenerator(13),
                "event_type": "merchant_staking"
            }
        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=data, format="json")
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertTrue(req_data.data["hash"] == data["hash"])
        self.assertTrue(req_data.data["memo"] == data["memo"])
        self.assertTrue(req_data.data["event_type"] == data["event_type"])

    @patch("Api.views.is_transaction_memo_valid")
    def test_events_2_for_user_withdrawals_pass(self, mock_memo):
        mock_memo.return_value = True
        event_data = {
            "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
            "memo": uidGenerator(),
            "event_type": "user_withdrawals"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")
        # # working on the event listener testing, how do we enable merching hash and memo
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["hash"] == event_data["hash"])
        self.assertTrue(req_data.data["memo"] == event_data["memo"])
        self.assertTrue(req_data.data["event_type"] == event_data["event_type"])

    # @patch("Api.views.is_transaction_memo_valid")
    def test_events_3_for_user_withdrawals_fail_invalid_memo(self):
        #mock a fake transaction hash
        # mock_memo.return_value = True
        event_data = {
            "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
            "memo": uidGenerator(),
            "event_type": "user_withdrawals"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")
        # # working on the event listener testing, how do we enable merching hash and memo
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue("error" in req_data.data)

    @patch("Api.views.is_transaction_memo_valid")
    def test_events_4_for_user_withdrawals_fail_invalid_hash(self, mock_memo):
        mock_memo.return_value = True
        #This will return 200 but will be ignore during the celery task execution
        event_data = {
            "hash": "Not a valid stellar hash",
            "memo": uidGenerator(),
            "event_type": "user_withdrawals"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")
        print(req_data.data)
        print(req_data.status_code)
        # # working on the event listener testing, how do we enable merching hash and memo
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(event_data["hash"] ==  req_data.data["hash"])
        self.assertTrue(event_data["memo"] ==  req_data.data["memo"])
        self.assertTrue(event_data["event_type"] ==  req_data.data["event_type"])


    def test_events_5_for_merchant_withdrawals_fail_invalid_memo(self):
        #mock a fake transaction hash
        event_data = {
            "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
            "memo": uidGenerator(),
            "event_type": "user_withdrawals"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")
        # # working on the event listener testing, how do we enable merching hash and memo
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertEqual(req_data.status_code, 400)
        self.assertTrue("error" in req_data.data)

    @patch("Api.views.is_transaction_memo_valid")
    def test_events_5_for_merchant_withdrawals_fail_invalid_hash(self, mock_memo):
        mock_memo.return_value = True
        #This will return 200 but will be ignore during the celery task execution
        event_data = {
            "hash": "Not a valid stellar hash",
            "memo": uidGenerator(),
            "event_type": "user_withdrawals"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")
        # # working on the event listener testing, how do we enable merching hash and memo
        self.assertTrue(req_data.headers["Content-Type"] == 'application/json')
        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(event_data["hash"] ==  req_data.data["hash"])
        self.assertTrue(event_data["memo"] ==  req_data.data["memo"])
        self.assertTrue(event_data["event_type"] ==  req_data.data["event_type"])



