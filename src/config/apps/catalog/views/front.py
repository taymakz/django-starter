from django.db.models import Subquery, OuterRef
from rest_framework.generics import ListAPIView
from rest_framework.permissions import AllowAny

from config.api.response import PaginationApiResponse
from config.apps.catalog.filters import ProductFilter
from config.apps.catalog.models import Product, ProductImage
from config.apps.catalog.serializers.front import ProductCardSerializer


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
