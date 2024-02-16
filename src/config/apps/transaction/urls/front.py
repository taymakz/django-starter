from django.urls import path

from config.apps.transaction.views import front

urlpatterns = [
    path('request/', front.OrderTransactionRequest.as_view(), name='transaction_request'),

]
