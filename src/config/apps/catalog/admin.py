from django.contrib import admin
from django.utils.html import format_html
from treenode.admin import TreeNodeModelAdmin
from treenode.forms import TreeNodeForm

from config.apps.catalog.models import Category, Brand


@admin.register(Category)
class CategoryAdmin(TreeNodeModelAdmin):
    # set the changelist display mode: 'accordion', 'breadcrumbs' or 'indentation' (default)
    # when changelist results are filtered by a querystring,
    # 'breadcrumbs' mode will be used (to preserve data display integrity)
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_ACCORDION
    treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_BREADCRUMBS
    # treenode_display_mode = TreeNodeModelAdmin.TREENODE_DISPLAY_MODE_INDENTATION
    prepopulated_fields = {'slug': ('title_en',)}
    list_display = ['__str__', 'title_ir', 'title_en', 'slug', 'file']
    list_editable = ['title_ir', 'title_en', 'slug']
    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm

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
    list_display = ['__str__', 'title_ir', 'title_en', 'order', 'image']
    list_editable = ['title_ir', 'title_en', 'order', 'image']
