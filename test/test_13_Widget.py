from .test_setup  import TestSetUpClass
from django.urls import reverse
# from Api.templates.Api import widget


class WidgetHTMLTest(TestSetUpClass):
    """
    test the html template for widget
    """
    withdrawal_url = reverse("Widget Withdrawal")
    deposit_url = reverse("Widget Deposit")

    def test_1_success(self):
        """
        Test for success deposit template
        """
        req = self.client.get(self.withdrawal_url)
        self.assertTrue(req.headers["Content-Type"] == "text/html; charset=utf-8")
        self.assertTrue(req.status_code == 200)
        self.assertContains(req, "https://cdn.jsdelivr.net/gh/Cowryprotocol1/widget@main/deposit/deposit.js")
        self.assertContains(req, "https://cdn.jsdelivr.net/gh/Cowryprotocol1/widget@main/deposit/index-deposit.css")


    def test_2_success(self):
        req = self.client.get(self.deposit_url)
        self.assertTrue(req.headers["Content-Type"] == "text/html; charset=utf-8")
        self.assertTrue(req.status_code == 200)
        self.assertContains(req, "https://cdn.jsdelivr.net/gh/Cowryprotocol1/widget@main/withdraw/withdraw.js")
        self.assertContains(req, "https://cdn.jsdelivr.net/gh/Cowryprotocol1/widget@main/withdraw/index-withdraw.css")
