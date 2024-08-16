# Generated by Django 4.1.6 on 2024-08-11 23:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0092_alter_jointaccount_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='joint_account_kyc',
            name='verification',
            field=models.CharField(blank=True, choices=[('Unverified', 'Unverified'), ('Under Review', 'Under Review'), ('Verified', 'Verified')], default='Unverified', max_length=200),
        ),
    ]
