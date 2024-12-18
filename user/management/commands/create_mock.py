from django.core.management.base import BaseCommand
from user.models import User, Class, LeaveType, LeaveApplication
from datetime import date, datetime


class Command(BaseCommand):
    help = 'Create initial data for teachers, students, classes, and leave applications'

    def handle(self, *args, **kwargs):

        # Create Leave Types
        leave_types = ['病假', 'Personal Leave', 'Family Emergency']
        for leave_type in leave_types:
            LeaveType.objects.create(type_name=leave_type)
        self.stdout.write(self.style.SUCCESS('Successfully created leave types.'))

        # Create Leave Applications for Students
        students = User.objects.filter(role='student')
        leave_type = LeaveType.objects.all()[0].id
        for student in students:
            LeaveApplication.objects.create(
                student=student,
                leave_type=leave_type,
                reason='Feeling unwell',
                apply_date=date(2024, 11, 25),
                start_datetime=datetime(2024, 11, 25, 9, 0),
                end_datetime=datetime(2024, 11, 25, 12, 0),
                status='pending'
            )
        self.stdout.write(self.style.SUCCESS('Successfully created leave applications.'))
