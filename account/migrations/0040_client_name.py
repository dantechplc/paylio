# Generated by Django 4.1.6 on 2023-10-15 11:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0039_paymentmethods_withdrawal_transaction_message'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='name',
            field=models.CharField(blank=True, max_length=250, null=True),
        ),
    ]
