from rest_framework import serializers

from ..models import User


class UserAdminSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name")
    has_password = serializers.BooleanField(source="has_usable_password")

    class Meta:
        model = User
        fields = (
            "full_name",
            "first_name",
            "last_name",
            "email",
            "phone",
            "national_code",
            "is_superuser",
            "is_verify",
            "has_password",
        )


# Authentication Section -------------------------------
class UserAdminLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserAdminAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()


class UserAdminPasswordAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserAdminOTPAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()


# Forgot Password Section -------------------------------


class UserAdminForgotPasswordCheckSerializer(serializers.Serializer):
    username = serializers.CharField()


class UserAdminForgotPasswordOTPSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()


class UserAdminForgotPasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()


class UserAdminEditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "first_name",
            "last_name",
            "national_code",
        )
