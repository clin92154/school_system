from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from user.models import User, Class, Semester
import random
from datetime import datetime , timedelta
class Command(BaseCommand):
    help = 'Create sample data including groups, teachers, students, classes, and semesters'

    def handle(self, *args, **kwargs):
        self.create_groups()
        self.create_semesters()
        self.create_classes()
        self.create_teachers(10)
        self.create_students(10)
        self.stdout.write(self.style.SUCCESS('All sample data and groups have been successfully created.'))

    def create_groups(self):
        """創建群組並分配權限"""
        groups = ['student', 'teacher', 'admin']
        for group_name in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(self.style.SUCCESS(f'Group "{group_name}" created.'))
            else:
                self.stdout.write(f'Group "{group_name}" already exists.')

        # 分配權限示例 (根據需求調整)
        self.assign_permissions('student', ['view_user'])
        self.assign_permissions('teacher', ['view_user', 'change_user'])
        self.assign_permissions('admin', ['add_user', 'change_user', 'delete_user', 'view_user'])

    def assign_permissions(self, group_name, permission_codenames):
        """分配權限給指定群組"""
        group = Group.objects.get(name=group_name)
        content_type = ContentType.objects.get_for_model(User)
        for codename in permission_codenames:
            try:
                permission = Permission.objects.get(content_type=content_type, codename=codename)
                group.permissions.add(permission)
                self.stdout.write(f'Permission "{codename}" added to group "{group_name}".')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Permission "{codename}" does not exist.'))

    def create_semesters(self):
        """創建學期"""
        Semester.objects.get_or_create(year=2023, term=1,begin_time='2023-01-01',final_time='2023-06-30')
        Semester.objects.get_or_create(year=2023, term=2,begin_time='2023-07-01',final_time='2023-06-30')
        Semester.objects.get_or_create(year=2024, term=1,begin_time='2024-01-01',final_time='2024-06-30')
        Semester.objects.get_or_create(year=2024, term=2,begin_time='2024-07-01',final_time='2024-06-30')

        self.stdout.write(self.style.SUCCESS('Semesters created.'))

    def create_classes(self):
        """創建班級"""
        for i in range(1, 4):  # 創建三個班級 A, B, C
            Class.objects.get_or_create(
                class_name=chr(64 + i),  # A, B, C
                grade=i,
                year=2023
            )
        self.stdout.write(self.style.SUCCESS('Classes created.'))

    def create_teachers(self, count):
        """創建教師"""
        semesters = list(Semester.objects.all())
        classes = list(Class.objects.all())
        for i in range(count):
            user_id = f"T{i+1:03d}"
            first_name = f"Teacher"
            last_name = f"{i+1}"
            gender = random.choice(['male', 'female'])
            birthday = self.random_date()
            semester = random.choice(semesters)
            class_name = random.choice(classes)

            teacher = User.objects.create_user(
                user_id=user_id,
                name=f"{first_name} {last_name}",
                first_name=first_name,
                last_name=last_name,
                birthday=birthday,
                role='teacher',
                gender=gender,
                semester=semester,
                class_name=class_name
            )
            teacher.groups.add(Group.objects.get(name='teacher'))
        self.stdout.write(self.style.SUCCESS(f'{count} Teachers created.'))

    def create_students(self, count):
        """創建學生"""
        classes = list(Class.objects.all())
        semesters = list(Semester.objects.all())
        for i in range(count):
            user_id = f"S{i+1:03d}"
            first_name = f"Student"
            last_name = f"{i+1}"
            gender = random.choice(['male', 'female'])
            birthday = self.random_date()
            semester = random.choice(semesters)
            class_name = random.choice(classes)

            student = User.objects.create_user(
                user_id=user_id,
                name=f"{first_name} {last_name}",
                first_name=first_name,
                last_name=last_name,
                birthday=birthday,
                role='student',
                gender=gender,
                semester=semester,
                class_name=class_name
            )
            student.groups.add(Group.objects.get(name='student'))
        self.stdout.write(self.style.SUCCESS(f'{count} Students created.'))

    def random_date(self, start_year=1980, end_year=2010):
        """生成隨機生日"""
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
