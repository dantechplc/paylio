# Generated by Django 4.1.6 on 2024-04-01 19:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0065_alter_cards_freeze'),
    ]

    operations = [
        migrations.AddField(
            model_name='cards',
            name='billing_address',
            field=models.TextField(blank=True, null=True),
        ),
    ]
