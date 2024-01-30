# Generated by Django 5.0.1 on 2024-01-26 15:05

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("media", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Banner",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_deleted", models.BooleanField(default=False)),
                (
                    "deleted_at",
                    models.DateTimeField(blank=True, editable=False, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("modified_at", models.DateTimeField(auto_now=True)),
                (
                    "position",
                    models.CharField(
                        choices=[
                            ("HOME_SLIDER_BANNER", "اسلایدر صفحه اصلی"),
                            ("HOME_SIDE_BANNER", "بنر کنار اسلایدر صفحه اصلی"),
                        ],
                        max_length=40,
                    ),
                ),
                ("title", models.CharField(max_length=155)),
                ("order", models.IntegerField(blank=True, default=1, null=True)),
                (
                    "description",
                    models.CharField(blank=True, max_length=155, null=True),
                ),
                ("url", models.URLField(blank=True, null=True)),
                ("is_external", models.BooleanField(default=False)),
                ("is_public", models.BooleanField(default=True)),
                (
                    "image",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="banners",
                        to="media.media",
                    ),
                ),
            ],
            options={
                "verbose_name": "Banner",
                "verbose_name_plural": "Banners",
                "db_table": "banners",
                "ordering": ("order",),
            },
        ),
    ]
