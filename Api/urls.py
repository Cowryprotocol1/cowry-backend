

from django.urls import path, include
from .views import *


urlpatterns = [
    path('', IndexPage.as_view(), name='index'),
    path('onboard', OnBoardMA.as_view(), name='onboard'), #Tested
    path('deposit', ON_RAMP_FIAT_USERS.as_view(), name='deposit'), #tested
    path("merchants",
        MerchantDepositConfirmation.as_view(), name="merchants"), #tested
    path("offboarding", OFF_BOARDING_MA.as_view(), name="offboard"), #tested
    path("withdrawal", OFF_RAMP_FIAT.as_view(), name="withdrawal"), #tested
    path("totalSupply", AllTokenTotalSupply.as_view(), name="totalSupply"), #tested
    path("accounts", AccountDetails.as_view(), name="Accounts"), #tested
    path(".well-known/stellar.toml", StellarToml.as_view(), name="toml_endpoint"), #tested
    path("sep6/deposit", Sep6Deposit, name="sep6Deposit"), #tested
    path("sep6/info", sepInfo, name="sep6Info"), #tested
    path("sep6/withdraw", sep6Withdrawal, name="sep6Withdraw"), #tested
    path("submit_xdr", SubmitAnXdr.as_view(), name="submitxdr"),
    path("audit_protocol", auditProtocol, name="audit"), #tested
    path("transactionStatus", transactionStatus, name="transactionStatus") #tested
    # path("transactions/deposit/interactive", sep24Withdrawal, name='sep24Stellar')
    # path("canceltransaction", TransactionExpire.as_view(), name="TransactionExpire")
    


]
