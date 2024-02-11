from rest_framework import serializers

from config.apps.inventory.models import StockRecord


class StockRecordCardSerializer(serializers.ModelSerializer):
    special_sale_price = serializers.SerializerMethodField()
    special_sale_price_start_at = serializers.SerializerMethodField()
    special_sale_price_end_at = serializers.SerializerMethodField()

    class Meta:
        model = StockRecord
        fields = (
            "sale_price",
            "special_sale_price",
            "special_sale_price_start_at",
            "special_sale_price_end_at",
            "num_stock",
            "in_order_limit",
        )

    def get_special_sale_price(self, obj: StockRecord):
        if obj.has_special_price_with_date:
            return obj.special_sale_price if obj.is_special_price_dates_valid else None
        return obj.special_sale_price

    def get_special_sale_price_start_at(self, obj: StockRecord):
        return (
            obj.special_sale_price_start_at
            if obj.is_special_price_dates_valid
            else None
        )

    def get_special_sale_price_end_at(self, obj: StockRecord):
        return (
            obj.special_sale_price_end_at if obj.is_special_price_dates_valid else None
        )


class StockRecordSerializer(serializers.ModelSerializer):
    special_sale_price = serializers.SerializerMethodField()
    special_sale_price_start_at = serializers.SerializerMethodField()
    special_sale_price_end_at = serializers.SerializerMethodField()

    class Meta:
        model = StockRecord
        fields = (
            "id",
            "sku",
            "sale_price",
            "special_sale_price",
            "special_sale_price_start_at",
            "special_sale_price_end_at",
            "num_stock",
            "in_order_limit",
        )

    def get_special_sale_price(self, obj: StockRecord):
        if obj.has_special_price_with_date:
            return obj.special_sale_price if obj.is_special_price_dates_valid else None
        return obj.special_sale_price

    def get_special_sale_price_start_at(self, obj: StockRecord):
        return (
            obj.special_sale_price_start_at
            if obj.is_special_price_dates_valid
            else None
        )

    def get_special_sale_price_end_at(self, obj: StockRecord):
        return (
            obj.special_sale_price_end_at if obj.is_special_price_dates_valid else None
        )
