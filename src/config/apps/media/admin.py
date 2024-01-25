from django.contrib import admin
from django.utils.html import format_html

from .models import Media


@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "file",
        "resize_width",
        "resize_height",
    )
    search_fields = (
        "title",
        "created_at",
    )

    @staticmethod
    def file(obj):
        if obj.file:
            return format_html(
                f'<img src="{obj.file.url}" width="100px" height="100px" style="border-radius:5px;" />'
            )
        else:
            return ""
