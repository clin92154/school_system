from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import *
from datetime import datetime, timedelta
from rest_framework_simplejwt.tokens import RefreshToken


class LoginTestCase(APITestCase):
    def setUp(self):
        # 建立測試用帳號
        self.student = User.objects.create_user(
            user_id="S001",
            first_name="John",
            last_name="Doe",
            birthday=datetime(2005, 1, 1),
            role="student",
            password="0101Test!"
        )

    def test_valid_login(self):
        """測試使用正確的帳號和密碼進行登入"""
        data = {
            "user_id": "S001",
            "password": "0101Test!"
        }
        response = self.client.post('/api/login/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["role"], "student")
        self.assertEqual(response.data["user_id"], "S001")

    def test_invalid_password(self):
        """測試使用錯誤密碼進行登入"""
        data = {
            "user_id": "S001",
            "password": "wrongpassword"
        }
        response = self.client.post('/api/login/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials")

    def test_missing_password(self):
        """測試遺漏密碼欄位進行登入"""
        data = {
            "user_id": "S001"
        }
        response = self.client.post('/api/login/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_nonexistent_user(self):
        """測試使用不存在的帳號進行登入"""
        data = {
            "user_id": "INVALID001",
            "password": "randompassword"
        }
        response = self.client.post('/api/login/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data["detail"], "Invalid credentials")

    def test_multiple_logins(self):
        """測試同一帳號多次登入"""
        data = {
            "user_id": "S001",
            "password": "0101Test!"
        }
        response1 = self.client.post('/api/login/', data, format="json")
        response2 = self.client.post('/api/login/', data, format="json")

        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertNotEqual(response1.data["access"], response2.data["access"])



class LeaveStatusTestCase(APITestCase):
    def setUp(self):
        # 設定角色（教師與學生）
        self.teacher = User.objects.create_user(
            user_id='T001',
            first_name='Teacher',
            last_name='One',
            birthday=datetime(1980, 1, 1),
            role='teacher',
        )

        self.student = User.objects.create_user(
            user_id='S001',
            first_name='Student',
            last_name='One',
            birthday=datetime(2005, 1, 1),
            role='student',
        )

        self.other_student = User.objects.create_user(
            user_id='S002',
            first_name='Student',
            last_name='Two',
            birthday=datetime(2005, 1, 1),
            role='student',
        )

        # 設定學期與請假類型
        self.semester = Semester.objects.create(
            year=2024,
            term='1',
            begin_time=datetime.now().date(),
            final_time=(datetime.now() + timedelta(days=100)).date()
        )

        self.leave_type = LeaveType.objects.create(type_name='Sick Leave')
        self.period1 = Period.objects.create(period_number=1, begin_time="08:00", end_time="09:00")
        self.period2 = Period.objects.create(period_number=2, begin_time="09:00", end_time="10:00")

        # 設定請假申請
        self.leave_application = LeaveApplication.objects.create(
            student=self.student,
            leave_type=self.leave_type,
            reason="High fever",
            apply_date=datetime.now().date(),
            start_datetime=datetime.now().date(),
            end_datetime=(datetime.now() + timedelta(days=1)).date(),
            status="pending",
        )

        self.leave_application.period.set([self.period1, self.period2])

    def test_list_leave_status_student(self):
        """測試學生是否可以查看自己的請假申請列表"""
        self.token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/list/leaving/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('leave_id', response.data[0])

    def test_list_leave_status_teacher(self):
        """測試教師是否可以查看學生的請假申請列表"""
        self.token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/list/leaving/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_view_leave_detail_student(self):
        """測試學生是否可以查看自己的請假詳情"""
        self.student_token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.student_token}')
        response = self.client.get(f'/api/leaving-detail/{self.leave_application.leave_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['leave_id'], self.leave_application.leave_id)

    def test_view_leave_detail_teacher(self):
        """測試教師是否可以查看其班級學生的請假詳情"""
        self.teacher_token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.teacher_token}')
        response = self.client.get('/api/leaving-detail/' + self.leave_application.leave_id + '/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['leave_id'], self.leave_application.leave_id)

    def test_list_leave_status_empty(self):
        """測試當學生沒有請假申請時是否顯示空列表"""
        self.token = str(RefreshToken.for_user(self.other_student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/list/leaving/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_view_leave_detail_unauthorized_student(self):
        """測試學生是否無法查看其他學生的請假詳情"""
        self.token = str(RefreshToken.for_user(self.other_student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get(f'/api/leaving-detail/{self.leave_application.leave_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_view_leave_detail_nonexistent(self):
        """測試查看不存在的請假申請是否返回404"""
        self.token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        response = self.client.get('/api/leaving-detail/INVALID123/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CourseScheduleTestCase(APITestCase):
    def setUp(self):
        # 建立測試用的角色與數據
        self.teacher = User.objects.create_user(
            user_id="T001",
            first_name="Teacher",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="teacher",
        )

        self.student = User.objects.create_user(
            user_id="S001",
            first_name="Student",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="student",
        )

        self.semester = Semester.objects.create(
            year=2024,
            term="1",
            begin_time=datetime.now().date(),
            final_time=(datetime.now() + timedelta(days=100)).date()
        )

        self.class_a = Class.objects.create(
            class_name="A",
            grade=3,
            teacher_id=self.teacher,
            year=2024
        )

        self.period1 = Period.objects.create(period_number=1, begin_time="08:00", end_time="09:00")
        self.period2 = Period.objects.create(period_number=2, begin_time="09:00", end_time="10:00")

        self.course = Course.objects.create(
            course_id="COURSE001",
            course_name="Mathematics",
            course_description="Basic algebra and geometry.",
            teacher_id=self.teacher,
            class_id=self.class_a,
            semester=self.semester,
            day_of_week="Monday",
        )
        self.course.period.set([self.period1, self.period2])

        self.student.class_name = self.class_a
        self.student.save()

    def test_teacher_view_course_schedule(self):
        """測試教師查看授課課表"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/list/courses/?semester_id={self.semester.semester_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['course_name'], "Mathematics")

    def test_student_view_class_schedule(self):
        """測試學生查看班級課表"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/list/courses/?semester_id={self.semester.semester_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['course_name'], "Mathematics")

    def test_schedule_without_semester_id(self):
        """測試不提供學期 ID 時的錯誤處理(預期錯誤，因為我沒擋:p)"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/list/courses/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_teacher_view_other_class_schedule(self):
        """測試教師無法查看非授課班級的課表"""
        other_teacher = User.objects.create_user(
            user_id="T002",
            first_name="Other",
            last_name="Teacher",
            birthday="1985-01-01",
            role="teacher",
        )
        token = str(RefreshToken.for_user(other_teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/list/courses/?semester_id={self.semester.semester_id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)

    def test_unauthorized_role_view_schedule(self):
        """測試未授權角色（非教師或學生）無法查看課表"""
        admin_user = User.objects.create_user(
            user_id="ADMIN001",
            first_name="Admin",
            last_name="User",
            birthday=datetime(2005, 1, 1),
            role="admin",
        )
        token = str(RefreshToken.for_user(admin_user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/list/courses/?semester_id={self.semester.semester_id}')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)


class StudentGradesTestCase(APITestCase):
    def setUp(self):
        # 建立測試用角色與數據
        self.teacher = User.objects.create_user(
            user_id="T001",
            first_name="Teacher",
            last_name="One",
            birthday=datetime(1980, 1, 1),
            role="teacher",
        )

        self.student_class = Class.objects.create(
            class_name="A",
            grade=3,
            teacher_id=self.teacher,
            year=2024
        )

        self.student = User.objects.create_user(
            user_id="S001",
            first_name="Student",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="student",
            class_name=self.student_class
        )

        self.semester = Semester.objects.create(
            semester_id="2024-1",
            year=2024,
            term="1",
            begin_time=datetime.now().date(),
            final_time=(datetime.now() + timedelta(days=100)).date()
        )

        self.course = Course.objects.create(
            course_name="Mathematics",
            course_description="Basic algebra and geometry.",
            teacher_id=self.teacher,
            class_id=self.student_class,
            semester=self.semester,
            day_of_week="Monday",
        )

        self.course_student = CourseStudent.objects.update(
            course_id=self.course,
            student_id=self.student,
            semester=self.semester,
            middle_score=85.0,
            final_score=90.0,
            average=87.5,
            rank=1
        )

    def test_view_semester_grades(self):
        """測試學生查詢學期成績"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/student/semester-grades/{self.semester.semester_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("grades", response.data)
        self.assertEqual(len(response.data["grades"]), 1)
        self.assertEqual(response.data["grades"][0]["average"], 87.5)

    def test_view_all_grades(self):
        """測試學生查詢歷年成績"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/student/all-grades/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("grades_history", response.data)
        self.assertEqual(len(response.data["grades_history"]), 1)
        self.assertEqual(response.data["grades_history"][0]["overall_average"], 87.5)

    def test_view_nonexistent_semester_grades(self):
        """測試查詢不存在的學期成績"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/student/semester-grades/INVALID/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_unauthorized_role_view_grades(self):
        """測試非學生角色查詢成績被拒絕"""
        admin_user = User.objects.create_user(
            user_id="ADMIN001",
            first_name="Admin",
            last_name="User",
            birthday=datetime(1990, 1, 1),
            role="admin",
        )
        token = str(RefreshToken.for_user(admin_user).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/student/semester-grades/{self.semester.semester_id}/')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_view_semester_with_no_courses(self):
        """測試查詢學期內無課程的成績"""
        new_semester = Semester.objects.create(
            semester_id="2025-1",
            year=2025,
            term="1",
            begin_time=(datetime.now() + timedelta(days=365)).date(),
            final_time=(datetime.now() + timedelta(days=465)).date()
        )
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/student/semester-grades/{new_semester.semester_id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)


class StudentRecordsTestCase(APITestCase):
    def setUp(self):
        # 建立測試用角色與數據
        self.teacher = User.objects.create_user(
            user_id="T001",
            first_name="Teacher",
            last_name="One",
            birthday=datetime(1980, 1, 1),
            role="teacher",
        )

        self.student_class = Class.objects.create(
            class_name="A",
            grade=3,
            teacher_id=self.teacher,
            year=2024
        )

        self.student = User.objects.create_user(
            user_id="S001",
            first_name="Student",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="student",
            class_name=self.student_class
        )

    def test_list_class(self):
        """測試查詢班級列表"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/list/class/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['class_name'], "A")

    def test_list_students_in_class(self):
        """測試查詢班級學生列表"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/class/{self.student_class.class_id}/students/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['user_id'], self.student.user_id)

    def test_view_student_detail(self):
        """測試查詢指定學生詳細資料"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/students/{self.student.user_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['user_id'], self.student.user_id)
        self.assertEqual(response.data['class_info']['class_name'], "A")

    def test_list_students_in_nonexistent_class(self):
        """測試查詢不存在的班級學生列表"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/class/INVALID/students/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_view_nonexistent_student_detail(self):
        """測試查詢不存在的學生詳細資料"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/students/INVALID/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)


class LeaveApprovalTestCase(APITestCase):
    def setUp(self):
        # 建立測試用角色與數據
        self.teacher = User.objects.create_user(
            user_id="T001",
            first_name="Teacher",
            last_name="One",
            birthday=datetime(1980, 1, 1),
            role="teacher",
        )

        self.student = User.objects.create_user(
            user_id="S001",
            first_name="Student",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="student",
        )

        self.leave_type = LeaveType.objects.create(type_name="Sick Leave")
        self.period1 = Period.objects.create(period_number=1, begin_time="08:00", end_time="09:00")
        self.period2 = Period.objects.create(period_number=2, begin_time="09:00", end_time="10:00")

        self.leave_application = LeaveApplication.objects.create(
            leave_id="2024010101S001",
            student=self.student,
            leave_type=self.leave_type,
            reason="Fever",
            apply_date=datetime.now().date(),
            start_datetime=datetime(2024, 1, 1, 8, 0),
            end_datetime=datetime(2024, 1, 1, 18, 0),
            status="pending",
        )
        self.leave_application.period.set([self.period1, self.period2])

    def test_submit_leave_application(self):
        """測試學生提交請假申請"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "leave_type": self.leave_type.type_name,
            "reason": "Fever",
            "start_datetime": "2024-01-01T08:00:00",
            "end_datetime": "2024-01-01T18:00:00",
            "period": [self.period1.id, self.period2.id]
        }
        response = self.client.post('/api/leaving-application/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("leave_id", response.data)

    def test_view_leave_detail_teacher(self):
        """測試教師查詢請假詳情"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/leaving-detail/{self.leave_application.leave_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["leave_id"], self.leave_application.leave_id)

    def test_approve_leave_application(self):
        """測試教師審核請假申請"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "status": "approved",
            "remark": "Approved due to valid medical certificate."
        }
        response = self.client.post(f'/api/leave-approval/{self.leave_application.leave_id}/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "請假申請審核完成")

    def test_student_cannot_approve_leave(self):
        """測試學生無權審核請假申請"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "status": "approved",
            "remark": "Invalid action."
        }
        response = self.client.post(f'/api/leave-approval/{self.leave_application.leave_id}/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn("detail", response.data)

    def test_invalid_leave_application_detail(self):
        """測試查詢不存在的請假詳情"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/leaving-detail/INVALID123/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)

    def test_invalid_leave_application_time(self):
        """測試無效的請假時間"""
        token = str(RefreshToken.for_user(self.student).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "leave_type": self.leave_type.type_name,
            "reason": "Error Test",
            "start_datetime": "2024-01-01T18:00:00",
            "end_datetime": "2024-01-01T08:00:00",
            "period": [self.period1.id, self.period2.id]
        }
        response = self.client.post('/api/leaving-application/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

class CourseGradesTestCase(APITestCase):
    def setUp(self):
        # 建立測試用角色與數據
        self.teacher = User.objects.create_user(
            user_id="T001",
            first_name="Teacher",
            last_name="One",
            birthday=datetime(1980, 1, 1),
            role="teacher",
        )

        self.student_class = Class.objects.create(
            class_name="A",
            grade=3,
            teacher_id=self.teacher,
            year=2024
        )

        self.student1 = User.objects.create_user(
            user_id="S001",
            first_name="Student",
            last_name="One",
            birthday=datetime(2005, 1, 1),
            role="student",
            class_name=self.student_class
        )

        self.student2 = User.objects.create_user(
            user_id="S002",
            first_name="Student",
            last_name="Two",
            birthday=datetime(2005, 2, 2),
            role="student",
            class_name=self.student_class
        )



        # 將學生分配到班級
        self.student1.class_name = self.student_class
        self.student1.save()

        self.student2.class_name = self.student_class
        self.student2.save()

        self.semester = Semester.objects.create(
            semester_id="2024-1",
            year=2024,
            term="1",
            begin_time=datetime.now().date(),
            final_time=(datetime.now() + timedelta(days=100)).date()
        )

        self.course = Course.objects.create(
            course_name="Mathematics",
            course_description="Basic algebra and geometry.",
            teacher_id=self.teacher,
            class_id=self.student_class,
            semester=self.semester,
            day_of_week="Monday",
        )


        self.invalidteacher = User.objects.create_user(
            user_id="T002",
            first_name="Teacher",
            last_name="two",
            birthday=datetime(1980, 1, 1),
            role="teacher",
        )


        self.invalidcourse = Course.objects.create(
            course_name='invalid course',
            course_description="Basic algebra and geometry.",
            class_id=self.student_class,
            teacher_id=self.invalidteacher,
            semester=self.semester,
            day_of_week="Monday",
        )

    def test_course_creation_creates_course_students(self):
        """測試課程建立後，自動為班級內學生創建成績表"""
        course_students = CourseStudent.objects.filter(course_id=self.course)
        self.assertEqual(course_students.count(), 2)  # 班級內有兩名學生
        self.assertTrue(CourseStudent.objects.filter(course_id=self.course, student_id=self.student1).exists())
        self.assertTrue(CourseStudent.objects.filter(course_id=self.course, student_id=self.student2).exists())

    def test_teacher_view_courses(self):
        """測試教師查詢課程列表"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get('/api/list/courses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['course_id'], self.course.course_id)

    def test_teacher_view_class_grades(self):
        """測試教師查詢課程班級成績"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/course/{self.course.course_id}/class-grades/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_teacher_input_grades(self):
        """測試教師輸入課程成績"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        data = {
            "grades": [
                {
                    "student_id": self.student1.user_id,
                    "middle_score": 80.0,
                    "final_score": 85.0
                },
                {
                    "student_id": self.student2.user_id,
                    "middle_score": 70.0,
                    "final_score": 75.0
                }
            ]
        }
        response = self.client.put(f'/api/course/{self.course.course_id}/grade-input/', data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['detail'], "Grades updated successfully.")
        # 驗證成績是否更新
        course_student1 = CourseStudent.objects.get(course_id=self.course, student_id=self.student1)
        course_student2 = CourseStudent.objects.get(course_id=self.course, student_id=self.student2)
        self.assertEqual(course_student1.middle_score, 80.0)
        self.assertEqual(course_student2.final_score, 75.0)
    def test_teacher_view_invalid_class_grades(self):
        """測試教師查詢非授課課程成績被拒"""
        token = str(RefreshToken.for_user(self.teacher).access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(f'/api/course/{self.invalidcourse.course_id}/class-grades/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("detail", response.data)


