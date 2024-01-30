from django.contrib import admin
from django.utils.html import format_html

from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "title",
        "url",
        "order",
        "is_public",
        "is_showing",
        "image",
    )
    list_editable = ("title", "url", "order", "is_public")

    @staticmethod
    def image(obj):
        if obj.image.file:
            return format_html(
                f'<img src="{obj.image.file.url}" width="100px" height="100px" style="border-radius:5px;" />'
            )
        else:
            return ""

    @staticmethod
    def is_showing(obj: Banner) -> bool:
        return (obj.is_public and not obj.is_deleted) and (
                (obj.start_at and obj.expire_at) and (obj.start_at <= obj.expire_at)
        )
