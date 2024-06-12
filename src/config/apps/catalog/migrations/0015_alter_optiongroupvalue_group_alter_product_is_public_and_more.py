# Generated by Django 5.0.1 on 2024-02-03 14:16

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0014_alter_product_categories_alter_product_is_public_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="optiongroupvalue",
            name="group",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="values",
                to="catalog.optiongroup",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="is_public",
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name="product",
            name="structure",
            field=models.CharField(
                choices=[
                    ("standalone", "Standalone"),
                    ("parent", "Parent"),
                    ("child", "Child"),
                ],
                default="standalone",
                max_length=16,
            ),
        ),
    ]