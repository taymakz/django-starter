# Generated by Django 5.0.1 on 2024-03-14 07:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "order",
            "0009_rename_receiver_fullname_orderaddress_receiver_family_and_more",
        ),
    ]

    operations = [
        migrations.AddField(
            model_name="orderitem",
            name="final_buy_price",
            field=models.PositiveBigIntegerField(blank=True, editable=False, null=True),
        ),
    ]