from rest_framework import serializers

from config.apps.inventory.models import StockRecord


class StockRecordCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockRecord
        fields = (
            "sale_price",
            "special_sale_price",
            "special_sale_price_start_at",
            "special_sale_price_end_at",
            "num_stock",
        )
