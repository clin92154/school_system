
# from rest_framework.views import GenericAPIView
from rest_framework.views import APIView

from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import *
from .serializers import *
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter






# API View for Categories
class CategoryListView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = User.objects.get(user_id=request.user)
        excluderoles = 'teachers' if user.role != 'teacher' else 'students' 
        parent_category = Category.objects.filter(parent_category=None)
        parent_category = parent_category.exclude(roles=excluderoles)
        data = [{'name': p_category.name,
          'roles': p_category.roles,
          'url':p_category.url,
          'subcategory':[{'name': category.name,
          'roles': category.roles,
          'url':f'{p_category.url}/{category.url}'} for category in Category.objects.filter(parent_category=p_category.id).exclude(roles=excluderoles)]
        } for p_category in parent_category ]
        
        return Response({'data':data},status=status.HTTP_200_OK)







# 請假類型列表 API
class LeaveTypeListView(APIView):
    @extend_schema(
        responses={200: LeaveTypeSerializer(many=True)},
        description="獲取所有請假類型",
        summary="請假類型列表"
    )
    def get(self, request, *args, **kwargs):
        leave_types = LeaveType.objects.all()
        serializer = LeaveTypeSerializer(leave_types, many=True)
        return Response(serializer.data)
# 節次列表 API
class PeriodListView(APIView):
    @extend_schema(
        responses={200: PeriodSerializer(many=True)},
        description="獲取所有課程節次",
        summary="課程節次列表"
    )
    def get(self, request):
        periods = Period.objects.all()
        serializer = PeriodSerializer(periods, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 請假列表 API
class LeaveListView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LeaveListSerializer

    @extend_schema(
        responses={
            200: LeaveListSerializer(many=True),
            403: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取請假列表（教師可查看班級學生請假，學生可查看自己的請假）",
        summary="請假列表查詢"
    )
    def get(self, request):
        user = request.user
        if user.role == 'teacher':
            students = User.objects.filter(class_name=user.class_name, role='student')
            leave_applications = LeaveApplication.objects.filter(student__in=students).order_by('status', 'apply_date')
        elif user.role == 'student':
            leave_applications = LeaveApplication.objects.filter(student=user).order_by('status', 'apply_date')
        else:
            return Response({'detail': '您沒有權限查看請假申請'}, 
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(leave_applications, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 請假詳情 API
class LeaveDetailView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LeaveDetailSerializer

    @extend_schema(
        responses={
            200: LeaveDetailSerializer,
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取請假申請詳細資訊",
        summary="請假詳情查詢"
    )
    def get(self, request, leave_id):
        try:
            leave_application = LeaveApplication.objects.get(leave_id=leave_id)
            if request.user.role == 'student' and leave_application.student != request.user:
                return Response({'detail': '您沒有權限查看此請假申請'}, 
                                status=status.HTTP_403_FORBIDDEN)
            elif request.user.role == 'teacher' and leave_application.student.class_name != request.user.class_name:
                return Response({'detail': '您沒有權限查看此請假申請'}, 
                                status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(leave_application)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except LeaveApplication.DoesNotExist:
            return Response({'detail': '找不到請假申請'}, status=status.HTTP_404_NOT_FOUND)




# API to get class list
class ClassListView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ClassListSerializer

    @extend_schema(
        responses={200: ClassListSerializer(many=True)},
        description="獲取所有班級列表",
        summary="班級列表"
    )
    def get(self, request):
        classes = Class.objects.all()
        serializer = self.get_serializer(classes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


# API to get list of days in a week
class DaysOfWeekView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return Response(days, status=status.HTTP_200_OK)

# API to get semester list
class SemesterListView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SemesterSerializer

    def get(self, request):
        semesters = Semester.objects.all()
        serializer = self.get_serializer(semesters, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class CourseListView(GenericAPIView):
    serializer_class = CourseListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='semester_id',
                description='學期 ID',
                required=False,
                type=str
            )
        ],
        responses={
            200: {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "course_id": {"type": "string"},
                        "course_name": {"type": "string"},
                        "course_description": {"type": "string"},
                        "teacher_name": {"type": "string"},
                        "class": {"type": "string"},
                        "semester": {"type": "string"},
                        "day_of_week": {"type": "string"},
                        "periods": {"type": "array", "items": {"type": "integer"}}
                    }
                }
            }
        },
        description="獲取課程列表",
        summary="課程列表查詢"
    )
    def get(self, request):
        user = request.user
        semester_id = request.query_params.get('semester_id')  # 從查詢參數中獲取 semester_id

        # 根據用戶的角色過濾課程
        if user.role == 'teacher':
            courses = Course.objects.filter(teacher_id=user)
        elif user.role == 'student':
            courses = Course.objects.filter(class_id=user.class_name)
        else:
            return Response({'detail': '您沒有權限查詢課表'}, 
                            status=status.HTTP_403_FORBIDDEN)
        # 如果提供了 semester_id，進一步過濾課程
        if semester_id:
            try:
                semester = Semester.objects.get(semester_id=semester_id)
                courses = courses.filter(semester=semester)
            except Semester.DoesNotExist:
                return Response({'detail': 'Semester not found.'}, status=status.HTTP_404_NOT_FOUND)
        
        data = [
            {
                'course_id': c.course_id,
                'course_name': c.course_name,
                'course_description': c.course_description,
                'teacher_name': c.teacher_id.name,
                'class': f"{c.class_id.grade} 年 {c.class_id.class_name} 班",
                'semester': c.semester.semester_id,
                'day_of_week': c.day_of_week,
                'periods': [p.period_number for p in c.period.all()]
            }
            for c in courses
        ]
        return Response(data, status=status.HTTP_200_OK)




class ScheduleView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "schedule": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "course_id": {"type": "string"},
                                "course_name": {"type": "string"},
                                "course_description": {"type": "string"},
                                "day_of_week": {"type": "string"},
                                "periods": {
                                    "type": "array",
                                    "items": {"type": "integer"}
                                }
                            }
                        }
                    }
                }
            },
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取課表資料（教師獲取授課課表，學生獲取班級課表）",
        summary="課表查詢"
    )
    def get(self, request, semester_id):
        user = request.user
        try:
            semester = Semester.objects.get(semester_id=semester_id)
        except Semester.DoesNotExist:
            return Response({'detail': 'Semester not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 根據使用者角色顯示對應課表
        if user.role == 'student':
            courses = Course.objects.filter(class_id=user.class_name, semester=semester)
        elif user.role == 'teacher':
            courses = Course.objects.filter(teacher_id=user, semester=semester)
        else:
            return Response({'detail': 'Only students and teachers can view schedules.'}, status=status.HTTP_403_FORBIDDEN)

        course_data = [
            {
                'course_id': course.course_id,
                'course_name': course.course_name,
                'course_description': course.course_description,
                'day_of_week': course.day_of_week,
                'periods': [period.period_number for period in course.period.all()]
            } for course in courses
        ]

        return Response({'schedule': course_data}, status=status.HTTP_200_OK)


