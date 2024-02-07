# Generated by Django 5.0.1 on 2024-02-07 10:17

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0023_remove_product_sku_product_short_slug"),
    ]

    operations = [
        migrations.AlterField(
            model_name="productattributevalue",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attribute_values",
                to="catalog.product",
            ),
        ),
    ]
