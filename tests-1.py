from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import *
from datetime import datetime, timedelta, date
from rest_framework_simplejwt.tokens import RefreshToken

class AuthenticationTests(APITestCase):
    def setUp(self):
        # 建立測試用戶
        self.user = User.objects.create(
            user_id='T111',
            name='Teacher 1',
            birthday=date(1990, 5, 3),
            role='teacher'
        )
        self.user.save()

    def test_login(self):
        """測試登入功能"""
        url = '/api/login/'
        data = {'user_id': 'T111', 'password': '0503Test!'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('role', response.data)
        self.assertEqual(response.data['user_id'], 'T111')

    def test_logout(self):
        """測試登出功能"""
        # 先登入獲取 token
        login_url = '/api/login/'
        login_data = {'user_id': 'T111', 'password': '0503Test!'}
        login_response = self.client.post(login_url, login_data, format='json')
        
        # 確保登入成功
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # 獲取 token
        access_token = login_response.data['access']
        refresh_token = login_response.data['refresh']

        # 測試登出
        logout_url = '/api/logout/'
        logout_data = {'refresh': refresh_token}
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        response = self.client.post(logout_url, logout_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

class ResetPasswordTests(APITestCase):
    def setUp(self):
        # 建立測試用戶
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
        """試重設密碼"""
        url = '/api/reset/password/'
        data = {'new_password': 'newpassword789'}
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newpassword789'))

class GradeManagementTests(APITestCase):
    def setUp(self):
        # 建立班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=3,
            year=2024
        )
        
        # 建立教師用戶
        self.teacher_user = User.objects.create_user(
            user_id='T001',
            name='Teacher One',
            birthday=date(1996, 5, 15),
            role='teacher'
        )
        self.teacher_token = str(RefreshToken.for_user(self.teacher_user).access_token)

        # 建立學生用戶
        self.student_user = User.objects.create_user(
            user_id='S001',
            name='Student One',
            birthday=date(1996, 5, 15),
            password='0515Test!',
            role='student',
            class_name=self.class_obj
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)

        # 建立學期
        self.semester = Semester.objects.create(
            semester_id='2024A', 
            year=2024, 
            begin_time='2024-11-26',
            final_time='2025-06-09',
            term='A'
        )

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

        # 獲取課程學生關係
        self.course_score = CourseStudent.objects.filter(
            course_id=self.course.course_id,
        )
        self.course_student = CourseStudent.objects.get(
            course_id=self.course,
            student_id=self.student_user
        )

    def test_input_grades(self):
        """測試成績輸入"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        url = f'/api/course/{self.course.course_id}/grade-input/'
        data = {
            'grades': [
                {
                    'student_id': self.student_user.user_id,
                    'middle_score': 85,
                    'final_score': 90
                }
            ]
        }
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GradeViewTests(APITestCase):
    def setUp(self):
        # 建立班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=3,
            year=2024
        )

        # 建立學生
        self.student_user = User.objects.create(
            user_id='S001',
            name='Student123',
            birthday=date(2003, 5, 15),
            role='student',
            class_name=self.class_obj
        )
        self.student_token = str(RefreshToken.for_user(self.student_user).access_token)

        # 建立節次
        self.period1 = Period.objects.create(period_number=1, begin_time='09:00', end_time='10:00')
        self.period2 = Period.objects.create(period_number=2, begin_time='10:00', end_time='11:00')

class LeaveModuleTests(APITestCase):
    def setUp(self):
        # 建立測試數據
        self.student = User.objects.create_user(
            user_id='S001', 
            name='Student',
            birthday=date(2000, 1, 1),
            role='student'
        )
        self.teacher = User.objects.create_user(
            user_id='T001', 
            name='Teacher',
            birthday=date(1990, 1, 1),
            role='teacher'
        )
        self.leave_type = LeaveType.objects.create(type_name='病假')
        self.token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_leave_application(self):
        """測試請假申請"""
        url = '/api/leaving-application/'
        data = {
            'leave_type': self.leave_type.id,
            'reason': '身體不適',
            'start_datetime': date(2024, 3, 20),
            'end_datetime': date(2024, 3, 21),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_leave_detail(self):
        """測試請假詳情"""
        # 先建立請假記錄
        leave = LeaveApplication.objects.create(
            student=self.student,
            leave_type=self.leave_type,
            reason='測試請假'
        )
        url = f'/api/leaving-detail/{leave.leave_id}/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_leave_approval(self):
        """測試請假審核"""
        # 切換到教師身份
        self.token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        
        leave = LeaveApplication.objects.create(
            student=self.student,
            leave_type=self.leave_type,
            reason='測試請假'
        )
        url = f'/api/leave-approval/{leave.leave_id}'
        data = {'status': 'approved', 'remark': '同意請假'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ListModuleTests(APITestCase):
    def setUp(self):
        # 建立基本測試數據
        self.teacher = User.objects.create_user(
            user_id='T001', 
            name='Teacher', 
            birthday=date(1990, 1, 1),  # 使用 date 物件
            role='teacher'
        )
        self.student = User.objects.create_user(
            user_id='S001', 
            name='Student', 
            birthday=date(2000, 1, 1),  # 使用 date 物件
            role='student'
        )
        self.token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # 建立測試用的類別
        self.category = Category.objects.create(
            name='測試類別',
            roles='teachers'
        )

        # 建立測試用的請假類型
        self.leave_type = LeaveType.objects.create(
            type_name='事假'
        )

        # 建立測試用的班級
        self.class_obj = Class.objects.create(
            class_name='A',
            grade=1,
            year=2024
        )

        # 建立測試用的學期
        self.semester = Semester.objects.create(
            year=2024,
            term='A',
            begin_time='2024-02-01',
            final_time='2024-06-30'
        )

        # 建立測試用的節次
        self.period = Period.objects.create(
            period_number=1,
            begin_time='08:00',
            end_time='09:00'
        )

    def test_category_list(self):
        """測試功能類別列表"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        url = '/api/categories/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)

    def test_leave_type_list(self):
        """測試請假類型列表"""
        url = '/api/list/leave-type/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['type_name'], '事假')

    def test_period_list(self):
        """測試節次列表"""
        url = '/api/list/period/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['period_number'], 1)

    def test_class_list(self):
        """測試班級列表"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        url = '/api/list/class/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['class_name'], 'A')

    def test_days_of_week(self):
        """測試星期列表"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        url = '/api/list/days-of-week/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 7)
        self.assertIn('Monday', response.data)

    def test_semester_list(self):
        """測試學期列表"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        url = '/api/list/semester/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data) > 0)
        self.assertEqual(response.data[0]['semester_id'], '2024-A')


    def test_get_class_list(self):
        """測試獲取班級列表"""
        # 建立額外的測試班級
        Class.objects.create(
            class_name='B',
            grade=1,
            year=2024
        )
        
        url = '/api/classes/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        class_names = [c['class_name'] for c in response.data]
        self.assertTrue('A' in class_names)
        self.assertTrue('B' in class_names)

    def test_get_semester_list(self):
        """測試獲取學期列表"""
        # 建立額外的測試學期
        Semester.objects.create(
            semester_id='2024B',
            year=2024,
            term='B',
            begin_time='2024-02-01',
            final_time='2024-06-30'
        )
        
        url = '/api/semesters/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        semester_ids = [s['semester_id'] for s in response.data]
        self.assertTrue('2024A' in semester_ids)
        self.assertTrue('2024B' in semester_ids)

class ProfileModuleTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            user_id='U001', 
            name='Test User',
            birthday=date(1990, 1, 1),  # 使用 date 物件
            role='student'
        )
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
    def test_user_profile(self):
        """測試個人檔案查看"""
        url = '/api/profile/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_info(self):
        """測試用戶資訊"""
        url = '/api/user-info/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_guardian_info(self):
        """測試監護人資訊"""
        # 先建立監護人
        guardian = Guardian.objects.create(
            student=self.user,
            name='測試監護人',
            phone_number='0912345678',
            relationship='父親',
            address='測試地址123號'
        )
        
        url = '/api/guardian/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

class GuardianTests(APITestCase):
    def setUp(self):
        # 建立測試學生用戶
        self.student = User.objects.create_user(
            user_id='S001',
            name='Test Student',
            birthday=date(2000, 1, 1),
            role='student'
        )
        self.token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

    def test_create_guardian(self):
        """測試建立監護人資料"""
        url = '/api/guardian/'
        data = {
            'name': '測試監護人',
            'phone_number': '0912345678',
            'relationship': '父親',
            'address': '測試地址123號'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('guardian_id', response.data)
        self.assertEqual(Guardian.objects.count(), 1)

    def test_get_guardian(self):
        """測試獲取監護人資料"""
        # 先建立監護人資料
        guardian = Guardian.objects.create(
            student=self.student,
            name='測試監護人',
            phone_number='0912345678',
            relationship='父親',
            address='測試地址123號'
        )
        
        url = '/api/guardian/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], '測試監護人')
        self.assertEqual(response.data['phone_number'], '0912345678')

    def test_update_guardian(self):
        """測試更新監護人資料"""
        # 先建立監護人資料
        guardian = Guardian.objects.create(
            student=self.student,
            name='測試監護人',
            phone_number='0912345678',
            relationship='父親',
            address='測試地址123號'
        )
        
        url = '/api/guardian/'
        update_data = {
            'name': '新監護人',
            'phone_number': '0987654321',
            'relationship': '母親',
            'address': '新測試地址456號'
        }
        response = self.client.post(url, update_data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 驗證資料是否更新成功
        guardian.refresh_from_db()
        self.assertEqual(guardian.name, '新監護人')
        self.assertEqual(guardian.phone_number, '0987654321')
        self.assertEqual(guardian.relationship, '母親')
        self.assertEqual(guardian.address, '新測試地址456號')

class CourseManagementTests(APITestCase):
    """課程管理模組測試 (Course Management Tests)"""
    def setUp(self):
        # 建立基本測試數據
        self.class_obj = Class.objects.create(
            class_name='A', 
            grade=1, 
            year=2024
        )
        self.teacher = User.objects.create_user(
            user_id='T001', 
            name='Teacher',
            birthday=date(1990, 1, 1),  # 使用 date 物件
            role='teacher'
        )
        self.student = User.objects.create_user(
            user_id='S001', 
            name='Student',
            birthday=date(2000, 1, 1),  # 使用 date 物件
            role='student',
            class_name=self.class_obj
        )
        self.semester = Semester.objects.create(
            semester_id='2024A',
            year=2024,
            term='A'
        )
        self.token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')