from .test_setup import TestSetUpClass
from django.urls import reverse




class EventTest(TestSetUpClass):


    def test_events(self):
        data = {
            "hash": "5de5bc0f18ec40d39d75293d13eb081807ee2ad231542571cff22827c5c484a6",
            "memo": "200525514585",
            "event_type": "user_withdrawals"
        }
        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=data, format="json")

        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["hash"] == data["hash"])
        self.assertTrue(req_data.data["memo"] == data["memo"])
        self.assertTrue(req_data.data["event_type"] == data["event_type"])


