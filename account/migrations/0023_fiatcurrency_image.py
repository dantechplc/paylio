# Generated by Django 4.1.6 on 2023-09-20 23:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0022_alter_account_account_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='fiatcurrency',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='fiat_images'),
        ),
    ]
