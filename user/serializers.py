from rest_framework import serializers
from .models import *

# 用戶登入序列化器
class LoginSerializer(serializers.Serializer):
    user_id = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)

# 密碼重設序列化器
class ResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True, write_only=True)

# 監護人序列化器
class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = ['name', 'phone_number', 'relationship', 'address']

# 用戶檔案序列化器
class UserProfileSerializer(serializers.ModelSerializer):
    class_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['user_id', 'name', 'first_name', 'last_name', 'eng_name', 
                 'role', 'semester', 'gender', 'birthday', 'class_name']
        read_only_fields = ['user_id', 'name', 'role', 'semester']

    def get_class_name(self, obj):
        if obj.class_name:
            return f"{obj.class_name.grade} 年 {obj.class_name.class_name} 班"
        return None

# 請假申請序列化器
class LeaveApplicationSerializer(serializers.ModelSerializer):
    period = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Period.objects.all()
    )

    class Meta:
        model = LeaveApplication
        fields = ['leave_type', 'reason', 'start_datetime', 'end_datetime', 'period']
        extra_kwargs = {
            'leave_type': {'required': True},
            'reason': {'required': True},
            'start_datetime': {'required': True},
            'end_datetime': {'required': True},
            'period': {'required': True},
        }

    def validate(self, data):
        if data['end_datetime'] < data['start_datetime']:
            raise serializers.ValidationError("結束時間不能早於開始時間")
        return data

# 請假詳情序列化器
class LeaveDetailSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source='student.user_id')
    leave_type = serializers.CharField(source='leave_type.type_name')
    approved_by = serializers.CharField(source='approved_by.user_id', allow_null=True)
    periods = serializers.SerializerMethodField()

    class Meta:
        model = LeaveApplication
        fields = ['leave_id', 'student', 'leave_type', 'reason', 'apply_date',
                 'start_datetime', 'end_datetime', 'status', 'approved_by',
                 'approved_date', 'remark', 'periods']

    def get_periods(self, obj):
        return [period.period_number for period in obj.period.all()]

# 請假審核序列化器
class LeaveApprovalSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['approved', 'rejected'])
    remark = serializers.CharField(required=False, allow_blank=True)

# 課程管理序列化器
class CourseManagementSerializer(serializers.ModelSerializer):
    # periods = serializers.PrimaryKeyRelatedField(
    #     many=True,
    #     queryset=Period.objects.all()
    # )
    class Meta:
        model = Course
        fields = ['course_name', 'course_description', 'semester', 'class_id',
                 'period', 'day_of_week']
        
    def validate(self, data):
        # 檢查是否有課程時間衝突
        print(data)
        teacher = self.context['request'].user
        semester = data['semester']
        periods = data['period']
        day_of_week = data['day_of_week']
        class_id = data['class_id']
        conflicting_courses1 = Course.objects.filter(
            teacher_id=teacher,
            semester=semester,
            period__in=periods,
            day_of_week=day_of_week
        )

        conflicting_courses2 = Course.objects.filter(
            class_id=class_id,
            semester=semester,
            period__in=periods,
            day_of_week=day_of_week
        )
        
        if self.instance:  # 更新時排除自己
            conflicting_courses1 = conflicting_courses1.exclude(pk=self.instance.pk)
            conflicting_courses2 = conflicting_courses2.exclude(pk=self.instance.pk)
            
        if conflicting_courses1.exists() or conflicting_courses2.exists():
            raise serializers.ValidationError("課程時間衝突")
            
        return data

# 成績輸入序列化器
class GradeInputSerializer(serializers.Serializer):
    student_id = serializers.CharField()
    middle_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)
    final_score = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, allow_null=True)

    def validate(self, data):
        for field in ['middle_score', 'final_score']:
            if field in data and data[field] is not None:
                if data[field] < 0 or data[field] > 100:
                    raise serializers.ValidationError(f"{field} 必須在 0 到 100 之間")
        return data

# 課程列表序列化器
class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher_id.name')
    class_name = serializers.SerializerMethodField()
    periods = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['course_id', 'course_name', 'course_description', 'teacher_name',
                 'class_name', 'semester', 'day_of_week', 'periods']

    def get_class_name(self, obj):
        return obj.class_id.class_id
    

    def get_periods(self, obj):
        return [period.period_number for period in obj.period.all()]

# 學生成績序列化器
class StudentGradeSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course_id.course_name')
    semester = serializers.CharField(source='semester.semester_id')

    class Meta:
        model = CourseStudent
        fields = ['course_name', 'semester', 'middle_score', 'final_score',
                 'average', 'rank']

# 班級列表序列化器
class ClassListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Class
        fields = ['class_id', 'grade', 'class_name', 'year']

# 班級學生列表序列化器
class ClassStudentListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['user_id', 'name', 'gender', 'birthday']

# 學生詳細資料序列化器
class StudentDetailSerializer(serializers.ModelSerializer):
    class_info = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['user_id', 'name', 'role', 'gender','class_info','birthday']

    def get_class_info(self, obj):
        if obj.class_name:
            return {
                'grade': obj.class_name.grade,
                'class_name': obj.class_name.class_name
            }
        return None

# 學期序列化器
class SemesterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Semester
        fields = ['semester_id', 'year', 'term', 'begin_time', 'final_time']

# 課程學生序列化器
class CourseStudentSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course_id.course_name')
    semester = serializers.CharField(source='semester.semester_id')

    class Meta:
        model = CourseStudent
        fields = ['course_name', 'semester', 'middle_score', 'final_score',
                  'average', 'rank']

# 請假類型序列化器
class LeaveTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaveType
        fields = ['id', 'type_name'] 

class PeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = Period
        fields = ['period_number', 'begin_time','end_time'] 

# 請假列表序列化器
class LeaveListSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.name')
    leave_type = serializers.CharField(source='leave_type.type_name')
    periods = serializers.SerializerMethodField()

    class Meta:
        model = LeaveApplication
        fields = ['leave_id', 'student_name', 'leave_type', 'start_datetime', 
                 'end_datetime', 'status', 'periods']

    def get_periods(self, obj):
        return [period.period_number for period in obj.period.all()]