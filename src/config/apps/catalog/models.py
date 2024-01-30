from django.core.cache import cache
from django.db import models
from treenode.models import TreeNodeModel

from config.libs.db.fields import UpperCaseCharField
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
    order = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    treenode_display_field = "title_en"

    def save(self, *args, **kwargs):
        # Call the parent class's save method
        super().save(*args, **kwargs)
        # self.re_new_cache()

    def __str__(self):
        if self.tn_parent:
            return f"{self.tn_parent.title_en} - {self.title_en}"
        return self.title_en

    class Meta(TreeNodeModel.Meta):
        db_table = "categories"
        ordering = ("order",)
        verbose_name = "Category"
        verbose_name_plural = "Categories"

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

    # @staticmethod
    # def build_tree(categories, parent_id=None):
    #     tree = []
    #     for category in categories:
    #         if category.tn_parent_id == parent_id:
    #             node = CategorySerializerTest(category).data
    #             node["children"] = self.build_tree(categories, parent_id=category.id)
    #             tree.append(node)
    #     return tree


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

    order = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Call the parent class's save method
        super().save(*args, **kwargs)
        # self.re_new_cache()

    class Meta:
        db_table = "brands"
        ordering = ("order",)
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

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
        )  # No expiration for brands

    def __str__(self):
        return f"{self.title_ir} - {self.title_en}"


class OptionGroup(models.Model):
    title = models.CharField(max_length=255, db_index=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Option Group"
        verbose_name_plural = "Option Groups"


class OptionGroupValue(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    group = models.ForeignKey(OptionGroup, on_delete=models.CASCADE)

    color_code = models.CharField(max_length=10, null=True, blank=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Option Group Value"
        verbose_name_plural = "Option Group Values"


class ProductClass(models.Model):
    title_ir = models.CharField(max_length=255, db_index=True)
    title_en = models.CharField(max_length=255, db_index=True)
    description = models.CharField(max_length=2048, null=True, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True, db_index=True)

    track_stock = models.BooleanField(default=True)
    require_shipping = models.BooleanField(default=True)

    @property
    def has_attribute(self):
        return self.attributes.exists()

    def __str__(self):
        return self.title_ir

    class Meta:
        verbose_name = "Product Class"
        verbose_name_plural = "Product Classes"


class ProductAttribute(models.Model):
    class AttributeTypeChoice(models.TextChoices):
        text = 'text'
        integer = 'integer'
        float = 'float'
        option = 'option'
        multi_option = 'multi_option'

    product_class = models.ForeignKey(ProductClass, on_delete=models.CASCADE, null=True, related_name='attributes')
    title = models.CharField(max_length=64)
    type = models.CharField(max_length=16, choices=AttributeTypeChoice.choices, default=AttributeTypeChoice.text)
    option_group = models.ForeignKey(OptionGroup, on_delete=models.PROTECT, null=True, blank=True)
    required = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Product Attribute"
        verbose_name_plural = "Product Attributes"


class Product(BaseModel):
    class ProductTypeChoice(models.TextChoices):
        standalone = 'standalone'
        parent = 'parent'
        child = 'child'

    structure = models.CharField(max_length=16, choices=ProductTypeChoice.choices, default=ProductTypeChoice.standalone)
    parent = models.ForeignKey("self", related_name="children", on_delete=models.CASCADE, null=True, blank=True)
    order = models.PositiveSmallIntegerField(default=0, blank=True, null=True)

    title_ir = models.CharField(max_length=255, null=True, blank=True)
    title_en = models.CharField(max_length=255, null=True, blank=True)
    slug = models.SlugField(unique=True, allow_unicode=True, null=True, blank=True)
    upc = UpperCaseCharField(max_length=24, unique=True, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    meta_title = models.CharField(max_length=128, null=True, blank=True)
    meta_description = models.TextField(null=True, blank=True)

    product_class = models.ForeignKey(ProductClass, on_delete=models.PROTECT, null=True, blank=True,
                                      related_name='products')
    attributes = models.ManyToManyField(ProductAttribute, through='ProductAttributeValue')
    recommended_products = models.ManyToManyField('catalog.Product', through='ProductRecommendation', blank=True)
    categories = models.ManyToManyField(Category, related_name='products', blank=True)
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')

    def __str__(self):
        return f"{self.title_ir}"

    @property
    def main_image(self):
        if self.images.exists():
            return self.images.first()
        else:
            return None

    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"
        ordering = ("order",)


class ProductAttributeValue(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    attribute = models.ForeignKey(ProductAttribute, on_delete=models.CASCADE)

    value_text = models.TextField(null=True, blank=True)
    value_integer = models.IntegerField(null=True, blank=True)
    value_float = models.FloatField(null=True, blank=True)
    value_option = models.ForeignKey(OptionGroupValue, on_delete=models.PROTECT, null=True, blank=True)
    value_multi_option = models.ManyToManyField(OptionGroupValue, blank=True,
                                                related_name='multi_valued_attribute_value')

    class Meta:
        verbose_name = "Attribute Value"
        verbose_name_plural = "Attribute Values"
        unique_together = ('product', 'attribute')


class ProductRecommendation(models.Model):
    primary = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='primary_recommendation')
    recommendation = models.ForeignKey(Product, on_delete=models.CASCADE)
    rank = models.PositiveSmallIntegerField(default=0)

    class Meta:
        unique_together = ('primary', 'recommendation')
        ordering = ('primary', '-rank')


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ForeignKey('media.Media', on_delete=models.PROTECT)

    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ('order',)

    def delete(self, *args, **kwargs):
        super().delete(*args, **kwargs)

        for index, image in enumerate(self.product.images.all()):
            image.order = index
            image.save()


class ProductProperty(models.Model):
    name = models.CharField(max_length=40)

    def __str__(self):
        return self.name


class ProductPropertyValue(models.Model):
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="properties"
    )
    property = models.ForeignKey(ProductProperty, on_delete=models.CASCADE)
    value = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.property.name} : {self.value}"
