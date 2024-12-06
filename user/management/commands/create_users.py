import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from user.models import User

class Command(BaseCommand):
    help = 'Create sample teachers and students'

    def handle(self, *args, **kwargs):
        self.create_teachers(10)
        self.create_students(10)
        self.stdout.write(self.style.SUCCESS('Successfully created 10 teachers and 10 students.'))

    def create_teachers(self, count):
        for i in range(count):
            user_id = f"T{i+1:03d}"
            name = f"Teacher {i+1}"
            birthday = self.random_date()
            User.objects.create_user(
                user_id=user_id,
                name=name,
                birthday=birthday,
                role='teacher',
                username=user_id  # 设置 username 为 user_id，以确保唯一性
            )

    def create_students(self, count):
        for i in range(count):
            user_id = f"S{i+1:03d}"
            name = f"Student {i+1}"
            birthday = self.random_date()
            User.objects.create_user(
                user_id=user_id,
                name=name,
                birthday=birthday,
                role='student',
                username=user_id  # 设置 username 为 user_id，以确保唯一性
            )

    def random_date(self, start_year=1980, end_year=2010):
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        delta = end_date - start_date
        random_days = random.randint(0, delta.days)
        return start_date + timedelta(days=random_days)
