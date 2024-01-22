from rest_framework import serializers

from config.apps.messages.verification.enums import VerificationMessageUsageOptions


class VerificationRequestOTPSerializer(serializers.Serializer):
    to = serializers.CharField()
    otp_usage: VerificationMessageUsageOptions = serializers.CharField()
