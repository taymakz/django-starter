from rest_framework import serializers

from config.apps.catalog.models import Category, Brand, Product
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
        return {'name': obj.get('image', {}).get('name', '')}

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['children'] = self.many_nested(instance)
        return representation

    def many_nested(self, instance):
        children = instance.get('children', [])
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
        )


class ProductCardBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = (
            "title_ir",
            "title_en",
        )


class ProductCardSerializer(serializers.ModelSerializer):
    url = serializers.CharField(source='get_absolute_url')
    stockrecord = StockRecordCardSerializer()
    image = serializers.SerializerMethodField()
    brand = ProductCardBrandSerializer()

    class Meta:
        model = Product
        fields = (
            'image',
            'title_ir',
            'title_en',
            'slug',
            'upc',
            'url',
            'stockrecord',
            'brand',
        )

    def get_image(self, obj):
        return obj.primary_image_file
