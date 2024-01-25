from django.contrib import admin
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

    # use TreeNodeForm to automatically exclude invalid parent choices
    form = TreeNodeForm


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    pass
