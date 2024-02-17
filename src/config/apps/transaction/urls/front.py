from django.urls import path

from config.apps.transaction.views import front

urlpatterns = [
    path('request/', front.TransactionRequest.as_view(), name='transaction_request'),
    path('request/repayment/', front.TransactionRePaymentRequest.as_view(), name='transaction_repayment_request'),
    path('verify/', front.TransactionVerify.as_view(), name='transaction_verify'),
    path('result/<str:transaction_number>/<str:transaction_slug>/', front.TransactionResult.as_view(),
         name='transaction_result'),

]
