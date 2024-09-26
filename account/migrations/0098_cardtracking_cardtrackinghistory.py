# Generated by Django 4.1.6 on 2024-09-25 01:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0097_investment_investment_profile'),
    ]

    operations = [
        migrations.CreateModel(
            name='CardTracking',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('track_no', models.CharField(blank=True, max_length=12, unique=True)),
                ('delivery_date', models.DateField(blank=True, null=True)),
                ('status', models.CharField(choices=[('order processed', 'Order Processed'), ('order shipped', 'Order Shipped'), ('order en route', 'Order En Route'), ('order delivered', 'Order Delivered')], default='order processed', max_length=255)),
                ('client', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='card_tracking', to='account.client')),
            ],
        ),
        migrations.CreateModel(
            name='CardTrackingHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('old_status', models.CharField(choices=[('order processed', 'Order Processed'), ('order shipped', 'Order Shipped'), ('order en route', 'Order En Route'), ('order delivered', 'Order Delivered')], max_length=255)),
                ('new_status', models.CharField(choices=[('order processed', 'Order Processed'), ('order shipped', 'Order Shipped'), ('order en route', 'Order En Route'), ('order delivered', 'Order Delivered')], max_length=255)),
                ('changed_at', models.DateTimeField(auto_now_add=True)),
                ('card_tracking', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='history', to='account.cardtracking')),
            ],
        ),
    ]