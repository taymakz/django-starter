from rest_framework import serializers

from config.apps.catalog.models import Product
from config.apps.catalog.serializers.front import ProductAttributeValueSerializer
from config.apps.inventory.serializers.front import StockRecordSerializer
from config.apps.order.models import OrderItem, Order


class OrderItemProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    stockrecord = StockRecordSerializer()
    attribute = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            'id',
            'image',
            'title_ir',
            'title_en',
            'url',
            'stockrecord',
            'attribute',
        ),

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["attribute"] = (
            data["attribute"][0] if data["attribute"] else None
        )
        return data

    def get_image(self, obj):
        return obj.primary_image_file

    def get_url(self, obj: Product):
        return obj.get_absolute_url()


# Current Order ( Not Paid )
class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer()

    class Meta:
        model = OrderItem
        fields = (
            'id',
            'product',
            'count',
        )


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = (
            'id',
            'items'
        )
