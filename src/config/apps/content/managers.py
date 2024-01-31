from django.db import models
from django.db.models import Q
from django.utils.timezone import now


class BannerManager(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(
                Q(start_at__isnull=True) | Q(start_at__lte=now()),
                Q(expire_at__isnull=True) | Q(expire_at__gte=now()),
                is_public=True,
            )
        )
