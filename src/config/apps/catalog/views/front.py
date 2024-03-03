from django.core.cache import cache
from django.db.models import (
    Subquery,
    OuterRef,
    Q,
    Prefetch,
    BooleanField,
    Case,
    When,
    Exists,
)
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from config.api.enums import ResponseMessage
from config.api.response import PaginationApiResponse, BaseResponse
from config.apps.catalog.filters import ProductFilter
from config.apps.catalog.models import (
    Product,
    ProductImage,
    OptionGroup,
    ProductAttributeValue,
    ProductPropertyValue,
    OptionGroupValue,
    ProductComment,
)
from config.apps.catalog.serializers.front import (
    ProductCardSerializer,
    SearchFilterOptionSerializer,
    ProductDetailSerializer,
    ProductDetailSchemaSerializer,
    ProductDetailChildrenSerializer,
    ProductCommentListSerializer,
    ProductCommentCreateSerializer,
)
from config.apps.order.models import OrderItem, Order


class ProductSearchView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = ProductCardSerializer
    pagination_class = PaginationApiResponse
    filterset_class = ProductFilter

    queryset = (
        Product.objects.only(
            "id",
            "title_ir",
            "title_en",
            "slug",
            "short_slug",
            "structure",
            "brand__title_en",
            "brand__title_ir",
            "brand__slug",
            "product_class__track_stock",
        )
        .select_related("brand", "stockrecord", "product_class")
        .prefetch_related("categories", "attributes__value_option")
        .filter(
            is_public=True,
            structure__in=[
                Product.ProductTypeChoice.standalone,
                Product.ProductTypeChoice.parent,
            ],
        )
        .annotate(
            is_available=Case(
                When(
                    product_class__track_stock=True,
                    then=Case(
                        When(stockrecord__num_stock__gt=0, then=True),
                        default=False,
                        output_field=BooleanField(),
                    ),
                ),
                default=True,
                output_field=BooleanField(),
            )
        )
        .order_by("-is_available")
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

            primary_image_subquery = ProductImage.objects.filter(
                product=OuterRef("pk")
            ).values("image__file")[:1]
            prefetch_recommended_products = Prefetch(
                "recommended_products",
                queryset=Product.objects.only(
                    "id",
                    "title_ir",
                    "title_en",
                    "slug",
                    "short_slug",
                    "brand__title_en",
                    "brand__title_ir",
                    "brand__slug",
                    "product_class__track_stock",
                )
                .select_related("brand", "stockrecord", "product_class")
                .filter(
                    is_public=True,
                )
                .annotate(primary_image_file=Subquery(primary_image_subquery)),
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
                .prefetch_related(
                    Prefetch(
                        "value_multi_option",
                        queryset=OptionGroupValue.objects.select_related("group").all(),
                    )
                ),
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
                    .select_related(
                        "stockrecord", "brand", "brand__image", "product_class"
                    )
                    .prefetch_related(
                        prefetch_recommended_products,
                        prefetch_images,
                        prefetch_attributes,
                        prefetch_properties,
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
                Product.objects.select_related(
                    "stockrecord", "brand", "brand__image", "product_class"
                )
                .prefetch_related(
                    prefetch_recommended_products,
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
            print(e)
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST, message=ResponseMessage.FAILED.value
            )


class ProductCommentListAPIView(ListAPIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    pagination_class = PaginationApiResponse
    serializer_class = ProductCommentListSerializer
    queryset = ProductComment.objects.filter(accept_by_admin=True).annotate(
        is_buyer=Case(
            When(user=None, then=False),  # If user is None, they cannot be a buyer
            default=Exists(
                OrderItem.objects.only(
                    "product_id",
                    "product__parent_id",
                    "order__user_id",
                    "order__payment_status",
                )
                .select_related("product")
                .filter(
                    Q(product_id=OuterRef("product"))
                    | Q(product__parent_id=OuterRef("product")),
                    order__user_id=OuterRef("user"),
                    order__payment_status=Order.PaymentStatusChoice.PAID,
                )
            ),
            output_field=BooleanField(),
        )
    )

    def list(self, request, *args, **kwargs):
        product_id = request.data.get("product_id", None)
        if not product_id:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
        # Filter the queryset using the provided product_id
        queryset = super().get_queryset()

        # Proceed with standard list view behavior
        page = self.paginate_queryset(queryset)

        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)


class ProductCommentCreateAPIView(ListAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = ProductCommentCreateSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return BaseResponse(
                data=serializer.data,
                status=status.HTTP_201_CREATED,
                message=ResponseMessage.SUCCESS.value,
            )
        return BaseResponse(
            status=status.HTTP_400_BAD_REQUEST,
            message=serializer.errors,
        )
