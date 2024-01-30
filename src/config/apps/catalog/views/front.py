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
    CategorySerializer, CategorySerializerTest, )


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
                Category.objects.filter(tn_level=1, is_public=True)
                .only(
                    "id",
                    "title_ir",
                    "title_en",
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


class GetHeaderDataViewTest(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def build_tree(self, categories, parent_id=None):
        tree = []
        for category in categories:
            if category.tn_parent_id == parent_id:
                node = CategorySerializerTest(category).data
                node["children"] = self.build_tree(categories, parent_id=category.id)
                tree.append(node)
        return tree

    def get(self, request, *args, **kwargs):
        categories = (
            Category.objects.filter(is_public=True).select_related(
                'image', ).only("id", "tn_parent_id", "tn_level", "tn_children_pks", "title_ir", "title_en", "slug",
                                "image")
        ).order_by('tn_level')
        # TODO : need a Serializer
        # Build the tree structure
        tree = self.build_tree(categories)
        return BaseResponse(
            tree,
            status=status.HTTP_200_OK,
            message=ResponseMessage.SUCCESS.value,
        )
