from django.contrib import admin

from config.apps.transaction.models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["__str__", "created_at", "modified_at"]
