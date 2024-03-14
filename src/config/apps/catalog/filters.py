from django.db.models import Q, Case, When, IntegerField, F, Sum
from django.db.models.functions import Now
from django.utils.timezone import now
from django_filters import rest_framework as filters

from config.apps.catalog.models import Product
from config.apps.order.models import Order


class ProductFilter(filters.FilterSet):
    search = filters.CharFilter(method="filter_search", label="Search")
    categorySlug = filters.CharFilter(method="filter_category")
    brand = filters.CharFilter(method="filter_brand")
    color = filters.CharFilter(method="filter_color")
    size = filters.CharFilter(method="filter_size")
    price = filters.CharFilter(method="filter_price")
    gender = filters.CharFilter(method="filter_gender")
    sort = filters.NumberFilter(method="filter_sort")
    available = filters.BooleanFilter(
        field_name="stockrecord__num_stock", method="filter_availability"
    )
    special = filters.BooleanFilter(method="filter_special")

    class Meta:
        model = Product
        fields = ["search", "categories", "brand", "color", "size", "gender", "price"]

    def filter_search(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(title_ir__icontains=value)
                | Q(title_en__icontains=value)
                | Q(slug__icontains=value)
                | Q(upc__icontains=value)
            )
        return queryset

    def filter_category(self, queryset, name, value):
        if value:
            queryset = queryset.filter(
                Q(categories__slug__iexact=value)
                | Q(parent__categories__slug__iexact=value)
                | Q(children__categories__slug__iexact=value),
                structure__in=[
                    Product.ProductTypeChoice.standalone,
                    Product.ProductTypeChoice.parent,
                ],
            ).distinct()
        return queryset

    def filter_price(self, queryset, name, value):
        if value:
            # Extract the min and max values from the range
            min_price, max_price = [int(x) for x in value.split(",")]
            return queryset.annotate(
                final_price=Case(
                    When(
                        stockrecord__special_sale_price__isnull=False,
                        stockrecord__special_sale_price_start_at__lte=now(),
                        stockrecord__special_sale_price_end_at__gte=now(),
                        then=F("stockrecord__special_sale_price"),
                    ),
                    default=F("stockrecord__sale_price"),
                    output_field=IntegerField(),
                )
            ).filter(final_price__gte=min_price, final_price__lte=max_price)

        return queryset

    def filter_brand(self, queryset, name, value):
        brand_ids = [int(x) for x in value.split(",")]
        return queryset.filter(brand__id__in=brand_ids)

    def filter_color(self, queryset, name, value):
        color_ids = [int(x) for x in value.split(",")]

        return queryset.filter(
            Q(attribute_values__value_option_id__in=color_ids)
            | Q(parent__attribute_values__value_option_id__in=color_ids)
            | Q(children__attribute_values__value_option_id__in=color_ids),
            structure__in=[
                Product.ProductTypeChoice.standalone,
                Product.ProductTypeChoice.parent,
            ],
        ).distinct()

    def filter_gender(self, queryset, name, value):
        genders_ids = [int(x) for x in value.split(",")]
        return queryset.filter(categories__id__in=genders_ids)

    def filter_size(self, queryset, name, value):
        size_ids = [int(x) for x in value.split(",")]
        return queryset.filter(
            Q(attribute_values__value_option_id__in=size_ids)
            | Q(parent__attribute_values__value_option_id__in=size_ids)
            | Q(children__attribute_values__value_option_id__in=size_ids),
            structure__in=[
                Product.ProductTypeChoice.standalone,
                Product.ProductTypeChoice.parent,
            ],
        ).distinct()

    def filter_sort(self, queryset, name, value):
        if value == 1:  # Newest
            return queryset.order_by("-created_at")
        elif value == 2:  # Most Sale
            return queryset.annotate(
                total_sales=Sum(
                    Case(
                        When(
                            in_baskets__order__payment_status=Order.PaymentStatusChoice.PAID,
                            then=F('in_baskets__count')
                        ),
                        default=0,
                        output_field=IntegerField(),
                    )
                )
            ).order_by("-total_sales")
        elif value == 3:  # Expensive
            return queryset.annotate(
                price=Case(
                    When(
                        stockrecord__special_sale_price__isnull=False,
                        stockrecord__special_sale_price_start_at__lte=now(),
                        stockrecord__special_sale_price_end_at__gte=now(),
                        then=F("stockrecord__special_sale_price"),
                    ),
                    default=F("stockrecord__sale_price"),
                    output_field=IntegerField(),
                )
            ).order_by("-price")
        elif value == 4:  # Cheap
            return queryset.annotate(
                price=Case(
                    When(
                        stockrecord__special_sale_price__isnull=False,
                        stockrecord__special_sale_price_start_at__lte=now(),
                        stockrecord__special_sale_price_end_at__gte=now(),
                        then=F("stockrecord__special_sale_price"),
                    ),
                    default=F("stockrecord__sale_price"),
                    output_field=IntegerField(),
                )
            ).order_by("price")
        return queryset

    def filter_availability(self, queryset, name, value):
        if value:
            return queryset.filter(
                Q(stockrecord__num_stock__gt=0, product_class__track_stock=True)
                | Q(product_class__track_stock=False),
            )
        return queryset

    def filter_special(self, queryset, name, value):
        if value:
            now = Now()
            return queryset.filter(
                Q(stockrecord__special_sale_price_start_at__isnull=True)
                | Q(stockrecord__special_sale_price_start_at__lte=now),
                Q(stockrecord__special_sale_price_end_at__isnull=True)
                | Q(stockrecord__special_sale_price_end_at__gte=now),
                stockrecord__special_sale_price__isnull=False,
            )
        return queryset
