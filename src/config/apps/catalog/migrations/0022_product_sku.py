# Generated by Django 5.0.1 on 2024-02-07 08:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0021_remove_productproperty_product_class_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="product",
            name="sku",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
    ]