from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate
from .models import *
from .serializers import *
from rest_framework.generics import GenericAPIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

class SemesterGradeView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, semester_id):
        user = request.user
        if user.role != 'student':  #驗證授權
            return Response({'detail': 'Only students can view their grades.'}, status=status.HTTP_403_FORBIDDEN)
        try:
            semester = Semester.objects.get(semester_id=semester_id)
        except Semester.DoesNotExist: #如果學期不存在
            return Response({'detail': 'Semester not found.'}, status=status.HTTP_404_NOT_FOUND)

        course_students = CourseStudent.objects.filter(student_id=user, semester=semester)  #取得選擇學期之各科目成績單
        if not course_students: #如果該學期不存在成績
            return Response({'detail': 'No grades found for the selected semester.'}, status=status.HTTP_404_NOT_FOUND)

        total_score = 0
        total_courses = 0
        data = []
        for course_student in course_students:  #依據各科目成績單計算總成績
            total_score += course_student.average or 0
            total_courses += 1
            data.append({
                'course_name': course_student.course_id.course_name,
                'middle_score': course_student.middle_score,
                'final_score': course_student.final_score,
                'average': course_student.average,
                'rank': course_student.rank,
            })

        overall_average = total_score / total_courses if total_courses > 0 else None #依據計算總成績平均
        return Response({'grades': data, 'overall_average': overall_average}, status=status.HTTP_200_OK) #回傳各科目成績單，學期總平均
