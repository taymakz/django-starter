from django.core.cache import cache
from django.db.models import Subquery, OuterRef
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import PaginationApiResponse, BaseResponse
from config.apps.catalog.filters import ProductFilter
from config.apps.catalog.models import Product, ProductImage, OptionGroup
from config.apps.catalog.serializers.front import ProductCardSerializer, SearchFilterOptionSerializer


class ProductSearchView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductCardSerializer
    pagination_class = PaginationApiResponse
    filterset_class = ProductFilter

    queryset = (Product.objects.only(
        "title_ir",
        "title_en",
        "slug",
        "upc",
        "structure",
        "brand__title_en",
        "brand__title_ir",
        "brand__slug",
    )
                .select_related("brand", "stockrecord")
                .prefetch_related("categories", "attributes__value_option", "images__image")
                .filter(is_public=True,
                        structure__in=[Product.ProductTypeChoice.standalone, Product.ProductTypeChoice.parent])
                .annotate(primary_image_file=Subquery(ProductImage.objects.select_related('image').filter(
        product=OuterRef("pk")
    ).values("image__file")[:1])))


class SearchFilterOptionView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = SearchFilterOptionSerializer

    def get(self, request, *args, **kwargs):
        try:
            cached_filterOptions = cache.get("cached_filterOptions")

            if cached_filterOptions:
                return BaseResponse(
                    cached_filterOptions,
                    status=status.HTTP_200_OK,
                    message=ResponseMessage.SUCCESS.value,
                )
            options = OptionGroup.objects.filter(filter_contain=True).prefetch_related('option_group_values').all()
            data = SearchFilterOptionSerializer(options, many=True).data
            cache.set(
                "cached_filterOptions", data, timeout=None
            )  # No expiration for categories

            return BaseResponse(data=data, status=status.HTTP_200_OK, message=ResponseMessage.SUCCESS.value)
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
