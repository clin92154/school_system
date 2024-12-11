# Generated by Django 5.1.3 on 2024-12-11 09:03

import django.core.validators
import django.db.models.deletion
import django.utils.timezone
import user.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="LeaveType",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("type_name", models.CharField(max_length=10)),
            ],
        ),
        migrations.CreateModel(
            name="Period",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("period_number", models.PositiveIntegerField()),
                ("begin_time", models.TimeField(blank=True, null=True)),
                ("end_time", models.TimeField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Semester",
            fields=[
                (
                    "semester_id",
                    models.CharField(max_length=10, primary_key=True, serialize=False),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        help_text="請輸入年份，例如 2024",
                        validators=[django.core.validators.MinValueValidator(1900)],
                    ),
                ),
                (
                    "term",
                    models.CharField(
                        choices=[("1", "第一學期"), ("2", "第二學期")], max_length=10
                    ),
                ),
                ("begin_time", models.DateField(blank=True, null=True)),
                ("final_time", models.DateField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="User",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("password", models.CharField(max_length=128, verbose_name="password")),
                (
                    "last_login",
                    models.DateTimeField(
                        blank=True, null=True, verbose_name="last login"
                    ),
                ),
                (
                    "is_superuser",
                    models.BooleanField(
                        default=False,
                        help_text="Designates that this user has all permissions without explicitly assigning them.",
                        verbose_name="superuser status",
                    ),
                ),
                (
                    "first_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="first name"
                    ),
                ),
                (
                    "last_name",
                    models.CharField(
                        blank=True, max_length=150, verbose_name="last name"
                    ),
                ),
                (
                    "is_staff",
                    models.BooleanField(
                        default=False,
                        help_text="Designates whether the user can log into this admin site.",
                        verbose_name="staff status",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(
                        default=True,
                        help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.",
                        verbose_name="active",
                    ),
                ),
                (
                    "date_joined",
                    models.DateTimeField(
                        default=django.utils.timezone.now, verbose_name="date joined"
                    ),
                ),
                ("user_id", models.CharField(max_length=20, unique=True)),
                ("name", models.CharField(max_length=20)),
                ("birthday", models.DateField()),
                ("eng_name", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "role",
                    models.CharField(
                        choices=[
                            ("admin", "Admin"),
                            ("student", "Student"),
                            ("teacher", "Teacher"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "gender",
                    models.CharField(
                        choices=[("male", "男生"), ("female", "女生")], max_length=10
                    ),
                ),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "user",
                "verbose_name_plural": "users",
                "abstract": False,
            },
            managers=[
                ("objects", user.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name="Category",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=20)),
                (
                    "roles",
                    models.CharField(
                        blank=True,
                        choices=[("teachers", "Teachers"), ("students", "Students")],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("url", models.CharField(blank=True, max_length=100, null=True)),
                (
                    "parent_category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="subcategories",
                        to="user.category",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Class",
            fields=[
                (
                    "class_name",
                    models.CharField(
                        max_length=1,
                        validators=[
                            django.core.validators.RegexValidator(
                                message="Class name must be a single uppercase letter from A to Z.",
                                regex="^[A-Z]$",
                            )
                        ],
                    ),
                ),
                (
                    "class_id",
                    models.CharField(max_length=10, primary_key=True, serialize=False),
                ),
                (
                    "grade",
                    models.PositiveIntegerField(
                        choices=[
                            (1, "1 年級"),
                            (2, "2 年級"),
                            (3, "3 年級"),
                            (4, "4 年級"),
                            (5, "5 年級"),
                            (6, "6 年級"),
                        ]
                    ),
                ),
                (
                    "year",
                    models.PositiveIntegerField(
                        help_text="請輸入年份，例如 2024",
                        validators=[
                            django.core.validators.MinValueValidator(1900),
                            django.core.validators.MaxValueValidator(2024),
                        ],
                    ),
                ),
                (
                    "teacher_id",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="teacher_class",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="user",
            name="class_name",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="user.class",
            ),
        ),
        migrations.CreateModel(
            name="Course",
            fields=[
                (
                    "course_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("course_name", models.CharField(max_length=50)),
                ("course_description", models.TextField(blank=True, null=True)),
                (
                    "day_of_week",
                    models.CharField(
                        choices=[
                            ("Monday", "Monday"),
                            ("Tuesday", "Tuesday"),
                            ("Wednesday", "Wednesday"),
                            ("Thursday", "Thursday"),
                            ("Friday", "Friday"),
                            ("Saturday", "Saturday"),
                            ("Sunday", "Sunday"),
                        ],
                        max_length=10,
                    ),
                ),
                (
                    "class_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.class"
                    ),
                ),
                (
                    "teacher_id",
                    models.ForeignKey(
                        limit_choices_to={"role": "teacher"},
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                ("period", models.ManyToManyField(to="user.period")),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.semester"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Guardian",
            fields=[
                (
                    "guardian_id",
                    models.CharField(
                        editable=False,
                        max_length=50,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("name", models.CharField(max_length=20)),
                ("phone_number", models.CharField(max_length=20)),
                ("relationship", models.CharField(max_length=10)),
                ("address", models.TextField()),
                (
                    "student",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "student"},
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="LeaveApplication",
            fields=[
                (
                    "leave_id",
                    models.CharField(max_length=20, primary_key=True, serialize=False),
                ),
                ("reason", models.TextField(max_length=255)),
                ("apply_date", models.DateField(default=django.utils.timezone.now)),
                ("start_datetime", models.DateField(blank=True, null=True)),
                ("end_datetime", models.DateField(blank=True, null=True)),
                ("approved_date", models.DateField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                        ],
                        default="pending",
                        max_length=10,
                    ),
                ),
                ("remark", models.TextField(blank=True, null=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        limit_choices_to={"role": "teacher"},
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_leaves",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "guardian",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to="user.guardian",
                    ),
                ),
                (
                    "student",
                    models.ForeignKey(
                        limit_choices_to={"role": "student"},
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "leave_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.leavetype"
                    ),
                ),
                ("period", models.ManyToManyField(to="user.period")),
            ],
        ),
        migrations.CreateModel(
            name="CourseStudent",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "middle_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "final_score",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                (
                    "average",
                    models.DecimalField(
                        blank=True, decimal_places=2, max_digits=5, null=True
                    ),
                ),
                ("rank", models.PositiveIntegerField(blank=True, null=True)),
                (
                    "course_id",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.course"
                    ),
                ),
                (
                    "student_id",
                    models.ForeignKey(
                        limit_choices_to={"role": "student"},
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "semester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to="user.semester"
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="user",
            name="semester",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="user.semester",
            ),
        ),
    ]
