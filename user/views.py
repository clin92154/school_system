# from rest_framework.views import GenericAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenBlacklistView
from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views import View
from django.contrib.auth.hashers import make_password
from django.utils.crypto import get_random_string
from django.db.models import Q
from .models import User, Course, Semester
from .models import *
from .serializers import *
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from drf_spectacular.types import OpenApiTypes

#登入登出模組
# 登入 API
class LoginView(GenericAPIView):
    serializer_class = LoginSerializer

    @extend_schema(
        request=LoginSerializer,
        responses={
            200: {
                "type": "object",
                "properties": {
                    "refresh": {"type": "string"},
                    "access": {"type": "string"},
                    "role": {"type": "string"},
                    "name": {"type": "string"},
                    "user_id": {"type": "string"}
                }
            },
            401: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="使用者登入 API",
        summary="使用者登入"
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = serializer.validated_data['user_id']
        password = serializer.validated_data['password']
        
        user = authenticate(request, user_id=user_id, password=password)
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': user.role,
                'name': user.name,
                'user_id': user.user_id
            }, status=status.HTTP_200_OK)
        return Response({'detail': 'Invalid credentials'}, 
                        status=status.HTTP_401_UNAUTHORIZED)


# 登出 API
# 自定義登出 API
class LogoutView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = None  # 登出不需要序列化器

    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "refresh": {"type": "string"}
            },
            "required": ["refresh"]
        },
        responses={
            205: None,
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="使用者登出 API",
        summary="使用者登出"
    )
    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"detail": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)
                
            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
# 重設密碼 API
class ResetPasswordView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ResetPasswordSerializer

    @extend_schema(
        request=ResetPasswordSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="重設使用者密碼",
        summary="密碼重設"
    )
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        new_password = serializer.validated_data['new_password']
        try:
            validate_password(new_password, user)
            user.set_password(new_password)
            user.save()
            return Response({'detail': '密碼重設成功'}, status=status.HTTP_200_OK)
        except ValidationError as e:
            return Response({'detail': e}, status=status.HTTP_400_BAD_REQUEST)

# 監護人視圖
class GuardianView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GuardianSerializer

    @extend_schema(
        responses={
            200: GuardianSerializer,
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取監護人資料",
        summary="查詢監護人資料"
    )
    def get(self, request):
        try:
            guardian = Guardian.objects.get(student=request.user)
            serializer = self.get_serializer(guardian)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Guardian.DoesNotExist as err:
            return Response({'detail': '找不到監護人資料'}, status=status.HTTP_404_NOT_FOUND)

    @extend_schema(
        request=GuardianSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            201: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "guardian_id": {"type": "string"}
                }
            },
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="新增或更新監護人資料",
        summary="監護人資料管理"
    )
    def post(self, request):
        try:
            guardian = Guardian.objects.get(student=request.user)
            serializer = self.get_serializer(guardian, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'detail': '監護人資料更新成功'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Guardian.DoesNotExist:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            guardian = serializer.save(student=request.user)
            return Response({'detail': '監護人資料創建成功', 'guardian_id': guardian.guardian_id}, status=status.HTTP_201_CREATED)

# 用戶檔案視圖
class UserProfileView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserProfileSerializer

    @extend_schema(
        responses={200: UserProfileSerializer},
        description="獲取用戶個人資料",
        summary="查詢個人資料"
    )
    def get(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        request=UserProfileSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="更新用戶個人資料",
        summary="更新個人資料"
    )
    def put(self, request):
        serializer = self.get_serializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'detail': '個人資料更新成功'}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 取得用戶名稱和 user_id API
class UserInfoView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        data = {
            'user_id': user.user_id,
            'name': user.name,
            'role':user.role
        }
        return Response(data, status=status.HTTP_200_OK)








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






# 學生請假申請 API
class LeaveApplicationView(GenericAPIView):
    serializer_class = LeaveApplicationSerializer

    @extend_schema(
        request=LeaveApplicationSerializer,
        responses={
            201: {
                "type": "object",
                "properties": {
                    "detail": {"type": "string"},
                    "leave_id": {"type": "integer"}
                }
            },
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="學生請假申請 API",
        summary="提交請假申請"
    )
    def post(self, request):
        if request.user.role != 'student':
            return Response({'detail': 'Only students can apply for leave.'},
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        leave_application = serializer.save(student=request.user)
        return Response({
            'detail': 'Leave application submitted successfully.',
            'leave_id': leave_application.leave_id
        }, status=status.HTTP_201_CREATED)

# 請假類型列表 API
class LeaveTypeListView(GenericAPIView):
    @extend_schema(
        responses={200: LeaveTypeSerializer(many=True)},
        description="獲取所有請假類型",
        summary="請假類型列表"
    )
    def get(self, request):
        leave_types = LeaveType.objects.all()
        serializer = LeaveTypeSerializer(leave_types, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

# 節次列表 API
class PeriodListView(GenericAPIView):
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

# 請假審核 API
class LeaveApprovalView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = LeaveApprovalSerializer

    @extend_schema(
        request=LeaveApprovalSerializer,
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="教師審核請假申請",
        summary="請假審核"
    )
    def post(self, request, leave_id):
        if request.user.role != 'teacher':
            return Response({'detail': '只有老師可以審核請假申請'}, 
                            status=status.HTTP_403_FORBIDDEN)

        try:
            leave_application = LeaveApplication.objects.get(leave_id=leave_id)
            if leave_application.student.class_name != request.user.class_name:
                return Response({'detail': '您沒有權限審核此請假申請'}, 
                                status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            leave_application.status = serializer.validated_data['status']
            leave_application.approved_by = request.user
            leave_application.approved_date = datetime.now().date()
            leave_application.remark = serializer.validated_data.get('remark', '')
            leave_application.save()

            return Response({'detail': '請假申請審核完成'}, status=status.HTTP_200_OK)
        except LeaveApplication.DoesNotExist:
            return Response({'detail': '找不到請假申請'}, status=status.HTTP_404_NOT_FOUND)


# API View to manage courses
class CourseManagementView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CourseManagementSerializer

    def get(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id)
            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({'detail': '找不到課程'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        if request.user.role != 'teacher':
            return Response({'detail': '只有老師可以創建課程'}, 
                            status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(data=request.data, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.save(teacher_id=request.user)
        return Response({'detail': '課程創建成功', 'course_id': course.course_id}, 
                        status=status.HTTP_201_CREATED)

    def put(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id, teacher_id=request.user)
            serializer = self.get_serializer(course, data=request.data, 
                                              context={'request': request}, 
                                              partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'detail': '課程更新成功'}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({'detail': '找不到課程或您沒有權限修改此課程'}, 
                            status=status.HTTP_404_NOT_FOUND)

    def delete(self, request, course_id):
        try:
            course = Course.objects.get(course_id=course_id, teacher_id=request.user)
            course.delete()
            return Response({'detail': '課程刪除成功'}, status=status.HTTP_200_OK)
        except Course.DoesNotExist:
            return Response({'detail': '找不到課程或您沒有權限刪除此課程'}, 
                            status=status.HTTP_404_NOT_FOUND)


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

class ClassStudentListView(GenericAPIView):
    # permission_classes = (IsAuthenticated,)
    serializer_class = ClassStudentListSerializer

    @extend_schema(
        responses={
            200: ClassStudentListSerializer(many=True),
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取指定班級的學生列表",
        summary="班級學生列表"
    )
    def get(self, request, class_id):
        try:
            class_obj = Class.objects.get(class_id=class_id)
            students = User.objects.filter(class_name=class_obj, role='student')
            serializer = self.get_serializer(students, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Class.DoesNotExist:
            return Response({'detail': '找不到班級'}, status=status.HTTP_404_NOT_FOUND)

# 學生詳細資料視圖
class StudentDetailView(GenericAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StudentDetailSerializer

    def get(self, request, student_id):
        try:
            student = User.objects.get(user_id=student_id, role='student')
            serializer = self.get_serializer(student)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'detail': '找不到學生'}, status=status.HTTP_404_NOT_FOUND)

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
            courses = Course.objects.none()  # 管理員等其他角色預設不提供課程列表

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

class CourseGradeInputView(GenericAPIView):
    @extend_schema(
        request={
            "type": "object",
            "properties": {
                "grades": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "student_id": {"type": "string"},
                            "middle_score": {"type": "number"},
                            "final_score": {"type": "number"}
                        }
                    }
                }
            }
        },
        responses={
            200: {"type": "object", "properties": {"detail": {"type": "string"}}},
            400: {"type": "object", "properties": {"detail": {"type": "string"}}},
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="教師輸入學生成績",
        summary="成績輸入"
    )
    def put(self, request, course_id):
        user = request.user
        if user.role != 'teacher':
            return Response({'detail': 'Only teachers can input grades.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            course = Course.objects.get(course_id=course_id, teacher_id=user)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to input grades for this course.'}, status=status.HTTP_404_NOT_FOUND)

        grades = request.data.get('grades', [])
        if not grades:
            return Response({'detail': 'Grades are required.'}, status=status.HTTP_400_BAD_REQUEST)

        for grade in grades:
            student_id = grade.get('student_id')
            middle_score = grade.get('middle_score')
            final_score = grade.get('final_score')
            student = User.objects.get(user_id= student_id)
            try:
                course_student = CourseStudent.objects.get(course_id=course, student_id=student)
                course_student.middle_score = middle_score
                course_student.final_score = final_score
                if middle_score and final_score:
                    course_student.average = (middle_score + final_score) / 2
                course_student.save()
            except CourseStudent.DoesNotExist:
                return Response({'detail': f'Student with ID {student_id} is not enrolled in this course.'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'detail': 'Grades updated successfully.'}, status=status.HTTP_200_OK)


class StudentGradeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: StudentGradeSerializer(many=True),
            403: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取學生成績資料",
        summary="學生成績查詢"
    )
    def get(self, request):
        user = request.user
        # if user.role != 'student':
        #     return Response({'detail': 'Only students can view their grades.'}, status=status.HTTP_403_FORBIDDEN)

        course_students = CourseStudent.objects.filter(student_id=user)
        data = []
        for course_student in course_students:
            data.append({
                'course_name': course_student.course_id.course_name,
                'semester': course_student.semester.semester_id,
                'middle_score': course_student.middle_score,
                'final_score': course_student.final_score,
                'average': course_student.average,
                'rank': course_student.rank,
            })

        return Response(data, status=status.HTTP_200_OK)


class ClassGradeRankView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, course_id):
        user = request.user
        if user.role != 'teacher':
            return Response({'detail': 'Only teachers can view grades of their students.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            course = Course.objects.get(course_id=course_id, teacher_id=user)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to view grades for this course.'}, status=status.HTTP_404_NOT_FOUND)

        course_students = CourseStudent.objects.filter(course_id=course).order_by('-average')
        data = []
        for rank, course_student in enumerate(course_students, start=1):
            course_student.rank = rank
            course_student.save()
            data.append({
                'student_id': course_student.student_id.user_id,
                'student_name': course_student.student_id.name,
                'middle_score': course_student.middle_score,
                'final_score': course_student.final_score,
                'average': course_student.average,
                'rank': rank
            })

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


class SemesterGradeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    @extend_schema(
        responses={
            200: {
                "type": "object",
                "properties": {
                    "grades": {
                        "type": "array",
                        "items": StudentGradeSerializer
                    },
                    "overall_average": {"type": "number"}
                }
            },
            403: {"type": "object", "properties": {"detail": {"type": "string"}}},
            404: {"type": "object", "properties": {"detail": {"type": "string"}}}
        },
        description="獲取指定學期的成績資料",
        summary="學期成績查詢"
    )
    def get(self, request, semester_id):
        user = request.user
        if user.role != 'student':
            return Response({'detail': 'Only students can view their grades.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            semester = Semester.objects.get(semester_id=semester_id)
        except Semester.DoesNotExist:
            return Response({'detail': 'Semester not found.'}, status=status.HTTP_404_NOT_FOUND)

        course_students = CourseStudent.objects.filter(student_id=user, semester=semester)
        if not course_students:
            # print( Response({'detail': 'No grades found for the selected semester.'}, status=status.HTTP_404_NOT_FOUND))
            return Response({'detail': 'No grades found for the selected semester.'}, status=status.HTTP_404_NOT_FOUND)

        total_score = 0
        total_courses = 0
        data = []
        for course_student in course_students:
            total_score += course_student.average or 0
            total_courses += 1
            data.append({
                'course_name': course_student.course_id.course_name,
                'middle_score': course_student.middle_score,
                'final_score': course_student.final_score,
                'average': course_student.average,
                'rank': course_student.rank,
            })

        overall_average = total_score / total_courses if total_courses > 0 else None

        # print({'grades': data, 'overall_average': overall_average})

        return Response({'grades': data, 'overall_average': overall_average}, status=status.HTTP_200_OK)


class AllSemesterGradeView(GenericAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        if user.role != 'student':
            return Response({'detail': 'Only students can view their grades.'}, status=status.HTTP_403_FORBIDDEN)
            
        course_students = CourseStudent.objects.filter(student_id=user).order_by('semester__year', 'semester__term')
        if not course_students:
            return Response({'detail': 'No grades found'}, status=status.HTTP_404_NOT_FOUND)

        semesters = {}
        for course_student in course_students:
            semester_key = f"{course_student.semester.year}-{course_student.semester.term}"
            if semester_key not in semesters:
                semesters[semester_key] = {
                    'semester_id': course_student.semester.semester_id,
                    'courses': [],
                    'total_score': 0,
                    'total_courses': 0,
                }
            semesters[semester_key]['courses'].append({
                'course_name': course_student.course_id.course_name,
                'middle_score': course_student.middle_score,
                'final_score': course_student.final_score,
                'average': course_student.average,
            })
            semesters[semester_key]['total_score'] += course_student.average or 0
            semesters[semester_key]['total_courses'] += 1

        result = []
        for semester, details in semesters.items():
            result.append({
                'semester': semester,
                'courses': details['courses'],
                'overall_average': details['total_score'] / details['total_courses'] if details['total_courses'] > 0 else None
            })

        return Response({'grades_history': result}, status=status.HTTP_200_OK)
