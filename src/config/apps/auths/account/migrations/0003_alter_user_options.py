# Generated by Django 5.0.1 on 2024-01-19 21:13

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0002_recycleuser_user_created_at_user_created_by_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="user",
            options={
                "default_manager_name": "objects",
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
    ]
