# Generated by Django 5.1.3 on 2024-11-24 08:33

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0002_alter_period_begin_time_alter_period_end_time"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="leaveapplication",
            name="period",
        ),
        migrations.AddField(
            model_name="leaveapplication",
            name="period",
            field=models.ManyToManyField(to="user.period"),
        ),
    ]