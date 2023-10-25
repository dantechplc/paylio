# Generated by Django 4.1.6 on 2023-10-05 01:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0006_transactions_timestamp'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='transactions',
            name='timestamp',
        ),
        migrations.AddField(
            model_name='transactions',
            name='transaction_type',
            field=models.CharField(blank=True, choices=[('DEPOSIT', 'Deposit'), ('WITHDRAWAL', 'Withdrawal'), ('TRANSFER', 'Transfer')], max_length=200),
        ),
    ]
