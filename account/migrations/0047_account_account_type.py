# Generated by Django 4.1.6 on 2023-10-22 03:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0046_alter_exchangerate_exchange_fee_percentage'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='account_type',
            field=models.CharField(blank=True, choices=[('Individual Account', 'Individual Account'), ('Business Account', 'Business Account')], max_length=200, null=True),
        ),
    ]
