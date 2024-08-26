# Generated by Django 4.1.6 on 2024-07-26 06:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0080_paymentmethods_banks'),
    ]

    operations = [
        migrations.AddField(
            model_name='banks',
            name='supporting_currency',
            field=models.ManyToManyField(blank=True, null=True, to='account.fiatcurrency'),
        ),
    ]