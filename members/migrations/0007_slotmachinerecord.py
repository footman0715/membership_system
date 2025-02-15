# Generated by Django 5.1.6 on 2025-02-15 13:15

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0006_consumptionrecord_expiry_date'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='SlotMachineRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('bet', models.IntegerField(help_text='下注積分')),
                ('grid_result', models.TextField(help_text='3x3 拉霸結果，如：🍒 🍋 🍒 / 🍋 🍋 🍋 / 🔔 🍒 7')),
                ('win_points', models.IntegerField(default=0, help_text='贏得積分(含0)')),
                ('played_at', models.DateTimeField(default=django.utils.timezone.now, help_text='遊玩時間')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='slot_records', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
