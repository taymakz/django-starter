from rest_framework import serializers

from config.apps.catalog.models import (
    Category,
    Brand,
    Product,
    OptionGroup,
    OptionGroupValue,
    ProductAttributeValue,
    ProductAttribute,
    ProductImage,
    ProductProperty,
    ProductPropertyValue,
)
from config.apps.inventory.serializers.front import (
    StockRecordCardSerializer,
    StockRecordSerializer,
)
from config.apps.media.serializers.front import MediaFileNameSerializer


class CategoryTreeSerializer(serializers.ModelSerializer):
    image = MediaFileNameSerializer()
    children = serializers.ListField()

    class Meta:
        model = Category
        fields = (
            "id",
            "image",
            "title_ir",
            "title_en",
            "slug",
            "children",
        )


class CategorySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    image = serializers.SerializerMethodField()
    title_ir = serializers.CharField()
    title_en = serializers.CharField()
    slug = serializers.SlugField()
    children = serializers.ListField(child=serializers.DictField(), default=[])

    def get_image(self, obj):
        return {"name": obj.get("image", {}).get("name", "")}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation["children"] = self.many_nested(instance)
        return representation

    def many_nested(self, instance):
        children = instance.get("children", [])
        serializer = self.__class__(children, many=True)
        return serializer.data


class BrandSerializer(serializers.ModelSerializer):
    image = MediaFileNameSerializer()

    class Meta:
        model = Brand
        fields = (
            "id",
            "image",
            "title_ir",
            "title_en",
            "slug",
        )


class ProductCardBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            "title_ir",
            "title_en",
            "slug",
        )


class ProductCardSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source="get_absolute_url")
    stockrecord = StockRecordCardSerializer()
    image = serializers.SerializerMethodField()
    track_stock = serializers.SerializerMethodField()
    brand = ProductCardBrandSerializer()

    class Meta:
        model = Product
        fields = (
            "image",
            "title_ir",
            "title_en",
            "url",
            "stockrecord",
            "track_stock",
            "brand",
        )

    def get_image(self, obj):
        return obj.primary_image_file

    def get_track_stock(self, obj: Product):
        return obj.product_class.track_stock


class OptionGroupValueSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionGroupValue
        fields = (
            "id",
            "title",
            "color_code",
        )


class SearchFilterOptionSerializer(serializers.ModelSerializer):
    option_group_values = OptionGroupValueSerializer(many=True)

    class Meta:
        model = OptionGroup
        fields = ("id", "title", "filter_param_name", "option_group_values")


class ProductOptionGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = OptionGroup
        fields = (
            "id",
            "title",
        )


class ProductAttributeSerializer(serializers.ModelSerializer):
    option_group = ProductOptionGroupSerializer()

    class Meta:
        model = ProductAttribute
        fields = (
            "title",
            "type",
            "option_group",
            "required",
        )


class ProductOptionGroupValueSerializer(serializers.ModelSerializer):
    group = ProductOptionGroupSerializer()

    class Meta:
        model = OptionGroupValue
        fields = (
            "id",
            "title",
            "color_code",
            "group",
        )


class ProductAttributeValueSerializer(serializers.ModelSerializer):
    attribute = ProductAttributeSerializer()
    value_option = ProductOptionGroupValueSerializer()
    value_multi_option = ProductOptionGroupValueSerializer(many=True)

    class Meta:
        model = ProductAttributeValue
        fields = (
            "id",
            "attribute",
            "value_text",
            "value_integer",
            "value_float",
            "value_option",
            "value_multi_option",
        )


class ProductImageSerializer(serializers.ModelSerializer):
    image = MediaFileNameSerializer()

    class Meta:
        model = ProductImage
        fields = ("id", "image")


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = (
            "id",
            "title_ir",
            "slug",
        )


class ProductPropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductProperty
        fields = (
            "id",
            "name",
        )


class ProductPropertyValueSerializer(serializers.ModelSerializer):
    property = ProductPropertySerializer()

    class Meta:
        model = ProductPropertyValue
        fields = ("id", "property", "value")


class ProductDetailChildrenSerializer(serializers.ModelSerializer):
    stockrecord = StockRecordSerializer()
    images = ProductImageSerializer(many=True)
    attribute_values = ProductAttributeValueSerializer(many=True)

    class Meta:
        model = Product
        fields = (
            "id",
            "stockrecord",
            "attribute_values",
            "images",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.structure == Product.ProductTypeChoice.child:
            data["attribute_values"] = (
                data["attribute_values"][0] if data["attribute_values"] else None
            )
        return data


# product Detail
class ProductDetailSerializer(serializers.ModelSerializer):
    attribute_values = ProductAttributeValueSerializer(many=True)
    stockrecord = StockRecordSerializer()
    images = ProductImageSerializer(many=True)
    brand = BrandSerializer()
    properties = ProductPropertyValueSerializer(many=True)
    track_stock = serializers.SerializerMethodField()
    url = serializers.CharField(source="get_absolute_url")

    class Meta:
        model = Product
        fields = (
            "id",
            "structure",
            "attribute_values",
            "images",
            "url",
            "title_ir",
            "title_en",
            "short_slug",
            "stockrecord",
            "track_stock",
            "brand",
            "meta_title",
            "meta_description",
            "properties",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.structure == Product.ProductTypeChoice.parent:
            data["attribute_values"] = None
        return data

    def get_track_stock(self, obj: Product):
        return obj.product_class.track_stock


# this is only For Schema
class ProductDetailSchemaSerializer(serializers.ModelSerializer):
    children = ProductDetailChildrenSerializer(many=True)
    attribute_values = ProductAttributeValueSerializer(many=True)
    stockrecord = StockRecordSerializer()
    images = ProductImageSerializer(many=True)
    brand = BrandSerializer()
    url = serializers.CharField(source="get_absolute_url")

    class Meta:
        model = Product
        fields = (
            "id",
            "structure",
            "children",
            "attribute_values",
            "images",
            "url",
            "title_ir",
            "title_en",
            "stockrecord",
            "brand",
            "meta_title",
            "meta_description",
        )

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if instance.structure != Product.ProductTypeChoice.child:
            data["attribute_values"] = None
        return data
