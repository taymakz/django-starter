from django.contrib import admin

from . import models


@admin.register(models.VerifyOTPService)
class VerifyOTPServiceAdmin(admin.ModelAdmin):
    list_display = (
        "to",
        "code",
        "type",
        "is_expired",
    )

    @staticmethod
    def is_expired(obj):
        return obj.is_expired()
