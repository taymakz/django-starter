from django.db import models
from treenode.models import TreeNodeModel

from config.libs.db.models import BaseModel


class Category(TreeNodeModel, BaseModel):
    image = models.ForeignKey('media.Media', on_delete=models.SET_NULL, blank=True, null=True,
                              related_name='categories')
    title_ir = models.CharField(max_length=155)
    title_en = models.CharField(max_length=155, db_index=True)

    description = models.CharField(max_length=2048, null=True, blank=True)
    is_public = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, allow_unicode=True)
    order = models.IntegerField(default=1, blank=True, null=True)

    treenode_display_field = "title_en"

    def __str__(self):
        return self.title_en

    class Meta(TreeNodeModel.Meta):
        db_table = "categories"
        ordering = ("order",)
        verbose_name = "Category"
        verbose_name_plural = "Categories"


class Brand(BaseModel):
    image = models.ForeignKey('media.Media', on_delete=models.SET_NULL, blank=True, null=True, related_name='brands')
    title_ir = models.CharField(max_length=55)
    title_en = models.CharField(max_length=55)

    order = models.IntegerField(default=1, blank=True, null=True)

    class Meta:
        db_table = "brands"
        ordering = ("order",)
        verbose_name = "Brand"
        verbose_name_plural = "Brands"

    def __str__(self):
        return f"{self.title_ir} - {self.title_en}"
