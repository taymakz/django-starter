from django.core.cache import cache
from django.db.models import (
    Subquery,
    OuterRef,
    Q,
    Prefetch,
    BooleanField,
    Case,
    When,
    Exists, Count,
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
    ProductComment, Brand, )
from config.apps.catalog.serializers.front import (
    ProductCardSerializer,
    SearchFilterOptionSerializer,
    ProductDetailSerializer,
    ProductDetailSchemaSerializer,
    ProductDetailChildrenSerializer,
    ProductCommentListSerializer,
    ProductCommentCreateSerializer, CatalogSearchSerializer, CatalogSearchProductSerializer,
    CatalogSearchBrandSerializer,
)
from config.apps.catalog.tasks import add_product_visit_celery
from config.apps.order.models import OrderItem, Order


class CatalogSearchView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = CatalogSearchSerializer

    def get(self, request, *args, **kwargs):
        try:
            query = self.request.query_params.get('q', '')
            if len(query) < 3:  # only search if query length is more than 3 characters
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
            products = Product.objects.select_related('product_class', 'stockrecord').only(
                "id",
                "title_ir",
                "title_en",
                "slug",
                "short_slug",
                "upc",
                "is_public",
                "structure",
                "product_class__track_stock",
            ).filter(
                Q(title_ir__icontains=query) |
                Q(title_en__icontains=query) |
                Q(short_slug__icontains=query) |
                Q(upc__icontains=query),
                is_public=True,
                structure__in=[
                    Product.ProductTypeChoice.standalone,
                    Product.ProductTypeChoice.parent,
                ]).annotate(
                primary_image_file=Subquery(
                    ProductImage.objects.select_related("image")
                    .filter(product=OuterRef("pk"))
                    .values("image__file")[:1]
                )
            ).annotate(
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
            ).order_by("-is_available").distinct()[:10]

            brands = Brand.objects.select_related('image').only("id", "title_ir", "title_en", "slug", "image__file",
                                                                "image__width", "image__height").filter(
                Q(title_ir__icontains=query) |
                Q(title_en__icontains=query) |
                Q(slug__icontains=query)
            ).distinct()[:3]

            data = {
                "products": CatalogSearchProductSerializer(products, many=True).data,
                "brands": CatalogSearchBrandSerializer(brands, many=True).data
            }
            return BaseResponse(
                data=data,
                status=status.HTTP_200_OK,
                message=ResponseMessage.SUCCESS.value
            )
        except Exception as e:
            print(e)
            return BaseResponse(
                status=status.HTTP_400_BAD_REQUEST,
                message=ResponseMessage.FAILED.value
            )


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
                            Q(
                                stockrecord__num_stock__gt=0,
                                parent__product_class__track_stock=True,
                            )
                            | Q(parent__product_class__track_stock=False)
                            ,
                            parent__short_slug=short_slug,
                            structure=Product.ProductTypeChoice.child,
                        )
                    )
                    .select_related(
                        "stockrecord", "brand", "brand__image", "product_class", "parent__product_class"
                    )
                    .prefetch_related(
                        prefetch_recommended_products,
                        prefetch_images,
                        prefetch_attributes,
                        prefetch_properties,
                        'comments'
                    ).annotate(comment_count=Count('comments'))
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
                    'comments'
                ).annotate(comment_count=Count('comments'))
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
    ).order_by('-created_at')

    def list(self, request, product_id=None):
        if not product_id:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
        # Filter the queryset using the provided product_id
        queryset = super().get_queryset().filter(product_id=product_id)

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


class ProductVisitLoggedInView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, format=None):
        try:
            # Retrieve user and IP address
            user = request.user
            ip_address = request.META.get('REMOTE_ADDR', None)

            # Get visited URL from the POST data
            product_slug = request.data.get('product_slug', None)
            if not product_slug:
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
            add_product_visit_celery.apply_async(kwargs={
                'product_slug': product_slug,
                'ip_address': ip_address,
                'user_id': user.id,

            }, priority=1)
            return BaseResponse(status=status.HTTP_201_CREATED)
        except Exception as e:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST)


class ProductVisitAnonymousView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            # Retrieve IP address
            ip_address = request.META.get('REMOTE_ADDR', None)

            # Get visited URL from the POST data
            product_slug = request.data.get('product_slug', None)
            if not product_slug:
                return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
            add_product_visit_celery.apply_async(kwargs={
                'product_slug': product_slug,
                'ip_address': ip_address,

            }, priority=1)
            return BaseResponse(status=status.HTTP_201_CREATED)
        except Exception as e:
            return BaseResponse(status=status.HTTP_400_BAD_REQUEST)
