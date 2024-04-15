# Generated by Django 4.1.6 on 2024-03-30 21:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0058_card_type_cards'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='cards',
            options={'verbose_name_plural': 'Cards'},
        ),
        migrations.AlterField(
            model_name='cards',
            name='card_holder_name',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='cards',
            name='card_number',
            field=models.CharField(blank=True, max_length=16, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='cards',
            name='cvv',
            field=models.CharField(blank=True, max_length=4, null=True),
        ),
        migrations.AlterField(
            model_name='cards',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]