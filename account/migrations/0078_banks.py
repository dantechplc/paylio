# Generated by Django 4.1.6 on 2024-07-13 18:30

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0077_remove_paymentmethods_supporting_currency_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Banks',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='banks')),
            ],
        ),
    ]