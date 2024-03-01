from rest_framework import serializers

from ..models import User, UserSearchHistory


class UserSearchHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSearchHistory
        fields = ("id", "search")


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source="get_full_name")
    has_password = serializers.CharField(source="has_usable_password")
    search_histories = UserSearchHistorySerializer(many=True)

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
            "search_histories",
        )


# Authentication Section -------------------------------
class UserLogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class UserAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()


class UserPasswordAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()


class UserOTPAuthenticationCheckSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()


# Forgot Password Section -------------------------------


class UserForgotPasswordCheckSerializer(serializers.Serializer):
    username = serializers.CharField()


class UserForgotPasswordOTPSerializer(serializers.Serializer):
    username = serializers.CharField()
    otp = serializers.CharField()


class UserForgotPasswordResetSerializer(serializers.Serializer):
    username = serializers.CharField()
    token = serializers.CharField()
    password = serializers.CharField()
    confirm_password = serializers.CharField()


class UserEditProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'national_code',
        )
