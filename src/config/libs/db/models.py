from django.db import models
from django.db.models import QuerySet
from django.utils import timezone


class BaseModelQuerySet(QuerySet):
    def delete(self):
        return self.update(is_deleted=True, deleted_at=timezone.now())


class BaseModelManager(models.Manager):
    def get_queryset(self):
        return BaseModelQuerySet(self.model, self._db).filter(is_deleted=False)


class BaseModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    modified_at = models.DateTimeField(auto_now=True, editable=False)

    objects = BaseModelManager()

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save()
