# Generated by Django 5.0.1 on 2024-01-26 15:07

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("content", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="banner",
            name="expire_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="banner",
            name="start_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
