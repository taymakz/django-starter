from rest_framework import serializers


class VerificationRequestOTPSerializer(serializers.Serializer):
    to = serializers.CharField()
    otp_usage = serializers.CharField()
