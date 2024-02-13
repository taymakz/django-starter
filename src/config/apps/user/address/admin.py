from django.contrib import admin

from .models import UserAddresses


@admin.register(UserAddresses)
class UserAddressesAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "receiver_fullname",
        "receiver_phone",
        "destination",
    )

    @staticmethod
    def receiver_fullname(obj: UserAddresses):
        return f"{obj.receiver_name} {obj.receiver_family}"

    @staticmethod
    def destination(obj):
        return f"{obj.receiver_province} / {obj.receiver_city}"
