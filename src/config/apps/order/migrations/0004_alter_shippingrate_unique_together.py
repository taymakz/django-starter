# Generated by Django 5.0.1 on 2024-02-14 15:15

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0003_alter_shippingrate_unique_together"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="shippingrate",
            unique_together={("service", "area", "all_area")},
        ),
    ]