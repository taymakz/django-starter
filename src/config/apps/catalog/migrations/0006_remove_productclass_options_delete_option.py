# Generated by Django 5.0.1 on 2024-01-29 16:40

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0005_product_brand_alter_product_categories"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="productclass",
            name="options",
        ),
        migrations.DeleteModel(
            name="Option",
        ),
    ]
