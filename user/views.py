from rest_framework.views import APIView
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


# API View for Categories
class CategoryListView(APIView):
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


# 登入 API
class LoginView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        password = request.data.get('password')
        print(user_id,password)

        # 驗證用戶
        user = authenticate(request, user_id=user_id, password=password)
        if user is not None:
            # 生成 JWT Token
            refresh = RefreshToken.for_user(user)
            role = user.role

            print({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': role,
                'name': user.name,
                'user_id': user.user_id
            })
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'role': role,
                'name': user.name,
                'user_id': user.user_id
            }, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

# 登出 API
# 自定義登出 API
class LogoutView(APIView):
    permission_classes = (IsAuthenticated,)

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
class ResetPasswordView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        new_password = request.data.get('new_password')

        if not new_password:
            return Response({'detail': 'New password is required'}, status=status.HTTP_400_BAD_REQUEST)

        # 設置新密碼
        user.password = make_password(new_password)
        user.save()

        return Response({'detail': 'Password has been reset successfully'}, status=status.HTTP_200_OK)


class GuardianView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user = request.user
        name = request.data.get('name')
        phone_num = request.data.get('phone_num')
        relationship = request.data.get('relationship')
        address = request.data.get('address')
        guardian = Guardian.objects.update_or_create(
            student=user,
            name=name,
            phone_number=phone_num,
            relationship=relationship,
            address=address,
        )
        print(guardian)
        return Response({'detail': 'guardian created successfully.'}, status=status.HTTP_201_CREATED)


    def get(self, request):
        user = request.user
        guardian = Guardian.objects.get(student=user)
        data = {
            'name': guardian.name,
            'guardian_id': guardian.guardian_id,
            'phone_number': guardian.phone_number,
            'relationship': guardian.relationship,
            'address': guardian.address
        }
        return Response(data, status=status.HTTP_200_OK)

    # def put(self, request):
    #     user = request.user
    #     name = request.data.get('name')
    #     gender = request.data.get('gender')
    #     birthday = request.data.get('birthday')

    #     if name:
    #         user.name = name
    #     if gender:
    #         user.gender = gender
    #     if birthday:
    #         user.birthday = birthday

    #     user.save()
    #     return Response({'detail': 'Profile updated successfully'}, status=status.HTTP_200_OK)

# 個人檔案設定 API
class UserProfileView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        data = {
            'user_id': user.user_id,
            'name': user.name,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'eng_name':user.eng_name,
            'role': user.role,
            'semester': user.semester.semester_id if user.semester else None,
            'gender': user.gender,
            'birthday': user.birthday,
            'class_name': f"{user.class_name.grade} 年 {user.class_name.class_name} 班" if user.class_name else None
        }
        return Response(data, status=status.HTTP_200_OK)

    def put(self, request):
        user = request.user
        first_name = request.data.get('first_name')
        eng_name = request.data.get('eng_name')
        last_name = request.data.get('last_name')
        gender = request.data.get('gender')
        birthday = request.data.get('birthday')
        if eng_name:
            user.eng_name = eng_name
        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if gender:
            user.gender = gender
        if birthday:
            user.birthday = birthday
        print(user.eng_name)
        user.save()
        return Response({'detail': 'Profile updated successfully'}, status=status.HTTP_200_OK)

# 取得用戶名稱和 user_id API
class UserInfoView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        data = {
            'user_id': user.user_id,
            'name': user.name,
            'role':user.role
        }
        return Response(data, status=status.HTTP_200_OK)
    

# 學生請假申請 API
class LeaveApplicationView(APIView):
    permission_classes = (IsAuthenticated,)#紀錄tokem有沒有白名單內，如果有的話取得User資料

    def post(self, request):
        user = request.user
        if user.role != 'student':
            return Response({'detail': 'Only students can apply for leave.'}, status=status.HTTP_403_FORBIDDEN)

        leave_type_id = request.data.get('leave_type_id')
        reason = request.data.get('reason')
        start_datetime = request.data.get('start_datetime')
        end_datetime = request.data.get('end_datetime')
        periods= request.data.get('periods') 
        print(periods)
        if not leave_type_id or not reason or not start_datetime or not end_datetime:
            return Response({'detail': 'All fields are required: leave_type_id, reason, start_datetime, end_datetime.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            start_datetime = datetime.strptime(start_datetime, '%Y-%m-%d')
            end_datetime = datetime.strptime(end_datetime, '%Y-%m-%d')
        except ValueError:
            return Response({'detail': 'Invalid datetime format. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)

        if end_datetime < start_datetime:
            return Response({'detail': 'End datetime cannot be earlier than start datetime.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_type = LeaveType.objects.filter(id=leave_type_id).first()
        if not leave_type:
            return Response({'detail': 'Invalid leave type.'}, status=status.HTTP_400_BAD_REQUEST)

        leave_application = LeaveApplication.objects.create(
            student=user,
            leave_type=leave_type,
            reason=reason,
            start_datetime=start_datetime,
            end_datetime=end_datetime
        )
        leave_application.period.set([Period.objects.get(period_number=period) for period in periods])
        return Response({'detail': 'Leave application submitted successfully.', 'leave_id': leave_application.leave_id}, status=status.HTTP_201_CREATED)

# 請假類型列表 API
class LeaveTypeListView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):
        leave_types = LeaveType.objects.all()
        data = [{'type_id': leave_type.id, 'type_name': leave_type.type_name} for leave_type in leave_types]
        return Response(data, status=status.HTTP_200_OK)

# 請假類型列表 API
class PeriodListView(APIView):
    # permission_classes = (IsAuthenticated,)

    def get(self, request):
        periods = Period.objects.all()
        data = [{'period': str(period),'period_id': period.id, 'period_num': period.period_number} for period in periods]
        return Response(data, status=status.HTTP_200_OK)


class LeaveListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        user = request.user
        try:

            if user.role == 'teacher':
                # 老師查詢所屬班級所有學生的請假申請
                if user.class_name:
                    students = User.objects.filter(class_name=user.class_name, role='student')
                    leave_applications = LeaveApplication.objects.filter(student__in=students).order_by("-apply_date","status")
                    data = [
                        {
                            'leave_id': leave.leave_id,
                            'student': leave.student.user_id,
                            'leave_type': leave.leave_type.type_name,
                            'apply_date': leave.apply_date,
                            'start_datetime': leave.start_datetime,
                            'end_datetime': leave.end_datetime,
                            'status':leave.status
                        } for leave in leave_applications
                    ]
                    return Response({'leave_list': data}, status=status.HTTP_200_OK)
                else:
                    return Response({'detail': 'You are not assigned to a class.'}, status=status.HTTP_400_BAD_REQUEST)

            elif user.role == 'student':
                # 學生查詢自己的請假申請
                leave_applications = LeaveApplication.objects.filter(student=user).order_by("-apply_date","status")
                data = [
                    {
                        'leave_id': leave.leave_id,
                        'student': leave.student.user_id,
                        'leave_type': leave.leave_type.type_name,
                        'apply_date': leave.apply_date,
                        'start_datetime': leave.start_datetime,
                        'end_datetime': leave.end_datetime,
                        'status':leave.status
                    } for leave in leave_applications
                ]
                return Response({'leave_list': data}, status=status.HTTP_200_OK)

            else:
                return Response({'detail': 'You do not have permission to view leave applications.'}, status=status.HTTP_403_FORBIDDEN)
        except Exception as err:
                print(err)
                return Response({'detail': err})


# 查詢請假詳細狀態 API
class LeaveDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, leave_id):
        user = request.user
        try:
            leave_application = LeaveApplication.objects.get(leave_id=leave_id)

            # 學生只能查看自己的請假申請，老師可以查看其指導班級學生的請假申請
            if user.role == 'student' and leave_application.student != user:
                return Response({'detail': 'You do not have permission to view this leave application.'}, status=status.HTTP_403_FORBIDDEN)
            elif user.role == 'teacher' and leave_application.student.class_name != user.class_name:
                return Response({'detail': 'You do not have permission to view this leave application.'}, status=status.HTTP_403_FORBIDDEN)
            periods = leave_application.period.all()  # 假設 leave_application 和 period 是多對多關係
            data = {
                'leave_id': leave_application.leave_id,
                'student': leave_application.student.user_id,
                'leave_type': leave_application.leave_type.type_name,
                'reason': leave_application.reason,
                'apply_date': leave_application.apply_date,
                'start_datetime': leave_application.start_datetime,
                'end_datetime': leave_application.end_datetime,
                'status': leave_application.status,
                'approved_by': leave_application.approved_by.user_id if leave_application.approved_by else None,
                'approved_date': leave_application.approved_date,
                'remark': leave_application.remark,
                'periods': [period.period_number for period in periods] # 假設您希望返回節次的 ID 列表
            }           

            return Response(data, status=status.HTTP_200_OK)
        except LeaveApplication.DoesNotExist:
            return Response({'detail': 'Leave application not found.'}, status=status.HTTP_404_NOT_FOUND)

# 老師審核請假申請 API
class LeaveApprovalView(APIView):
    permission_classes = (IsAuthenticated,)
    def post(self, request, leave_id):
        user = request.user
        if user.role != 'teacher':
            return Response({'detail': 'Only teachers can approve leave applications.'}, status=status.HTTP_403_FORBIDDEN)

        try:
            leave_application = LeaveApplication.objects.get(leave_id=leave_id)
            if leave_application.student.class_name != user.class_name:
                return Response({'detail': 'You do not have permission to approve this leave application.'}, status=status.HTTP_403_FORBIDDEN)

            leave_status = request.data.get('status')
            remark = request.data.get('remark', '')

            if leave_status not in ['approved', 'rejected']:
                return Response({'detail': 'Invalid status. Must be either "approved" or "rejected".'}, status=status.HTTP_400_BAD_REQUEST)

            leave_application.status = leave_status
            leave_application.approved_by = user
            leave_application.approved_date = datetime.now().date()
            leave_application.remark = remark
            leave_application.save()

            return Response({'detail': 'Leave application updated successfully.'}, status=status.HTTP_200_OK)
        except LeaveApplication.DoesNotExist:
            return Response({'detail': 'Leave application not found.'}, status=status.HTTP_404_NOT_FOUND)


# API View to manage courses
class CourseManagementView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request,course_id):
        user = request.user
        print(course_id)
        # 根據用戶的角色過濾課程
        if user.role == 'teacher' or user.role == 'student':
            courses = Course.objects.get(course_id=course_id)
        else:
            courses = Course.objects.none()  # 管理員等其他角色預設不提供課程列表

        data = {
                'course_id': courses.course_id,
                'course_name': courses.course_name,
                'course_description': courses.course_description,
                'teacher_name': courses.teacher_id.name,
                'class': {'id':courses.class_id.class_id,'name':f"{courses.class_id.grade} 年 {courses.class_id.class_name} 班",},
                'semester': courses.semester.semester_id,
                'day_of_week': courses.day_of_week,
                'periods': [p.period_number for p in courses.period.all()]
                }
            
        return Response(data, status=status.HTTP_200_OK)
    # 新增課程
    def post(self, request):
        user = request.user
        # 確保只有老師能建立課程
        if user.role != 'teacher':
            return Response({'detail': 'Only teachers can create courses.'}, status=status.HTTP_403_FORBIDDEN)

        # 取得請求資料
        course_name = request.data.get('course_name')
        course_description = request.data.get('course_description')
        semester_id = request.data.get('semester_id')
        class_id = request.data.get('class_id')
        periods = request.data.get('periods')  # 節次
        day_of_week = request.data.get('day_of_week')  # 星期幾（選擇：Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday）（選擇：Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday）  # 星期幾
        print(request.data)

        # 驗證必填字段
        if not (course_name and semester_id and class_id and periods and day_of_week):
            return Response({'detail': 'All fields are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 驗證學期、班級是否存在
        try:
            semester = Semester.objects.get(semester_id=semester_id)
            class_obj = Class.objects.get(class_id=class_id)
        except (Semester.DoesNotExist, Class.DoesNotExist):
            return Response({'detail': 'Invalid semester or class.'}, status=status.HTTP_400_BAD_REQUEST)

        # 驗證節數是否存在
        period_objs = Period.objects.filter(id__in=periods)
        if period_objs.count() != len(periods):
            return Response({'detail': 'One or more periods are invalid.'}, status=status.HTTP_400_BAD_REQUEST)
        # 驗證是否衝堂
        conflicting_courses = Course.objects.filter(
            Q(teacher_id=user) & Q(semester=semester) & Q(period__in=period_objs) & Q(day_of_week=day_of_week)
        )
        if conflicting_courses.exists():
            return Response({'detail': 'Course schedule conflicts with another course.'}, status=status.HTTP_400_BAD_REQUEST)
    
        # # 創建課程
        course = Course.objects.create(
            course_name=course_name,
            course_description=course_description,
            teacher_id=user,
            class_id=class_obj,
            semester=semester,
            day_of_week=day_of_week
        )
        course.period.set(period_objs)

        # return Response({'detail': 'Course created successfully.', 'course_id': course.course_id}, status=status.HTTP_201_CREATED)
        return Response({'detail': 'Course created successfully.'}, status=status.HTTP_201_CREATED)

    # 修改課程
    def put(self, request, course_id):
        user = request.user
        # 確保只有課程的建立者可以修改
        try:
            course = Course.objects.get(course_id=course_id, teacher_id=user)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to edit this course.'}, status=status.HTTP_404_NOT_FOUND)

        # 取得請求資料
        course_name = request.data.get('course_name')
        course_description = request.data.get('course_description')
        semester_id = request.data.get('semester_id')
        class_id = request.data.get('class_id')
        periods = request.data.get('periods')  # 節次
        day_of_week = request.data.get('day_of_week')  # 星期幾

        # 驗證學期、班級是否存在
        try:
            print(semester_id,class_id)
            semester = Semester.objects.get(semester_id=semester_id)
            class_obj = Class.objects.get(class_id=class_id)
        except (Semester.DoesNotExist, Class.DoesNotExist):
            return Response({'detail': 'Invalid semester or class.'}, status=status.HTTP_400_BAD_REQUEST)

        # 驗證節數是否存在
        period_objs = Period.objects.filter(id__in=periods)
        if period_objs.count() != len(periods):
            return Response({'detail': 'One or more periods are invalid.'}, status=status.HTTP_400_BAD_REQUEST)

        # 更新課程信息
        course.course_name = course_name
        course.course_description = course_description
        course.semester = semester
        course.class_id = class_obj
        course.day_of_week = day_of_week
        course.period.set(period_objs)
        course.save()

        return Response({'detail': 'Course updated successfully.'}, status=status.HTTP_200_OK)

    # 刪除課程
    def delete(self, request, course_id):
        user = request.user
        # 確保只有課程的建立者可以刪除
        try:
            course = Course.objects.get(course_id=course_id, teacher_id=user)
        except Course.DoesNotExist:
            return Response({'detail': 'Course not found or you do not have permission to delete this course.'}, status=status.HTTP_404_NOT_FOUND)

        course.delete()
        return Response({'detail': 'Course deleted successfully.'}, status=status.HTTP_200_OK)


# API to get class list
class ClassListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        classes = Class.objects.all()
        data = [{'class_id': c.class_id, 'class_name': c.class_name, 'grade': c.grade, 'year': c.year} for c in classes]
        return Response(data, status=status.HTTP_200_OK)

class ClassStudentListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, class_id):
        try:
            class_obj = Class.objects.get(class_id=class_id)
        except Class.DoesNotExist:
            return Response({'detail': 'Class not found.'}, status=status.HTTP_404_NOT_FOUND)

        students = User.objects.filter(class_name=class_obj, role='student')
        student_data = [
            {
                'student_id': student.user_id,
                'name': student.name,
                'gender': student.gender,
                'birthday': student.birthday,
            } for student in students
        ]
        return Response({'students': student_data}, status=status.HTTP_200_OK)


class StudentDetailView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, student_id):
        try:
            student = User.objects.get(user_id=student_id, role='student')
        except User.DoesNotExist:
            return Response({'detail': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

        student_data = {
            'student_id': student.user_id,
            'name': student.name,
            'gender': student.gender,
            'birthday': student.birthday,
            'class_name': student.class_name.class_name if student.class_name else None,
            'grade': student.class_name.grade if student.class_name else None,
        }
        return Response(student_data, status=status.HTTP_200_OK)


# API to get list of days in a week
class DaysOfWeekView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        return Response(days, status=status.HTTP_200_OK)

# API to get semester list
class SemesterListView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        semesters = Semester.objects.all()
        data = [{'semester_id': s.semester_id, 'year': s.year, 'term': s.term} for s in semesters]
        return Response(data, status=status.HTTP_200_OK)

class CourseListView(APIView):
    permission_classes = (IsAuthenticated,)

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

class CourseGradeInputView(APIView):
    permission_classes = (IsAuthenticated,)

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


class StudentGradeView(APIView):
    permission_classes = (IsAuthenticated,)

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


class ClassGradeRankView(APIView):
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

class ScheduleView(APIView):
    permission_classes = (IsAuthenticated,)

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


class SemesterGradeView(APIView):
    permission_classes = (IsAuthenticated,)

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

        print({'grades': data, 'overall_average': overall_average})

        return Response({'grades': data, 'overall_average': overall_average}, status=status.HTTP_200_OK)


class AllSemesterGradeView(APIView):
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
