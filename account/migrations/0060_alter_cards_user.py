# Generated by Django 4.1.6 on 2024-03-30 21:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0059_alter_cards_options_alter_cards_card_holder_name_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='cards',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cards', to='account.client'),
        ),
    ]
