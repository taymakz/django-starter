from django.core.cache import cache
from django.db.models import OuterRef, Subquery, Window, F
from django.db.models.functions import RowNumber
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import Category, Brand, Product, ProductImage
from config.apps.catalog.serializers.front import (
    BrandSerializer,
    CategorySerializer,
    ProductCardSerializer,
)
from config.apps.content.models import Banner
from config.apps.content.serializers.front import (
    HomeDataSerializer,
    BannerSerializer,
    HeaderDataSerializer,
)


class GetHomeDataView(APIView):
    serializer_class = HomeDataSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            response_data = {}
            # Check if data is in cache
            cached_banners = cache.get("cached_banners")
            if cached_banners:
                response_data["banners"] = cached_banners
            else:
                banners = Banner.objects.all().select_related("image")
                response_data["banners"] = BannerSerializer(banners, many=True).data
                cache.set("cached_banners", response_data["banners"], timeout=None)

            cached_products = cache.get("cached_brand_products")
            if cached_products:
                all_products = cached_products
            else:
                nike_brand_id = 1
                adidas_brand_id = 2
                salomon_brand_id = 9
                newbalance_brand_id = 11
                brand_ids = [
                    nike_brand_id,
                    adidas_brand_id,
                    salomon_brand_id,
                    newbalance_brand_id,
                ]

                # Sub Query for product first image
                primary_image_subquery = ProductImage.objects.filter(
                    product=OuterRef("pk")
                ).values("image__file")[:1]

                brand_products = (
                    Product.objects.only(
                        "title_ir",
                        "title_en",
                        "brand__title_en",
                        "brand__title_ir",
                        "brand__slug",
                        "product_class__track_stock",
                    )
                    .select_related("brand", "stockrecord", "product_class")
                    .filter(
                        brand_id__in=brand_ids,
                        is_public=True,
                        structure__in=[
                            Product.ProductTypeChoice.standalone,
                            Product.ProductTypeChoice.parent,
                        ],
                    )
                    .annotate(primary_image_file=Subquery(primary_image_subquery))
                    .annotate(
                        row_number=Window(
                            expression=RowNumber(),
                            partition_by=F("brand__title_en"),
                            order_by="order",
                        )
                    )
                ).filter(
                    row_number__lte=10
                )  # Take 10 item from Each Brands
                all_products = ProductCardSerializer(brand_products, many=True).data
                cache.set(
                    "cached_brand_products", all_products, timeout=24 * 60 * 60
                )  # 1 day Cache time

            response_data["products_nike"] = [
                product
                for product in all_products
                if product["brand"]["title_en"] == "nike"
            ]
            response_data["products_adidas"] = [
                product
                for product in all_products
                if product["brand"]["title_en"] == "adidas"
            ]
            response_data["products_salomon"] = [
                product
                for product in all_products
                if product["brand"]["title_en"] == "salomon"
            ]
            response_data["products_newbalance"] = [
                product
                for product in all_products
                if product["brand"]["title_en"] == "newbalance"
            ]

            return BaseResponse(
                response_data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class GetHeaderDataView(APIView):
    serializer_class = HeaderDataSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        try:
            # Check if data is in cache
            cached_brands = cache.get("cached_brands")
            cached_categories = cache.get("cached_categories")

            if cached_brands and cached_categories:
                return BaseResponse(
                    {
                        "brands": cached_brands,
                        "categories": cached_categories,
                    },
                    status=status.HTTP_200_OK,
                    message=ResponseMessage.SUCCESS.value,
                )

            # If not in cache, perform the queries

            categories = (
                Category.objects.filter(is_public=True)
                .only(
                    "id",
                    "tn_parent_id",
                    "tn_children_pks",
                    "title_ir",
                    "title_en",
                    "slug",
                    "image__id",
                    "image__file",
                    "image__width",
                    "image__height",
                )
                .select_related("image")
            ).order_by("tn_level")
            brands = (
                Brand.objects.only(
                    "id",
                    "title_ir",
                    "title_en",
                    "slug",
                    "image__id",
                    "image__file",
                    "image__width",
                    "image__height",
                )
                .select_related("image")
                .all()
            )

            # Serialize the data
            response_data = {
                "brands": BrandSerializer(brands, many=True).data,
                "categories": CategorySerializer(
                    Category.build_tree(categories=categories), many=True
                ).data,
            }

            # Set data in cache
            cache.set(
                "cached_brands", response_data["brands"], timeout=None
            )  # No expiration for brands
            cache.set(
                "cached_categories", response_data["categories"], timeout=None
            )  # No expiration for categories

            return BaseResponse(
                response_data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
