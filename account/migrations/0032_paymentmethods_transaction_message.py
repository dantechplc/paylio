# Generated by Django 4.1.6 on 2023-10-05 10:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0031_paymentmethods_transaction_fee_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethods',
            name='transaction_message',
            field=models.TextField(blank=True, null=True),
        ),
    ]
