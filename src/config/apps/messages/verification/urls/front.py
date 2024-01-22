from django.urls import path

from config.apps.messages.verification.views import front

urlpatterns = [
    path('request/otp/', front.VerificationRequestOTPView.as_view(), name='verification_request_otp'),
]
