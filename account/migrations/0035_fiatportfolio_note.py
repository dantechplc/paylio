# Generated by Django 4.1.6 on 2023-10-12 15:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0034_alter_fiatportfolio_currency'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiatportfolio',
            name='note',
            field=models.CharField(blank=True, max_length=2200, null=True),
        ),
    ]
