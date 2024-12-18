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
