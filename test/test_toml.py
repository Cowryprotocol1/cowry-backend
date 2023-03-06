
from .test_setup import TestSetUpClass
from django.urls import reverse
import toml





class TomlTest(TestSetUpClass):
    TomlUrl =reverse("toml_endpoint")


    def test_001_toml(self):
        # test for successfully getting toml file
        req_data = self.client.generic(
            method="GET", path=self.TomlUrl
        )
        print(req_data.headers)
        toml_data = toml.loads(req_data.content.decode())
        print(toml_data)
        self.assertTrue(req_data["Content-Type"] == "text/plain; charset=utf-8")
        self.assertTrue("TRANSFER_SERVER" in toml_data)
        self.assertTrue("CURRENCIES" in toml_data)
        self.assertEqual(toml_data["CURRENCIES"][0]["code"], "NGN")
        self.assertTrue(req_data.headers["Access-Control-Allow-Origin"] == "*")
        
