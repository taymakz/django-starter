from rest_framework import serializers

from config.apps.catalog.models import Product
from config.apps.catalog.serializers.front import ProductAttributeValueSerializer
from config.apps.inventory.serializers.front import StockRecordSerializer
from config.apps.order.models import OrderItem, Order, ShippingRate, ShippingService
from config.libs.persian.date import model_date_field_convertor


class ShippingServiceSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = ShippingService
        fields = ('id', 'name', 'image', 'url')

    def get_image(self, obj: ShippingService):
        if obj.image:
            return obj.image.file.name
        return None


class ShippingRateSerializer(serializers.ModelSerializer):
    service = ShippingServiceSerializer()

    class Meta:
        model = ShippingRate
        fields = (
            'id', 'service', 'area', 'price', 'all_area', 'free_shipping_threshold', 'pay_at_destination'
        )


class OrderItemProductSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    title_ir = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()
    track_stock = serializers.SerializerMethodField()
    stockrecord = StockRecordSerializer()
    attribute_values = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "title_ir",
            "title_en",
            "image",
            "url",
            "stockrecord",
            "track_stock",
            "attribute_values",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["attribute_values"] = (
            data["attribute_values"][0] if data["attribute_values"] else None
        )
        return data

    def get_title_ir(self, obj: Product):
        if obj.structure == Product.ProductTypeChoice.standalone:
            return obj.title_ir
        elif obj.structure == Product.ProductTypeChoice.child:
            return obj.parent.title_ir

    def get_title_en(self, obj: Product):
        if obj.structure == Product.ProductTypeChoice.standalone:
            return obj.title_en
        elif obj.structure == Product.ProductTypeChoice.child:
            return obj.parent.title_en

    def get_track_stock(self, obj: Product):
        if obj.structure == Product.ProductTypeChoice.standalone:
            return obj.product_class.track_stock
        elif obj.structure == Product.ProductTypeChoice.child:
            return obj.parent.product_class.track_stock

    def get_image(self, obj: Product):
        if obj.structure == Product.ProductTypeChoice.standalone:
            return obj.images.first().image.file.name
        elif obj.structure == Product.ProductTypeChoice.child:
            return obj.parent.images.first().image.file.name

    def get_url(self, obj: Product):
        if obj.structure == Product.ProductTypeChoice.standalone:
            return obj.get_absolute_url()
        elif obj.structure == Product.ProductTypeChoice.child:
            return obj.parent.get_absolute_url()


# Current Order ( Not Paid )
class OrderItemSerializer(serializers.ModelSerializer):
    product = OrderItemProductSerializer()

    class Meta:
        model = OrderItem
        fields = (
            "id",
            "product",
            "count",
        )


class OrderOpenSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        fields = ("id", "items")


class OrderPendingSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)
    price = serializers.SerializerMethodField()
    repayment_expire_at = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            "id",
            "items",
            "slug",
            "price",
            "repayment_expire_at",
        )

    def get_price(self, obj: Order):
        return obj.get_payment_price()

    def get_repayment_expire_at(self, obj: Order):
        return model_date_field_convertor(obj.repayment_expire_at)


class OrderSerializer(serializers.Serializer):
    open_order = OrderOpenSerializer()
    pending_orders = OrderPendingSerializer(many=True)
