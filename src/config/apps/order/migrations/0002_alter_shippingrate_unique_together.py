# Generated by Django 5.0.1 on 2024-02-14 15:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("order", "0001_initial"),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name="shippingrate",
            unique_together={("service", "area", "is_public")},
        ),
    ]