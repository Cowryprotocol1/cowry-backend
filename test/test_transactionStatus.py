import json
from .test_setup import TestSetUpClass
from unittest.mock import patch
from django.urls import reverse


class TransactionStatusTest(TestSetUpClass):
    mock_data = [
        {
            "memo": "20069306662",
            "memo_bytes": "MjAwNjkzMDY2NjI=",
            "id": "7496f8216c46780a84e006c015a8f036caa22e0498855f2f7dbe3565aafaaa58",
            "paging_token": "3251908718370816",
            "successful": True,
            "hash": "7496f8216c46780a84e006c015a8f036caa22e0498855f2f7dbe3565aafaaa58",
            "ledger": 757144,
            "created_at": "2023-01-29T10:28:49Z",
            "source_account": "GDPN6O4BK7UWP4IU24Q5UEQ5WEG6TV3EN37C35YEWZZ4JLXFRB6CIW52",
            "source_account_sequence": "750403801055266",
            "fee_account": "GDPN6O4BK7UWP4IU24Q5UEQ5WEG6TV3EN37C35YEWZZ4JLXFRB6CIW52",
            "fee_charged": "500",
            "max_fee": "500",
            "operation_count": 5,
            "envelope_xdr": "AAAAAgAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAfQAAqp9AAAAIgAAAAEAAAAAAAAAAAAAAABj1k8LAAAAAQAAAAsyMDA2OTMwNjY2MgAAAAAFAAAAAQAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAABUAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAACTkdOQUxMT1cAAAAAAAAAAN7fO4FX6WfxFNch2hIdsQ3p12Ru/i33BLZzxK7liHwkAAAAAgAAAAEAAAABAAAAAN7fO4FX6WfxFNch2hIdsQ3p12Ru/i33BLZzxK7liHwkAAAAAQAAAAByZqSxvLQIeNDUGyiWYO8t7O/KZNUk76Ylg3PyNkrotQAAAAJOR05BTExPVwAAAAAAAAAA3t87gVfpZ/EU1yHaEh2xDenXZG7+LfcEtnPEruWIfCQAAAACVAvkAAAAAAEAAAAA3t87gVfpZ/EU1yHaEh2xDenXZG7+LfcEtnPEruWIfCQAAAAVAAAAAHJmpLG8tAh40NQbKJZg7y3s78pk1STvpiWDc/I2Sui1AAAAAk5HTkFMTE9XAAAAAAAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAAEAAAACAAAAAQAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAAEAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAABTkdOAAAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAABTck4AAAAAAQAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAAEAAAAAf2Xwzkg3BY7IA31vDFuXR2Wu3mt5y0fmfWrUGAP5vigAAAABTkdOAAAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAAAjw0YAAAAAAAAAAALrnJASAAAAQAbFjFTpZ8ToPe9Fkg4CNyZKKGQzGnNx0B9pz70rCfww1qjFtI0n6UDGNk3bv5CXneEkWiX/7xgfrUKohsz97wAD+b4oAAAAQJ1jNE3YXJ9Gyp/D+ajR6vTSzh6a3R5hNp8f+VQiDTstIJTcDmqb0gwLyh7OgQ6iFegIUR85zJ+w/KgKzcMscQU=",
            "result_xdr": "AAAAAAAAAfQAAAAAAAAABQAAAAAAAAAVAAAAAAAAAAAAAAABAAAAAAAAAAAAAAAVAAAAAAAAAAAAAAABAAAAAAAAAAAAAAABAAAAAAAAAAA=",
            "result_meta_xdr": "AAAAAgAAAAIAAAADAAuNmAAAAAAAAAAA3t87gVfpZ/EU1yHaEh2xDenXZG7+LfcEtnPEruWIfCQAAAAABfWdCAACqn0AAAAhAAAAAgAAAAAAAAALAAAAAAAyMlAAAAACAAAAAHP6TqLIQ4spWKi+GNrP3+chWmJvGAedaYRQkkzrnJASAAAAMgAAAAB/ZfDOSDcFjsgDfW8MW5dHZa7ea3nLR+Z9atQYA/m+KAAAAGQAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAMAAAAAAAuNAAAAAABj1kdFAAAAAAAAAAEAC42YAAAAAAAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAAAF9Z0IAAKqfQAAACIAAAACAAAAAAAAAAsAAAAAADIyUAAAAAIAAAAAc/pOoshDiylYqL4Y2s/f5yFaYm8YB51phFCSTOuckBIAAAAyAAAAAH9l8M5INwWOyAN9bwxbl0dlrt5rectH5n1q1BgD+b4oAAAAZAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAwAAAAAAC42YAAAAAGPWSmEAAAAAAAAABQAAAAIAAAADAAo0NgAAAAEAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAACTkdOQUxMT1cAAAAAAAAAAN7fO4FX6WfxFNch2hIdsQ3p12Ru/i33BLZzxK7liHwkAAABAB5gRwx//////////wAAAAYAAAAAAAAAAAAAAAEAC42YAAAAAQAAAAByZqSxvLQIeNDUGyiWYO8t7O/KZNUk76Ylg3PyNkrotQAAAAJOR05BTExPVwAAAAAAAAAA3t87gVfpZ/EU1yHaEh2xDenXZG7+LfcEtnPEruWIfCQAAAEAHmBHDH//////////AAAABQAAAAAAAAAAAAAAAgAAAAMAC42YAAAAAQAAAAByZqSxvLQIeNDUGyiWYO8t7O/KZNUk76Ylg3PyNkrotQAAAAJOR05BTExPVwAAAAAAAAAA3t87gVfpZ/EU1yHaEh2xDenXZG7+LfcEtnPEruWIfCQAAAEAHmBHDH//////////AAAABQAAAAAAAAAAAAAAAQALjZgAAAABAAAAAHJmpLG8tAh40NQbKJZg7y3s78pk1STvpiWDc/I2Sui1AAAAAk5HTkFMTE9XAAAAAAAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAQJybCsMf/////////8AAAAFAAAAAAAAAAAAAAACAAAAAwALjZgAAAABAAAAAHJmpLG8tAh40NQbKJZg7y3s78pk1STvpiWDc/I2Sui1AAAAAk5HTkFMTE9XAAAAAAAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAQJybCsMf/////////8AAAAFAAAAAAAAAAAAAAABAAuNmAAAAAEAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAACTkdOQUxMT1cAAAAAAAAAAN7fO4FX6WfxFNch2hIdsQ3p12Ru/i33BLZzxK7liHwkAAABAnJsKwx//////////wAAAAYAAAAAAAAAAAAAAAIAAAADAAo0NgAAAAEAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAABTkdOAAAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAAWKly4Af/////////8AAAABAAAAAAAAAAAAAAABAAuNmAAAAAEAAAAAcmaksby0CHjQ1BsolmDvLezvymTVJO+mJYNz8jZK6LUAAAABTkdOAAAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAAXeCXwAf/////////8AAAABAAAAAAAAAAAAAAACAAAAAwALjQAAAAABAAAAAH9l8M5INwWOyAN9bwxbl0dlrt5rectH5n1q1BgD+b4oAAAAAU5HTgAAAAAA+grBL9P3aABk6YcyNSx3cKC8GtgoF3mXmTXmyrtvNosAAAACg7rsAH//////////AAAAAQAAAAAAAAAAAAAAAQALjZgAAAABAAAAAH9l8M5INwWOyAN9bwxbl0dlrt5rectH5n1q1BgD+b4oAAAAAU5HTgAAAAAA+grBL9P3aABk6YcyNSx3cKC8GtgoF3mXmTXmyrtvNosAAAACp34yAH//////////AAAAAQAAAAAAAAAAAAAAAA==",
            "fee_meta_xdr": "AAAAAgAAAAMAC40AAAAAAAAAAADe3zuBV+ln8RTXIdoSHbEN6ddkbv4t9wS2c8Su5Yh8JAAAAAAF9Z78AAKqfQAAACEAAAACAAAAAAAAAAsAAAAAADIyUAAAAAIAAAAAc/pOoshDiylYqL4Y2s/f5yFaYm8YB51phFCSTOuckBIAAAAyAAAAAH9l8M5INwWOyAN9bwxbl0dlrt5rectH5n1q1BgD+b4oAAAAZAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAwAAAAAAC40AAAAAAGPWR0UAAAAAAAAAAQALjZgAAAAAAAAAAN7fO4FX6WfxFNch2hIdsQ3p12Ru/i33BLZzxK7liHwkAAAAAAX1nQgAAqp9AAAAIQAAAAIAAAAAAAAACwAAAAAAMjJQAAAAAgAAAABz+k6iyEOLKViovhjaz9/nIVpibxgHnWmEUJJM65yQEgAAADIAAAAAf2Xwzkg3BY7IA31vDFuXR2Wu3mt5y0fmfWrUGAP5vigAAABkAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAACAAAAAAAAAAAAAAADAAAAAAALjQAAAAAAY9ZHRQAAAAA=",
            "memo_type": "text",
            "signatures": [
                "BsWMVOlnxOg970WSDgI3JkooZDMac3HQH2nPvSsJ/DDWqMW0jSfpQMY2Tdu/kJed4SRaJf/vGB+tQqiGzP3vAA==",
                "nWM0Tdhcn0bKn8P5qNHq9NLOHprdHmE2nx/5VCINOy0glNwOapvSDAvKHs6BDqIV6AhRHznMn7D8qArNwyxxBQ==",
            ],
            "valid_after": "1970-01-01T00:00:00Z",
            "valid_before": "2023-01-29T10:48:43Z",
            "preconditions": {
                "timebounds": {"min_time": "0", "max_time": "1674989323"}
            },
        },
        {
            "memo": "50069306662",
            "memo_bytes": "MjAwNjkzMDY2NjI=",
            "id": "5583c663f71924ed64204ee36505f10b3cc27e083ffdae431c92022dde544f01",
            "paging_token": "3251522171310080",
            "successful": True,
            "hash": "5583c663f71924ed64204ee36505f10b3cc27e083ffdae431c92022dde544f01",
            "ledger": 757054,
            "created_at": "2023-01-29T10:20:54Z",
            "source_account": "GBBZ533CHWJBLNPNTRLBGZS4CLRQPBOHZNXQMLBMPVA2CY6R5XTTRAPV",
            "source_account_sequence": "2869781183070214",
            "fee_account": "GBBZ533CHWJBLNPNTRLBGZS4CLRQPBOHZNXQMLBMPVA2CY6R5XTTRAPV",
            "fee_charged": "100",
            "max_fee": "10000000",
            "operation_count": 1,
            "envelope_xdr": "AAAAAgAAAABDnu9iPZIVte2cVhNmXBLjB4XHy28GLCx9QaFj0e3nOACYloAACjINAAAABgAAAAEAAAAAAAAAAAAAAABj1kk2AAAAAQAAAAsyMDA2OTMwNjY2MgAAAAABAAAAAAAAAAEAAAAA+grBL9P3aABk6YcyNSx3cKC8GtgoF3mXmTXmyrtvNosAAAABTkdOAAAAAAD6CsEv0/doAGTphzI1LHdwoLwa2CgXeZeZNebKu282iwAAAALLQXgAAAAAAAAAAAHR7ec4AAAAQEYHoNMKfvXsC2+zxXmXlc9XEqwiiF+GrmWeWn+VFsHcHdmL9oF45AcCNvy59/Xd8Ye0ioLJ9Wh6yH27tyOlaww=",
            "result_xdr": "AAAAAAAAAGQAAAAAAAAAAQAAAAAAAAABAAAAAAAAAAA=",
            "result_meta_xdr": "AAAAAgAAAAIAAAADAAuNPgAAAAAAAAAAQ57vYj2SFbXtnFYTZlwS4weFx8tvBiwsfUGhY9Ht5zgAAAAXSHblqAAKMg0AAAAFAAAAAQAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAwAAAAAACjWsAAAAAGPPOvsAAAAAAAAAAQALjT4AAAAAAAAAAEOe72I9khW17ZxWE2ZcEuMHhcfLbwYsLH1BoWPR7ec4AAAAF0h25agACjINAAAABgAAAAEAAAAAAAAAAAAAAAABAAAAAAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAAAAgAAAAAAAAAAAAAAAAAAAAMAAAAAAAuNPgAAAABj1kiGAAAAAAAAAAEAAAACAAAAAwALjQAAAAABAAAAAEOe72I9khW17ZxWE2ZcEuMHhcfLbwYsLH1BoWPR7ec4AAAAAU5HTgAAAAAA+grBL9P3aABk6YcyNSx3cKC8GtgoF3mXmTXmyrtvNosAAAALpDt0AH//////////AAAAAQAAAAAAAAAAAAAAAQALjT4AAAABAAAAAEOe72I9khW17ZxWE2ZcEuMHhcfLbwYsLH1BoWPR7ec4AAAAAU5HTgAAAAAA+grBL9P3aABk6YcyNSx3cKC8GtgoF3mXmTXmyrtvNosAAAAI2Pn8AH//////////AAAAAQAAAAAAAAAAAAAAAA==",
            "fee_meta_xdr": "AAAAAgAAAAMACjWsAAAAAAAAAABDnu9iPZIVte2cVhNmXBLjB4XHy28GLCx9QaFj0e3nOAAAABdIduYMAAoyDQAAAAUAAAABAAAAAAAAAAAAAAAAAQAAAAAAAAAAAAABAAAAAAAAAAAAAAAAAAAAAAAAAAIAAAAAAAAAAAAAAAAAAAADAAAAAAAKNawAAAAAY886+wAAAAAAAAABAAuNPgAAAAAAAAAAQ57vYj2SFbXtnFYTZlwS4weFx8tvBiwsfUGhY9Ht5zgAAAAXSHblqAAKMg0AAAAFAAAAAQAAAAAAAAAAAAAAAAEAAAAAAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAACAAAAAAAAAAAAAAAAAAAAAwAAAAAACjWsAAAAAGPPOvsAAAAA",
            "memo_type": "text",
            "signatures": [
                "Rgeg0wp+9ewLb7PFeZeVz1cSrCKIX4auZZ5af5UWwdwd2Yv2gXjkBwI2/Ln39d3xh7SKgsn1aHrIfbu3I6VrDA=="
            ],
            "valid_after": "1970-01-01T00:00:00Z",
            "valid_before": "2023-01-29T10:23:50Z",
            "preconditions": {
                "timebounds": {"min_time": "0", "max_time": "1674987830"}
            },
        },
    ]
    @patch("Api.views.isTransaction_Valid.delay")
    @patch("Api.views.getStellar_tx_fromMemo")
    def test_valid_transaction_id_withdrawal(self, mock_transaction, mock_queu):
        mock_queu.return_value = "ok"
        mock_transaction.return_value = self.mock_data
        # Send a POST request to the API with a valid transaction ID for a withdrawal transaction
        response = self.client.post(
            reverse("transactionStatus"), data={"transactionId": "20069306662"}, format="json"
        )
        # Assert that the response has a 200 OK status code
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"] == 'application/json')

        # Assert that the response contains the expected message and status
        self.assertEqual(
            json.loads(response.content),
            {"msg": "we are updating your balance right away", "status": "success"},
        )
    @patch("Api.views.isTransaction_Valid.delay")
    @patch("Api.views.getStellar_tx_fromMemo")
    def test_valid_transaction_id_staking(self, mock_transaction, mock_queu):
        mock_queu.return_value = "ok"
        mock_transaction.return_value = self.mock_data
        # Send a POST request to the API with a valid transaction ID for a withdrawal transaction
        response = self.client.post(
            reverse("transactionStatus"), data={"transactionId": "50069306662"}, format="json"
        )
        # Assert that the response has a 200 OK status code
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.headers["Content-Type"] == 'application/json')

        # Assert that the response contains the expected message and status
        self.assertEqual(
            json.loads(response.content),
            {"msg": "we are updating your balance right away", "status": "success"},
        )
    @patch("Api.views.isTransaction_Valid.delay")
    @patch("Api.views.getStellar_tx_fromMemo")
    def test_invalid_transaction_id(self, mock_transaction, mock_queu):
        mock_queu.return_value = "ok"
        mock_transaction.return_value =[]
        # Send a POST request to the API with an invalid transaction ID
        response = self.client.post(
            reverse("transactionStatus"), data={"transactionId": "2006967898765"}, format="json"
        )

        # Assert that the response has a 400 Bad Request status code
        self.assertEqual(response.status_code, 400)

        # Assert that the response contains the expected message and status
        self.assertEqual(
            json.loads(response.content),
            {
                "msg": "no transaction with this transactionId found yet on the protocol account, please try again later",
                "status": "fail",
            },
        )

    def test_missing_transaction_id(self):
        # Send a POST request to the API without a transaction ID
        response = self.client.post(reverse("transactionStatus"))

        # Assert that the response has a 400 Bad Request status code
        self.assertEqual(response.status_code, 400)

        # Assert that the response contains the expected message and status
        self.assertEqual(
            json.loads(response.content),
            {
                "msg": "transactionId must be provided or you have provided an transactionId",
                "status": "fail",
            },
        )
