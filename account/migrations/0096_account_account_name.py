# Generated by Django 4.1.6 on 2024-08-16 13:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0095_account_joint_account_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='account',
            name='account_name',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
