from rest_framework import serializers

from config.apps.catalog.models import Category, Brand, Product, OptionGroup, OptionGroupValue
from config.apps.inventory.serializers.front import StockRecordCardSerializer
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
    brand = ProductCardBrandSerializer()

    class Meta:
        model = Product
        fields = (
            "image",
            "title_ir",
            "title_en",
            "slug",
            "upc",
            "url",
            "stockrecord",
            "brand",
        )

    def get_image(self, obj):
        return obj.primary_image_file


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
        fields = (
            "id",
            "title",
            "filter_param_name",
            "option_group_values"
        )
