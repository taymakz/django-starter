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
    def receiver_fullname(obj):
        return obj.user.get_full_name()

    @staticmethod
    def destination(obj):
        return f"{obj.receiver_province} / {obj.receiver_city}"
