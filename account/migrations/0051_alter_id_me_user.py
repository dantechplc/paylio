# Generated by Django 4.1.6 on 2024-03-24 23:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0050_id_me'),
    ]

    operations = [
        migrations.AlterField(
            model_name='id_me',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.client'),
        ),
    ]