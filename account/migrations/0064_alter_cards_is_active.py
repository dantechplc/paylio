# Generated by Django 4.1.6 on 2024-04-01 18:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0063_alter_cards_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cards',
            name='is_active',
            field=models.BooleanField(default=False, null=True),
        ),
    ]
