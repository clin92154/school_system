# Generated by Django 5.1.3 on 2024-12-04 04:46

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0006_user_semester_alter_leaveapplication_student"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="day_of_week",
            field=models.CharField(
                choices=[
                    ("Monday", "Monday"),
                    ("Tuesday", "Tuesday"),
                    ("Wednesday", "Wednesday"),
                    ("Thursday", "Thursday"),
                    ("Friday", "Friday"),
                    ("Saturday", "Saturday"),
                    ("Sunday", "Sunday"),
                ],
                default="Monday",
                max_length=10,
            ),
            preserve_default=False,
        ),
    ]
