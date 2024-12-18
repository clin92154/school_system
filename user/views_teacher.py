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
            
            if 'non_field_errors' in serializer.errors:
                return Response({'detail':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            return Response({'detail':serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        course = serializer.save(teacher_id=request.user)
        return Response({'detail': '課程建立成功', 'course_id': course.course_id}, 
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


class CourseGradeInputView(GenericAPIView):
    serializer_class = GradeInputSerializer

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
    serializer_class = GradeInputSerializer

    def get(self, request, course_id):
        user = request.user
        if user.role != 'teacher':
            return Response({'detail': 'Only teachers can view grades of their students.'}, status=status.HTTP_403_FORBIDDEN)



        try:
            course = Course.objects.get(course_id=course_id, teacher_id=user)

        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to view grades for this course.'}, status=status.HTTP_404_NOT_FOUND)


        try:
            course_students = CourseStudent.objects.filter(course_id=course).order_by('-average')

        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to view grades for this course.'}, status=status.HTTP_404_NOT_FOUND)


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
