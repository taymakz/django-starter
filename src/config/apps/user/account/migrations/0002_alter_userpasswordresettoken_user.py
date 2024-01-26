# Generated by Django 5.0.1 on 2024-01-25 17:36

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("account", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="userpasswordresettoken",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="reset_password_tokens",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]