# Generated by Django 5.0.1 on 2024-02-13 19:36

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("address", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="useraddresses",
            name="receiver_building_number",
            field=models.CharField(default="", max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="useraddresses",
            name="receiver_unit",
            field=models.CharField(default="w", max_length=10),
            preserve_default=False,
        ),
    ]