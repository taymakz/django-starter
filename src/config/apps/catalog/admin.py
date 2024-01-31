from django.contrib import admin
from django.db.models import Count
from django.utils.html import format_html
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from config.apps.catalog.models import (
    Category,
    Brand,
    ProductAttribute,
    ProductClass,
    ProductRecommendation,
    Product,
    ProductAttributeValue,
    ProductImage,
    OptionGroupValue,
    OptionGroup,
)
from config.apps.inventory.models import StockRecord


@admin.register(Category)
class CategoryAdmin(TreeNodeModelAdmin):
    raw_id_fields = ["tn_parent"]

    # set the changelist display mode: 'accordion', 'breadcrumbs' or 'indentation' (default)
    # when changelist results are filtered by a querystring,
    # 'breadcrumbs' mode will be used (to preserve data display integrity)
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION
    list_display = ["__str__", "title_ir", "title_en", "slug", "file"]
    list_editable = ["title_ir", "title_en", "slug"]
    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm
    exclude = ("tn_priority",)

    @staticmethod
    def file(obj: Category):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.file.url}" width="100px" height="100px" style="border-radius:5px;" />'
            )
        else:
            return ""


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ["__str__", "title_ir", "title_en", "order", "image", "file"]
    list_editable = ["title_ir", "title_en", "order", "image"]

    @staticmethod
    def file(obj: Category):
        if obj.image:
            return format_html(
                f'<img src="{obj.image.file.url}" width="100px" height="50px" style="border-radius:5px;color:white" />'
            )
        else:
            return ""


@admin.register(OptionGroup)
class OptionGroupAdmin(admin.ModelAdmin):
    pass


@admin.register(OptionGroupValue)
class OptionGroupValueAdmin(admin.ModelAdmin):
    pass


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1


class AttributeCountFilter(admin.SimpleListFilter):
    title = "Attribute Count"
    parameter_name = "attr_count"

    def lookups(self, request, model_admin):
        return [
            ("more_5", "More Than 5"),
            ("lower_5", "lower Than 5"),
        ]

    def queryset(self, request, queryset):
        if self.value() == "more_5":
            return queryset.annotate(attr_count=Count("attributes")).filter(
                attr_count__gt=5
            )
        if self.value() == "lower_5":
            return queryset.annotate(attr_count=Count("attributes")).filter(
                attr_count__lte=5
            )


@admin.register(ProductClass)
class ProductClassAdmin(admin.ModelAdmin):
    list_display = (
        "title_ir",
        "title_en",
        "slug",
        "require_shipping",
        "track_stock",
        "attribute_count",
    )
    list_filter = ("require_shipping", "track_stock", AttributeCountFilter)
    inlines = [ProductAttributeInline]
    actions = ["enable_track_stock"]
    prepopulated_fields = {"slug": ("title_en",)}

    def attribute_count(self, obj):
        return obj.attributes.count()

    def enable_track_stock(self, request, queryset):
        queryset.update(track_stock=True)


class ProductRecommendationInline(admin.StackedInline):
    model = ProductRecommendation
    extra = 0
    fk_name = "primary"


class ProductAttributeValueInline(admin.TabularInline):
    model = ProductAttributeValue
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class ProductStockRecordInline(admin.TabularInline):
    model = StockRecord
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [
        ProductAttributeValueInline,
        ProductImageInline,
        ProductRecommendationInline,
        ProductStockRecordInline,
    ]
    raw_id_fields = ["parent"]
    prepopulated_fields = {"slug": ("title_en",)}
    list_display = ["upc", "title_en", "title_ir", "slug", "order"]
    list_editable = ["title_ir", "title_en", "slug", "order"]
    search_fields = ("upc", "title_en", "slug")
