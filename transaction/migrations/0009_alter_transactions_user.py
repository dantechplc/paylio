# Generated by Django 4.1.6 on 2023-10-05 02:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0029_remove_cryptoportfolio_coin_and_more'),
        ('transaction', '0008_rename_card_name_transactions_card_holder'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactions',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.client'),
        ),
    ]
