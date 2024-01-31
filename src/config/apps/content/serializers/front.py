from rest_framework import serializers

from config.apps.catalog.models import Category
from config.apps.catalog.serializers.front import BrandSerializer, CategorySerializer
from config.apps.content.models import Banner
from config.apps.media.serializers.front import MediaFileNameSerializer


class BannerSerializer(serializers.ModelSerializer):
    image = MediaFileNameSerializer()

    class Meta:
        model = Banner
        fields = (
            "id",
            "image",
            "title",
            "position",
            "url",
            "is_external",
        )


class HomeDataSerializer(serializers.ModelSerializer):
    banners = BannerSerializer(many=True)
    products_nike = serializers.ListField()
    products_salomon = serializers.ListField()
    products_adidas = serializers.ListField()
    products_newbalance = serializers.ListField()

    class Meta:
        model = Banner
        fields = (
            "banners",
            "products_nike",
            "products_salomon",
            "products_adidas",
            "products_newbalance",
        )


class HeaderDataSerializer(serializers.ModelSerializer):
    brands = BrandSerializer(many=True)
    categories = CategorySerializer(many=True)

    class Meta:
        model = Category

        fields = (
            "brands",
            "categories",
        )
