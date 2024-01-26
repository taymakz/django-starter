from django.core.cache import cache
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import BaseResponse
from config.apps.catalog.models import Category, Brand
from config.apps.catalog.serializers.front import (
    HeaderDataSerializer,
    BrandSerializer,
    CategorySerializer,
)


class GetHeaderDataView(APIView):
    serializer_class = HeaderDataSerializer
    authentication_classes = []
    permission_classes = [AllowAny]

    @staticmethod
    def _get_cached_data(key):
        # Helper function to get cached data
        return cache.get(key)

    @staticmethod
    def _set_cached_data(key, data, timeout=None):
        # Helper function to set data in cache
        cache.set(key, data, timeout)

    # @cache_page(60 * 15)  # Cache for 15 minutes
    def get(self, request, *args, **kwargs):
        try:
            # Check if data is in cache
            cached_brands = self._get_cached_data("cached_brands")
            cached_categories = self._get_cached_data("cached_categories")

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
                Category.objects.filter(tn_level=1)
                .only(
                    "id",
                    "title_ir",
                    "title_en",
                    "order",
                    "slug",
                    "image",
                    "tn_children_pks",
                )
                .select_related("image")
            )
            brands = (
                Brand.objects.only("id", "title_ir", "title_en", "image")
                .select_related("image")
                .all()
            )

            # Serialize the data
            response_data = {
                "brands": BrandSerializer(brands, many=True).data,
                "categories": CategorySerializer(categories, many=True).data,
            }

            # Set data in cache
            self._set_cached_data(
                "cached_brands", response_data["brands"], timeout=None
            )  # No expiration for brands
            self._set_cached_data(
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