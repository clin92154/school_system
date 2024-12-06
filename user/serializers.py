from .models import User, LeaveApplication
from rest_framework import serializers
from .models import LeaveApplication

class LeaveApplicationSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.name', read_only=True)

    class Meta:
        model = LeaveApplication
        fields = [
            'leave_id',
            'student',
            'student_name',
            'leave_type',
            'reason',
            'apply_date',
            'start_datetime',
            'end_datetime',
            'status',
            'approved_by',
            'approved_by_name',
            'approved_date',
            'remark'
        ]