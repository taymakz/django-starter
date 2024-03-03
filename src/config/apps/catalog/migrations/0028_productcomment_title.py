# Generated by Django 5.0.1 on 2024-03-03 17:35

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalog", "0027_productcomment"),
    ]

    operations = [
        migrations.AddField(
            model_name="productcomment",
            name="title",
            field=models.CharField(default=django.utils.timezone.now, max_length=65),
            preserve_default=False,
        ),
    ]
