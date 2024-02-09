from django.contrib import admin

from config.apps.inventory.models import StockRecord


@admin.register(StockRecord)
class StockRecordAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "product_title",
        "buy_price",
        "sale_price",
        "special_sale_price",
        "special_sale_price_start_at",
        "special_sale_price_end_at",
        "num_stock",
        "threshold_low_stack",
    )
    list_editable = (
        "buy_price",
        "sale_price",
        "special_sale_price",
        "special_sale_price_start_at",
        "special_sale_price_end_at",
        "num_stock",
        "threshold_low_stack",
    )

    def product_title(self, obj: StockRecord):
        if obj.product.structure == obj.product.ProductTypeChoice.child:
            return f"child: {obj.product.parent.title_en}"
        return f"P-S: {obj.product.title_en}"
