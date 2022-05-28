

from django.urls import path, include
from .views import *


urlpatterns = [
    path('', index, name='index'),
    path('onboard', OnBoardMA.as_view(), name='onboard'),
    path('listener', EventListener.as_view(), name='Listener'),
    path('deposit', ON_RAMP_FIAT_USERS.as_view(), name='deposit'),
    path("merchants",
         MerchantDepositConfirmation.as_view(), name="merchants"),
    path("offboarding", OFF_BOARDING_MA.as_view(), name="offboard"),
    path("withdrawal", OFF_RAMP_FIAT.as_view(), name="withdrawal"),
]
