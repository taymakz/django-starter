from django.core.cache import cache
from django.db import models

from config.apps.content.enums import BannerPosition
from config.apps.content.managers import BannerManager
from config.libs.db.models import BaseModel

BANNER_POSITION_CHOICES = [(data.name, data.value) for data in BannerPosition]


class Banner(BaseModel):
    image = models.ForeignKey(
        "media.Media",
        on_delete=models.PROTECT,
        blank=True,
        null=True,
        related_name="banners",
    )
    position = models.CharField(choices=BANNER_POSITION_CHOICES, max_length=40)
    title = models.CharField(max_length=155)
    order = models.PositiveSmallIntegerField(default=0, blank=True, null=True)
    description = models.CharField(max_length=155, null=True, blank=True)

    url = models.URLField(blank=True, null=True)
    is_external = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    start_at = models.DateTimeField(blank=True, null=True)
    expire_at = models.DateTimeField(blank=True, null=True)
    objects = BannerManager()

    def __str__(self):
        return f"{self.title} - {self.get_position_display()} {self.image.resize_width}x{self.image.resize_height}"

    class Meta:
        db_table = "banners"
        ordering = ("-order",)
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def save(self, *args, **kwargs):
        # Call the parent class's save method
        super().save(*args, **kwargs)
        self.re_new_cache()

    @staticmethod
    def re_new_cache():
        # If something changes, renew the cache for banners
        cache_key = "cached_banners"
        cache.delete(cache_key)

        # Recompute the data and set it in cache
        banners = Banner.objects.all().select_related("image")

        from config.apps.content.serializers.front import BannerSerializer

        response_data = {
            "banners": BannerSerializer(banners, many=True).data,
        }

        cache.set(
            cache_key, response_data["banners"], timeout=None
        )  # No expiration for banners
