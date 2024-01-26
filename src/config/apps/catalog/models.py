from django.core.cache import cache
from django.db import models
from treenode.models import TreeNodeModel

from config.libs.db.models import BaseModel


class Category(TreeNodeModel, BaseModel):
    image = models.ForeignKey(
        "media.Media",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="categories",
    )
    title_ir = models.CharField(max_length=155)
    title_en = models.CharField(max_length=155, db_index=True)

    description = models.CharField(max_length=2048, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    order = models.IntegerField(default=1, blank=True, null=True)

    treenode_display_field = "title_en"

    def save(self, *args, **kwargs):
        # Call the parent class's save method
        super().save(*args, **kwargs)
        self.re_new_cache()

    def __str__(self):
        return self.title_en

    class Meta(TreeNodeModel.Meta):
        db_table = "categories"
        ordering = ("order",)
        verbose_name = "Category"
        verbose_name_plural = "Categories"

    def get_image(self):
        if self.image:
            return self.image.file.name
        return ""

    @staticmethod
    def re_new_cache():
        # If something changes, renew the cache for categories
        cache_key = "cached_categories"
        cache.delete(cache_key)

        # Recompute the data and set it in cache
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

        from config.apps.catalog.serializers.front import CategorySerializer

        response_data = {
            "categories": CategorySerializer(categories, many=True).data,
        }

        cache.set(
            cache_key, response_data["categories"], timeout=None
        )  # No expiration for categories


class Brand(BaseModel):
    image = models.ForeignKey(
        "media.Media",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="brands",
    )
    title_ir = models.CharField(max_length=55)
    title_en = models.CharField(max_length=55)

    order = models.IntegerField(default=1, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Call the parent class's save method
        super().save(*args, **kwargs)
        self.re_new_cache()

    class Meta:
        db_table = "brands"
        ordering = ("order",)
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def get_image(self):
        if self.image:
            return self.image.file.name
        return ""

    @staticmethod
    def re_new_cache():
        # If something changes, renew the cache for brands
        cache_key = "cached_brands"
        cache.delete(cache_key)

        # Recompute the data and set it in cache
        brands = (
            Brand.objects.only("title_ir", "title_en", "image")
            .select_related("image")
            .all()
        )

        from config.apps.catalog.serializers.front import BrandSerializer

        response_data = {
            "brands": BrandSerializer(brands, many=True).data,
        }

        cache.set(
            cache_key, response_data["brands"], timeout=None
        )  # No expiration for categories

    def __str__(self):
        return f"{self.title_ir} - {self.title_en}"
