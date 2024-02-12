# Generated by Django 5.0.1 on 2024-01-30 10:43

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("catalog", "0010_alter_product_options_alter_brand_order_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="product",
            name="tn_ancestors_count",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_ancestors_pks",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_children_count",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_children_pks",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_depth",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_descendants_count",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_descendants_pks",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_index",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_level",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_order",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_parent",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_priority",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_siblings_count",
        ),
        migrations.RemoveField(
            model_name="product",
            name="tn_siblings_pks",
        ),
        migrations.AddField(
            model_name="product",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="children",
                to="catalog.product",
            ),
        ),
    ]