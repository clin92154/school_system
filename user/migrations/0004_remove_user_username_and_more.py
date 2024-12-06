# Generated by Django 5.1.3 on 2024-11-26 06:50

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0003_remove_leaveapplication_period_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="username",
        ),
        migrations.AlterField(
            model_name="leaveapplication",
            name="apply_date",
            field=models.DateField(default=django.utils.timezone.now),
        ),
    ]