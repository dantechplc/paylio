# Generated by Django 4.1.6 on 2024-05-20 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0021_alter_transactions_transaction_type'),
    ]

    operations = [
        migrations.AlterField(
            model_name='transactions',
            name='date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
