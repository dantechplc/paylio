# Generated by Django 4.1.6 on 2024-03-27 01:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0053_alter_authorizationtoken_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='authorizationtoken',
            name='token',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]
