# Generated by Django 4.1.6 on 2024-06-19 22:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0076_paymentmethods_supporting_currency'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='paymentmethods',
            name='supporting_currency',
        ),
        migrations.AddField(
            model_name='paymentmethods',
            name='supporting_currency',
            field=models.ManyToManyField(blank=True, null=True, to='account.fiatcurrency'),
        ),
    ]
