from django.core.cache import cache
from django.db.models import Subquery, OuterRef, Q, Prefetch
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from config.api.enums import ResponseMessage
from config.api.response import PaginationApiResponse, BaseResponse
from config.apps.catalog.filters import ProductFilter
from config.apps.catalog.models import (
    Product,
    ProductImage,
    OptionGroup,
    ProductAttributeValue,
    ProductPropertyValue,
)
from config.apps.catalog.serializers.front import (
    ProductCardSerializer,
    SearchFilterOptionSerializer,
    ProductDetailSerializer,
    ProductDetailSchemaSerializer,
    ProductDetailChildrenSerializer,
)


class ProductSearchView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductCardSerializer
    pagination_class = PaginationApiResponse
    filterset_class = ProductFilter

    queryset = (
        Product.objects.only(
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
        .filter(
            is_public=True,
            structure__in=[
                Product.ProductTypeChoice.standalone,
                Product.ProductTypeChoice.parent,
            ],
        )
        .annotate(
            primary_image_file=Subquery(
                ProductImage.objects.select_related("image")
                .filter(product=OuterRef("pk"))
                .values("image__file")[:1]
            )
        )
    )


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
            options = (
                OptionGroup.objects.filter(filter_contain=True)
                .prefetch_related("option_group_values")
                .all()
            )
            data = SearchFilterOptionSerializer(options, many=True).data
            cache.set(
                "cached_filterOptions", data, timeout=None
            )  # No expiration for categories

            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )
        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class ProductDetailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductDetailSchemaSerializer

    def get(self, request, short_slug=None, *args, **kwargs):
        if not short_slug:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )

        try:
            product = Product.objects.only("structure").get(
                short_slug=short_slug,
                structure__in=[
                    Product.ProductTypeChoice.parent,
                    Product.ProductTypeChoice.standalone,
                ],
            )

            prefetch_images = Prefetch(
                "images",
                queryset=ProductImage.objects.all()
                .only(
                    "id", "product_id", "image__file", "image__width", "image__height"
                )
                .select_related("image"),
            )
            prefetch_attributes = Prefetch(
                "attribute_values",
                queryset=ProductAttributeValue.objects.all()
                .select_related(
                    "attribute",
                    "value_option",
                    "value_option__group",
                    "attribute__option_group",
                )
                .prefetch_related("value_multi_option"),
            )
            prefetch_properties = Prefetch(
                "properties",
                queryset=ProductPropertyValue.objects.all().select_related(
                    "property",
                ),
            )

            if product.structure == Product.ProductTypeChoice.parent:
                products = (
                    Product.objects.filter(
                        Q(
                            short_slug=short_slug,
                            structure__in=[
                                Product.ProductTypeChoice.parent,
                                Product.ProductTypeChoice.standalone,
                            ],
                        )
                        | Q(
                            parent__short_slug=short_slug,
                            structure=Product.ProductTypeChoice.child,
                        )
                    )
                    .select_related("stockrecord", "brand", "brand__image")
                    .prefetch_related(
                        prefetch_images, prefetch_attributes, prefetch_properties
                    )
                )

                parent_product = next(
                    (
                        p
                        for p in products
                        if p.structure == Product.ProductTypeChoice.parent
                    ),
                    None,
                )
                children_products = [
                    p
                    for p in products
                    if p.structure == Product.ProductTypeChoice.child
                ]

                parent_data = (
                    ProductDetailSerializer(parent_product).data
                    if parent_product
                    else None
                )
                if parent_data:
                    parent_data["children"] = ProductDetailChildrenSerializer(
                        children_products, many=True
                    ).data

                return BaseResponse(
                    data=parent_data,
                    status=status.HTTP_200_OK,
                    message=ResponseMessage.SUCCESS.value,
                )

            product = (
                Product.objects.select_related("stockrecord", "brand", "brand__image")
                .prefetch_related(
                    prefetch_images,
                    prefetch_attributes,
                    prefetch_properties,
                )
                .get(
                    short_slug=short_slug,
                    structure=Product.ProductTypeChoice.standalone,
                )
            )

            data = ProductDetailSerializer(product).data

            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value,
            )

        except Product.DoesNotExist:
            return BaseResponse(
                status=status.HTTP_404_NOT_FOUND, message=ResponseMessage.FAILED.value
            )

        except Exception as e:
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )
