# Generated by Django 4.1.6 on 2024-08-12 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0093_joint_account_kyc_verification'),
    ]

    operations = [
        migrations.AddField(
            model_name='jointaccount',
            name='account_number',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
    ]