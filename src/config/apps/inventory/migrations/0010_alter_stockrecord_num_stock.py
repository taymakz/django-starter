# Generated by Django 5.0.1 on 2024-02-16 16:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("inventory", "0009_stockrecord_in_order_limit"),
    ]

    operations = [
        migrations.AlterField(
            model_name="stockrecord",
            name="num_stock",
            field=models.IntegerField(default=0),
        ),
    ]