# Generated by Django 5.0.1 on 2024-02-11 16:43

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0008_stockrecord_sku"),
    ]

    operations = [
        migrations.AddField(
            model_name="stockrecord",
            name="in_order_limit",
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]
