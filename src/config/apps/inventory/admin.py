from django.contrib import admin

from config.apps.inventory.models import StockRecord


@admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    pass
