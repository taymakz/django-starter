from rest_framework import serializers

from ..models import User


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='get_full_name')
    has_password = serializers.CharField(source='has_usable_password')

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
