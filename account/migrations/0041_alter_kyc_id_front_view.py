# Generated by Django 4.1.6 on 2023-10-16 18:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0040_client_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='kyc',
            name='id_front_view',
            field=models.FileField(null=True, upload_to='kyc/%Y-%m-%d/'),
        ),
    ]
