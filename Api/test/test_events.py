import json, time
from .test_setup import TestSetUpClass
from django.urls import reverse




class EventTest(TestSetUpClass):


    # def test_events_0(self):
    #     # Testnet can be reset and hash will no longer be valid
    #     # this endpoint will always return 200, based the celery task we are using
    #     data = {
    #         "hash": "5de5bc0f18ec40d39d75293d13eb081807ee2ad231542571cff22827c5c484a6",
    #         "memo": "200525514585",
    #         "event_type": "user_withdrawals"
    #     }
    #     self.url = reverse('Listener')

    #     req_data = self.client.post(
    #         self.url, data=data, format="json")

    #     self.assertEqual(req_data.status_code, 200)
    #     self.assertTrue(req_data.data["hash"] == data["hash"])
    #     self.assertTrue(req_data.data["memo"] == data["memo"])
        # self.assertTrue(req_data.data["event_type"] == data["event_type"])

    def test_events_1(self):
        # Testnet can be reset and hash will no longer be valid
        # this endpoint will always return 200, based the celery task we are using
       

        self.url = reverse('onboard')
        response = self.client.post(self.url, self.onboarding_details)
        print(response.data)
        data = {
                "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
                "memo": response.data["user_details"]["UID"],
                "event_type": "merchant_staking"
            }
        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=data, format="json")

        self.assertEqual(req_data.status_code, 200)
        self.assertTrue(req_data.data["hash"] == data["hash"])
        self.assertTrue(req_data.data["memo"] == data["memo"])
        self.assertTrue(req_data.data["event_type"] == data["event_type"])

    def test_events_2(self):
        # print(self.general_keypair.public_key)
    
        self.url = reverse('onboard')
        response = self.client.post(self.url, self.onboarding_details)
        data_response = response.data

        event_data = {
            "hash": "202ff08e0dca56509f5fb3c77a11b92bac11efffe91063329a1ef77cd36eed22",
            "memo": data_response["user_details"]["UID"],
            "event_type": "merchant_staking"
        }

        self.url = reverse('Listener')

        req_data = self.client.post(
            self.url, data=event_data, format="json")

        print(req_data.data)
        print("Sleeping ...........")
        time.sleep(5)
        print("Done Sleeping ...........")

        self.url = reverse('Accounts')
        data = {"account_id":self.onboarding_details["blockchainAddress"]}

        req_data = self.client.generic(method="GET", path=self.url, data=json.dumps(
            data), content_type='application/json')
        print(req_data.data)
        print(req_data.data.stakedTokenAmount)

        working on the event listener testing, how do we enable merching hash and memo

        # self.assertEqual(req_data.status_code, 200)
        # self.assertTrue(req_data.data["hash"] == data["hash"])
        # self.assertTrue(req_data.data["memo"] == data["memo"])
        # self.assertTrue(req_data.data["event_type"] == data["event_type"])



