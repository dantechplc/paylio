# Generated by Django 4.1.6 on 2024-06-17 12:30

from django.db import migrations
import django_countries.fields


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0072_card_type_card_logo'),
    ]

    operations = [
        migrations.AddField(
            model_name='paymentmethods',
            name='country',
            field=django_countries.fields.CountryField(blank=True, max_length=2, null=True),
        ),
    ]