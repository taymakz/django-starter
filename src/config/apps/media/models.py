import hashlib
from datetime import datetime

from PIL import Image
from django.core.files.storage import default_storage
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.utils.crypto import get_random_string
from imagekit.models import ProcessedImageField

from config.apps.media.exceptions import DuplicateImageException
from config.libs.db.models import BaseModel


def upload_to(instance, filename):
    current_datetime = datetime.now()
    year = current_datetime.strftime("%Y")
    month = current_datetime.strftime("%m")
    day = current_datetime.strftime("%d")
    extension = filename.split(".")[-1].lower()
    random_name = get_random_string(30)

    filename = f"images/{year}/{month}/{day}/{random_name}.{extension}"
    return filename


# Create your models here.
class Media(BaseModel):
    file = ProcessedImageField(
        upload_to=upload_to,
        format="WEBP",
        options={"quality": 95},
        width_field="width",
        height_field="height"
    )
    title = models.CharField(max_length=128, null=True, blank=True)

    resize_width = models.PositiveIntegerField(default=0)
    resize_height = models.PositiveIntegerField(default=0)

    width = models.IntegerField(editable=False)
    height = models.IntegerField(editable=False)

    file_hash = models.CharField(max_length=40, db_index=True, editable=False)
    file_size = models.PositiveIntegerField(null=True, editable=False)

    focal_point_x = models.PositiveIntegerField(null=True, blank=True)
    focal_point_y = models.PositiveIntegerField(null=True, blank=True)
    focal_point_width = models.PositiveIntegerField(null=True, blank=True)
    focal_point_height = models.PositiveIntegerField(null=True, blank=True)

    def get_file_name(self):
        return self.file.name

    class Meta:
        db_table = "medias"
        ordering = ("-created_at", "-modified_at")

    def __str__(self):
        return f"{self.title}"

    def save(self, *args, **kwargs):
        # TODO: fix
        if not self.file.file.closed:
            self.file_size = self.file.size

            hasher = hashlib.sha1()
            for chunk in self.file.file.chunks():
                hasher.update(chunk)

            self.file_hash = hasher.hexdigest()

        super().save(*args, **kwargs)


@receiver(post_save, sender=Media)
def create_signal(sender, instance: Media, **kwargs):
    # check_duplicate_hash
    existed = Media.objects.filter(file_hash=instance.file_hash).exclude(pk=instance.pk).exists()
    if existed:
        raise DuplicateImageException("Duplicate")

    # resize_banner_image
    if kwargs.get("raw"):
        # Fixtures are being loaded, so skip resizing
        return

    try:
        old_object: Media = sender.objects.get(pk=instance.pk)
        new_image = instance.file
        old_image = old_object.file

        new_width = instance.width
        old_width = old_object.width

        new_height = instance.height
        old_height = old_object.height

        if (
                new_image != old_image
                or (new_width != old_width)
                or (new_height != old_height)
        ):
            if instance.file and (instance.resize_width and instance.resize_height):
                # Get resize dimensions
                width, height = instance.resize_width, instance.resize_height

                # Open the image using storage API
                with default_storage.open(instance.file.name, "rb") as file:
                    image = Image.open(file)

                    # Resize and save the image
                    resized_image = image.resize((width, height))

                    with default_storage.open(
                            instance.file.name, "wb"
                    ) as resized_file:
                        resized_image.save(resized_file)
    except sender.DoesNotExist:
        if instance.file and (instance.resize_width and instance.resize_height):
            # Get resize dimensions
            width, height = instance.resize_width, instance.resize_height

            # Open the image using storage API
            with default_storage.open(instance.file.name, "rb") as file:
                image = Image.open(file)

                # Resize and save the image
                resized_image = image.resize((width, height))

                with default_storage.open(instance.file.name, "wb") as resized_file:
                    resized_image.save(resized_file)


@receiver(pre_save, sender=Media)
def delete_old_image(sender, instance: Media, **kwargs):
    if kwargs.get("raw"):
        # Fixtures are being loaded, so skip deleting old image
        return
    if not instance.pk:
        return

    try:
        old_object: Media = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    new_image = instance.file
    old_image = old_object.file

    if new_image != old_image:
        # Delete the old image from storage
        old_object.file.delete(save=False)
