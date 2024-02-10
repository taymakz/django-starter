from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.messages.verification.models import VerifyOTPService
from config.apps.messages.verification.serializers.front import (
    VerificationRequestOTPSerializer,
)
from config.apps.user.account.models import User
from config.libs.validator.validators import validate_phone, validate_email


class VerificationRequestOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    serializer_class = VerificationRequestOTPSerializer

    def post(self, request, format=None):
        serializer = VerificationRequestOTPSerializer(data=request.data)

        # Check if refresh token is provided
        if not serializer.is_valid():
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        to = serializer.validated_data.get("to").lower()
        otp_usage = serializer.validated_data.get("otp_usage")
        to = User.get_formatted_username(to)

        if validate_phone(to):
            contact_type = VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE
        elif validate_email(to):
            contact_type = VerifyOTPService.VerifyOTPServiceTypeChoice.EMAIL
        else:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
        contact_info = to if validate_phone(to) else to
        otp_service = (
            VerifyOTPService.objects.filter(
                type=contact_type, to=contact_info, usage=otp_usage
            )
            .order_by("-id")
            .first()
        )

        if otp_service:
            if otp_service.is_expired():
                otp_service.delete()
            else:
                return BaseResponse(
                    status=status.HTTP_200_OK,
                    message=f"{ResponseMessage.PHONE_OTP_SENT.value.format(username=to) if VerifyOTPService.VerifyOTPServiceTypeChoice.PHONE else ResponseMessage.EMAIL_OTP_SENT.value.format(username=to)}",
                )

        new_otp_service = VerifyOTPService.objects.create(
            type=contact_type, to=contact_info, usage=otp_usage
        )
        new_otp_service.send_otp()

        return BaseResponse(
            status=status.HTTP_200_OK,
            message=f'{ResponseMessage.PHONE_OTP_SENT.value.format(username=to) if contact_type == "PHONE" else ResponseMessage.EMAIL_OTP_SENT.value.format(username=to)}',
        )
