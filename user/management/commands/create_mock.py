from django.core.management.base import BaseCommand
from user.models import User, Class, LeaveType, LeaveApplication
from datetime import date, datetime


class Command(BaseCommand):
    help = 'Create initial data for teachers, students, classes, and leave applications'

    def handle(self, *args, **kwargs):
        # Create Classes
        classes = []
        teachers = []
        # Create Teachers
        for i in range(1, 4):
            teacher = User.objects.create_user(
                user_id=f'T00{i}',
                name=f'Teacher {i}',
                birthday=date(1980, i, 15),
                role='teacher',
            )
            teachers.append(teacher)
        self.stdout.write(self.style.SUCCESS('Successfully created teachers.'))

        for i in range(1, 4):  # Create three classes A, B, C
            class_obj = Class.objects.create(
                class_name=chr(64 + i),  # A, B, C
                grade=i,
                year=2023,
                teacher_id = teachers[i-1]
            )
            classes.append(class_obj)
        self.stdout.write(self.style.SUCCESS('Successfully created classes.'))



        # Create Students
        for i in range(1, 11):  # Create ten students
            User.objects.create_user(
                user_id=f'S00{i}',
                name=f'Student {i}',
                birthday=date(2005, (i % 12) + 1, 15),
                role='student',
                class_name=classes[i % 3]
            )
        self.stdout.write(self.style.SUCCESS('Successfully created students.'))

        # # Create Leave Types
        # leave_types = ['Sick Leave', 'Personal Leave', 'Family Emergency']
        # for leave_type in leave_types:
        #     LeaveType.objects.create(type_name=leave_type)
        # self.stdout.write(self.style.SUCCESS('Successfully created leave types.'))

        # # Create Leave Applications for Students
        # students = User.objects.filter(role='student')
        # leave_type = LeaveType.objects.all()[0].id
        # for student in students:
        #     LeaveApplication.objects.create(
        #         student=student,
        #         leave_type=leave_type,
        #         reason='Feeling unwell',
        #         apply_date=date(2024, 11, 25),
        #         start_datetime=datetime(2024, 11, 25, 9, 0),
        #         end_datetime=datetime(2024, 11, 25, 12, 0),
        #         status='pending'
        #     )
        # self.stdout.write(self.style.SUCCESS('Successfully created leave applications.'))
