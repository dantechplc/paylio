# Generated by Django 4.1.6 on 2023-10-04 22:15

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0028_alter_paymentmethods_options_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='cryptoportfolio',
            name='coin',
        ),
        migrations.RemoveField(
            model_name='cryptoportfolio',
            name='user',
        ),
        migrations.RemoveField(
            model_name='account',
            name='crypto_main_balance',
        ),
        migrations.RemoveField(
            model_name='account',
            name='crypto_main_balance_currency',
        ),
        migrations.DeleteModel(
            name='CryptoCurrency',
        ),
        migrations.DeleteModel(
            name='CryptoPortfolio',
        ),
    ]
