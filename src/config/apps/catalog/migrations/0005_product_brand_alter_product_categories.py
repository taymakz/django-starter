# Generated by Django 5.0.1 on 2024-01-29 11:20

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0004_optiongroupvalue_color_code"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="brand",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="products",
                to="catalog.brand",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="categories",
            field=models.ManyToManyField(
                related_name="products", to="catalog.category"
            ),
        ),
    ]