from datetime import date
from rest_framework.test import APITestCase, APIClient
from django.urls import reverse 
from .user.models import *
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import date
from django.test import TestCase

class UserModelTests(TestCase):
    def test_password_validation(self):
        user = User(user_id='S123', birthday='2000-01-01', role='student', name='Test User')
        short_password = '123'
        valid_password = 'Valid123!'

        # 測試短密碼
        with self.assertRaises(ValidationError):
            validate_password(short_password, user)

        # 測試有效密碼
        try:
            validate_password(valid_password, user)
        except ValidationError:
            self.fail("Valid password failed validation")

class UserProfileTests(APITestCase):
    def setUp(self):
        # 建立一個測試用戶
        self.user = User.objects.create_user(
            user_id='U001',
            first_name='Test',
            last_name= ' User',
            birthday=date(1995, 5, 15),
            role='student',
            password='0515Test!',
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_get_user_profile(self):
        url = '/api/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.user.user_id)
        self.assertEqual(response.data['name'], self.user.name)
        self.assertEqual(response.data['role'], self.user.role)

    def test_update_user_profile(self):
        url = '/api/profile/'  
        data = {'first_name': 'Updated','last_name':'User', 'gender': 'male', 'birthday': '1995-06-20'}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertEqual(self.user.name, 'Updated User')
        self.assertEqual(self.user.gender, 'male')
        self.assertEqual(str(self.user.birthday), '1995-06-20')
class ResetPasswordTests(APITestCase):
    def setUp(self):
        # 建立一個測試用戶
        self.user = User.objects.create_user(
            user_id='U002',
            name='Test User 2',
            birthday=date(1996, 7, 20),
            password='0720Test!',
            role='teacher'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_reset_password(self):
        url = '/api/reset/password/'  # 假設在 urls.py 中已命名此視圖為 'category-list'
        data = {'new_password': 'newpassword789'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword789'))

class AuthenticationTests(APITestCase):
    def setUp(self):
        # 建立一個測試用戶，並正確設置密碼
        self.user = User.objects.create(
            user_id='T111',
            name='Teacher 1',
            birthday=date(1990, 5, 3),
            role='teacher'
        )
        # self.user.set_password('0503Django2023!')
        self.user.save()

    def test_login(self):
        # 使用 reverse 來獲取 login URL，避免硬編碼 URL 可能導致的錯誤
        url = '/api/login/'  # 'login' 是在 urls.py 中設置的名稱
        data = {'user_id': 'T111', 'password': '0503Test!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['user_id'], 'T111')

    def test_logout(self):
        # 先登入獲取 token
        login_url = '/api/login/'
        login_data = {'user_id': 'T111', 'password': '0503Test!'}
        login_response = self.client.post(login_url, login_data, format='json')
        
        # 確保登入成功
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # 獲取 access 和 refresh token
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']

        # 測試登出
        logout_url ='/api/logout/'
        logout_data = {'refresh': refresh_token}

        # 設置 Authorization header 為獲取的 access token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.post(logout_url, logout_data, format='json')

        # 確認狀態碼是否為 205，表示成功登出
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

# 測試 CategoryListView API
class CategoryListViewTest(APITestCase):

    def setUp(self):
        # 建立用戶和角色
        self.user = User.objects.create_user(
            user_id='U001',
            name='Test User',
            birthday=date(1990, 1, 1),
            password='password123',
            role='teacher'
        )
        self.client = APIClient()
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + str(refresh.access_token))

        # 建立分類
        self.parent_category = Category.objects.create(name='Parent Category', roles='teachers')
        self.child_category = Category.objects.create(name='Child Category', roles='teachers', parent_category=self.parent_category)

    def test_category_list_view(self):
        # 測試獲取分類列表
        url = '/api/categories/'  # 假設在 urls.py 中已命名此視圖為 'category-list'
        response = self.client.get(url)
        
        # 檢查回應狀態
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 檢查回應數據
        self.assertIn('data', response.data)
        self.assertEqual(len(response.data['data']), 1)
        self.assertEqual(response.data['data'][0]['name'], 'Parent Category')
        self.assertEqual(len(response.data['data'][0]['subcategory']), 1)
        self.assertEqual(response.data['data'][0]['subcategory'][0]['name'], 'Child Category')

class LeaveApplicationTests(APITestCase):
    def setUp(self):
        # 建立一個測試用的學生用戶
        self.user = User.objects.create_user(
            user_id='S001',
            name='Student User',
            birthday=date(2000, 5, 15),
            password='testpassword123',
            role='student'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 建立請假類型和節次
        self.leave_type = LeaveType.objects.create(type_name='Sick Leave')
        self.period = Period.objects.create(period_number=1, begin_time='09:00', end_time='10:00')

    def test_create_leave_application(self):
        """/api/leaving-application/"""
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('leave_id', response.data)

    def test_create_leave_application_invalid_leave_type(self):
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': 999,  # 無效的請假類型 ID
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Invalid leave type.')

    def test_create_leave_application_end_before_start(self):
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Family emergency',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-24',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'End datetime cannot be earlier than start datetime.')

    def test_create_leave_application_missing_fields(self):
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'No period selected'
            # 缺少 start_datetime, end_datetime, 和 periods
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'All fields are required: leave_type_id, reason, start_datetime, end_datetime.')

    def test_list_leave_applications_as_student(self):

        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')


        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        url = '/api/list/leaving/'
        response = self.client.get(url, format='json')
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data['leave_list'][0]['student'], self.user.user_id)

class LeaveApplicationTeacherTests(APITestCase):
    def setUp(self):
        # 建立一個測試用的班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=3,
            year=2024
        )

        # 建立一個測試用的學生用戶
        self.student_user = User.objects.create_user(
            user_id='SS01',
            name='Student123',
            birthday=date(2000, 5, 15),
            password='testpassword123',
            role='student',
            class_name=self.class_obj
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)

        # 建立一個測試用的老師用戶
        self.teacher_user = User.objects.create_user(
            user_id='TT01',
            name='Teacher123',
            birthday=date(1980, 7, 10),
            password='testpassword123',
            role='teacher',
            class_name=self.class_obj
        )
        self.teacher_token = str(RefreshToken.for_user(self.teacher_user).access_token)

        # 建立請假類型和節次
        self.leave_type = LeaveType.objects.create(type_name='Sick Leave')
        self.period = Period.objects.create(period_number=1, begin_time='09:00', end_time='10:00')

    def test_list_leave_applications_as_teacher(self):
        # 學生申請請假 
        """POST /api/leaving-application/"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('leave_id', response.data)

        # 老師查詢請假列表
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        url = '/api/list/leaving/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data['leave_list']) > 0)
        self.assertEqual(response.data['leave_list'][0]['student'], self.student_user.user_id)
        self.assertEqual(response.data['leave_list'][0]['leave_type'], self.leave_type.type_name)

    def test_leave_detail_view(self):
        """post '/api/leaving-application/'"""
        """GET '/api/leaving-detail/{leave_id}'"""

        # 學生申請請假
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        leave_id = response.data['leave_id']

        # 學生查詢請假詳細狀態
        url = f'/api/leaving-detail/{leave_id}/'
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['leave_id'], leave_id)
        self.assertEqual(response.data['student'], self.student_user.user_id)

    def test_leave_approval_view(self):
        # 學生申請請假
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = '/api/leaving-application/'
        data = {
            'leave_type_id': self.leave_type.id,
            'reason': 'Feeling unwell',
            'start_datetime': '2024-11-25',
            'end_datetime': '2024-11-25',
            'periods': [self.period.id]
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        leave_id = response.data['leave_id']

        # 老師審核請假
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        url = f'/api/leave-approval/{leave_id}/'
        data = {'status': 'approved', 'remark': 'Approved by teacher'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], 'Leave application updated successfully.')

    # def test_leave_manage_view(self):
    #     # 學生申請請假
    #     self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
    #     url = '/api/leaving-application/'
    #     data = {
    #         'leave_type_id': self.leave_type.id,
    #         'reason': 'Feeling unwell',
    #         'start_datetime': '2024-11-25',
    #         'end_datetime': '2024-11-25',
    #         'periods': [self.period.id]
    #     }
    #     response = self.client.post(url, data, format='json')
    #     self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    #     leave_id = response.data['leave_id']

    #     # 學生刪除請假申請
    #     response = self.client.delete(url, format='json')
    #     # print(response.data)
    #     self.assertEqual(response.status_code, status.HTTP_200_OK)
    #     self.assertEqual(response.data['detail'], 'Leave application deleted successfully.')

class CourseManagementTests(APITestCase):

    
    def setUp(self):
        # Create a teacher user
        self.teacher =  User.objects.create_user(
            user_id='T001',
            name='Teacher123',
            birthday=date(1980, 7, 10),
            password='testpassword123',
            role='teacher'
        )
        self.token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create class, semester, and periods
        self.class_obj = Class.objects.create(class_name='A', grade=3, year=2024)
        self.semester = Semester.objects.create(semester_id='2024-1', year=2024, begin_time='2024-11-26',final_time='2025-06-09',term='A')
        self.period1 = Period.objects.create(period_number=1, begin_time='09:00', end_time='10:00')
        self.period2 = Period.objects.create(period_number=2, begin_time='10:00', end_time='11:00')

    def test_create_course(self):
        """POST course/manage/"""
        url = reverse('course-management')
        data = {
            'course_name': 'Math 101',
            'course_description': 'Basic Mathematics',
            'semester_id': self.semester.semester_id, 
            'class_id': self.class_obj.class_id,
            'periods': [self.period1.id, self.period2.id],
            'day_of_week': 'Monday'
        }

        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('course_id', response.data)

    def test_create_course_conflict(self):
        """POST course/manage/"""
        Course.objects.create(
            course_id='C001',
            course_name='Science 101',
            course_description='Basic Science',
            teacher_id=self.teacher,
            class_id=self.class_obj,
            semester=self.semester,
            day_of_week='Monday'
        ).period.set([self.period1, self.period2])

        # Attempt to create a conflicting course
        url = reverse('course-management')
        data = {
            'course_name': 'Math 102',
            'course_description': 'Advanced Mathematics',
            'semester_id': self.semester.semester_id,
            'class_id': self.class_obj.class_id,
            'periods': [self.period1.id],
            'day_of_week': 'Monday'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Course schedule conflicts with another course.')

    #更新課程
    def test_update_course(self):
        """PUT course/manage/<str:course_id>/"""
        course = Course.objects.create(
            course_name='History 101',
            course_description='World History',
            teacher_id=self.teacher,
            class_id=self.class_obj,
            semester=self.semester,
            day_of_week='Tuesday'
        )
        course.period.set([self.period1])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Update the course details
        url = reverse('course-management-detail', args=[course.course_id])
        data = {
            'course_name': 'Updated History 101',
            'course_description': 'Updated World History',
            'semester_id': self.semester.semester_id,
            'class_id': self.class_obj.class_id,
            'periods': [self.period2.id],
            'day_of_week': 'Wednesday'
        }
        print(course.course_name)
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        course.refresh_from_db()
        print(course.course_name)
        self.assertEqual(course.course_name, 'Updated History 101')
        self.assertEqual(course.day_of_week, 'Wednesday')


    #刪除課程
    def test_delete_course(self):
        """刪除課程 PUT course/manage/<str:course_id>/"""
        course = Course.objects.create(
            course_id='C003',
            course_name='Geography 101',
            course_description='Physical Geography',
            teacher_id=self.teacher,
            class_id=self.class_obj,
            semester=self.semester,
            day_of_week='Thursday'
        )
        course.period.set([self.period1])

        # Delete the course
        url = reverse('course-management-detail', args=[course.course_id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Course.objects.filter(course_id='C003').exists())


class GradeManagementTests(APITestCase):

    def setUp(self):

        # 建立班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=3,
            year=2024
        )
        # 建立一個測試用的老師用戶
        self.teacher_user = User.objects.create_user(
            user_id='T001',
            name='Teacher One',
            birthday='2005-05-15',  # 添加生日字段
            password='0515Test!',
            role='teacher'
        )
        self.teacher_token = str(RefreshToken.for_user(self.teacher_user).access_token)

        # 建立一個測試用的學生用戶
        self.student_user = User.objects.create_user(
            user_id='S001',
            name='Student One',
            birthday='2005-05-15' , # 添加生日字段
            password='0515Test!',
            role='student',
            class_name=self.class_obj
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)



        # 建立學期
        self.semester = Semester.objects.create(semester_id='2024A', year=2024, begin_time='2024-11-26',final_time='2025-06-09',term='A')

        # print(self.semester)

        # 建立節次
        self.period = Period.objects.create(
            period_number=1,
            begin_time='09:00',
            end_time='10:00'
        )

        # 建立課程
        self.course = Course.objects.create(
            course_name='Math',
            course_description='Basic Math Course',
            teacher_id=self.teacher_user,
            class_id=self.class_obj,
            semester=self.semester,
            day_of_week='Monday'
        )
        self.course.period.set([self.period])
        # print(self.course.class_id)
        # 添加學生到課程中
        self.course_score = CourseStudent.objects.filter(
            course_id=self.course.course_id,
        )
        # print(self.course_score)
        self.course_student = CourseStudent.objects.get(
            course_id=self.course,
            student_id=self.student_user
        )

    #輸入課程成績
    def test_input_grades(self):
        """course/<str:course_id>/grade-input/"""
        url = f'/api/course/{self.course.course_id}/grade-input/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        data = {
            'grades': [
                {
                    'student_id': self.student_user.user_id,
                    'middle_score': 80,
                    'final_score': 90
                }
            ]
        }
        response = self.client.put(url, data, format='json')
        # print(response.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.course_student.refresh_from_db()
        self.assertEqual(self.course_student.middle_score, 80)
        self.assertEqual(self.course_student.final_score, 90)
        self.assertEqual(self.course_student.average, 85)

    def test_student_view_grades(self):
        """列出單一學生成績"""  
        url = '/api/student/grades/' 
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['course_name'], 'Math')

    def test_teacher_view_class_grades(self):
        """course/<str:course_id>/class-grades/"""
        url = f'/api/course/{self.course.course_id}/class-grades/'
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        response = self.client.get(url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['student_id'], self.student_user.user_id)
        self.assertEqual(response.data[0]['rank'], 1)

#成績
class GradeViewTests(APITestCase):

    def setUp(self):
        # 建立班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=3,
            year=2024
        )


        # 建立測試學生
        self.student_user = User.objects.create(
            user_id='S001',
            name='Student123',
            birthday= date(2003, 5,15) , # 必須提供生日,
            role='student',
            class_name=self.class_obj
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)
        # Create class, semester, and periods

        self.period1 = Period.objects.create(period_number=1, begin_time='09:00', end_time='10:00')
        self.period2 = Period.objects.create(period_number=2, begin_time='10:00', end_time='11:00')

        # 建立一個測試用的老師用戶
        self.teacher_user = User.objects.create_user(
            user_id='TT01',
            name='Teacher123',
            birthday=date(1980, 7, 15),
            password='testpassword123',
            role='teacher',
            class_name=self.class_obj
        )
        # self.teacher_token = str(RefreshToken.for_user(self.teacher_user).access_token)

        # 建立學期
        self.semester = Semester.objects.create(
            semester_id='2024A', 
            year=2024, 
            begin_time='2024-11-26',
            final_time='2025-06-09',
            term='A')

        self.semester1 = Semester.objects.create(
            semester_id='2024B', 
            year=2025, 
            begin_time='2025-12-26',
            final_time='2026-06-09',
            term='B')

        # 建立課程
        self.course1 = Course.objects.create(
            # course_id='C101',
            course_name='Math',
            teacher_id=self.teacher_user,
            class_id=self.class_obj,
            course_description='Advanced Mathematics',
            semester=self.semester,
            day_of_week='Monday'
        )

        self.course2 = Course.objects.create(
            # course_id=self.student.user_id,
            class_id=self.class_obj,
            teacher_id=self.teacher_user,
            course_name='English',
            course_description='Advanced English',
            semester=self.semester,
            day_of_week='Wednesday'
        )

        update_score = CourseStudent.objects.filter(course_id=self.course1,student_id=self.student_user,semester=self.semester)
        update_score = update_score[0]
        update_score.middle_score=80
        update_score.final_score=90
        update_score.save()
     
        update_score = CourseStudent.objects.filter(course_id=self.course2,student_id=self.student_user,semester=self.semester)
        update_score = update_score[0]
        update_score.middle_score=70
        update_score.final_score=75
        update_score.save()
        

        
        
        # CourseStudent.objects.update(
        #     student_id=self.student_user,
        #     course_id=self.course2,
        #     semester=self.semester,
        #     middle_score=70,
        #     final_score=75,
        #     average=72.5,
        #     rank=2
        # )

    def test_semester_grades(self):
        """測試學期成績查詢"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        url = f'/api/student/semester-grades/{self.semester.semester_id}/'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('grades', response.data)
        self.assertEqual(len(response.data['grades']), 2)  # 應該有兩門課程
        self.assertEqual(response.data['overall_average'], 78.75)  # 總平均分

    def test_all_grades(self):

        """測試歷年成績查詢"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
    
        url = '/api/student/all-grades/'
        response = self.client.get(url)
        # print("API Response:", response.data)  # Debugging line
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('grades_history', response.data)
        self.assertEqual(len(response.data['grades_history']), 1)  # Expected one semester's data
        self.assertEqual(response.data['grades_history'][0]['overall_average'], 78.75)

    def test_all_grades_semester_in(self):
        """測試歷年成績查詢"""


        self.course3 = Course.objects.create(
            class_id=self.class_obj,
            teacher_id=self.teacher_user,
            course_name='English 2',
            course_description='easy English',
            semester=self.semester1,
            day_of_week='Wednesday'
        )

        self.course4 = Course.objects.create(
            class_id=self.class_obj,
            teacher_id=self.teacher_user,
            course_name='Math 2',
            course_description='easy math',
            semester=self.semester1,
            day_of_week='Monday'
        )

        update_score = CourseStudent.objects.filter(course_id=self.course3,student_id=self.student_user,semester=self.semester1)
        update_score = update_score[0]
        update_score.middle_score=80
        update_score.final_score=90
        update_score.save()

        update_score = CourseStudent.objects.filter(course_id=self.course4,student_id=self.student_user,semester=self.semester1)
        update_score = update_score[0]
        update_score.middle_score=88
        update_score.final_score=92
        update_score.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')

        url = '/api/student/all-grades/'
        response = self.client.get(url)
        # print(response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('grades_history', response.data)
        self.assertEqual(len(response.data['grades_history']), 2)  # 應該有兩個學期
        self.assertEqual(response.data['grades_history'][0]['overall_average'], 78.75)  # 第一學期平均分
        self.assertEqual(response.data['grades_history'][1]['overall_average'], 87.5)  # 第二學期平均分