from rest_framework import serializers

from config.apps.user.address.models import UserAddresses


class UserAddressesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAddresses
        fields = (
            "id",
            "receiver_name",
            "receiver_family",
            "receiver_phone",
            "receiver_national_code",
            "receiver_province",
            "receiver_city",
            "receiver_postal_code",
            "receiver_building_number",
            "receiver_unit",
            "receiver_address",
        )
