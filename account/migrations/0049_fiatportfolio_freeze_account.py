# Generated by Django 4.1.6 on 2023-10-28 12:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0048_remove_account_fiat_main_balance_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiatportfolio',
            name='freeze_account',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
