from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import *
urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('reset/password/', ResetPasswordView.as_view(), name='reset-password'),
    path('profile/', UserProfileView.as_view(), name='profile-settings'),
    path('user-info/', UserInfoView.as_view(), name='user_info'),
    path('gruadian/', GuardianView.as_view()),  #請假列表
    path('leaving-application/', LeaveApplicationView.as_view(), name='leave-application'), #申請
    path('leaving-detail/<str:leave_id>/', LeaveDetailView.as_view(), name='leaving-detail'),  #詳細
    path('leave-approval/<str:leave_id>', LeaveApprovalView.as_view(), name='leave-approval'),#審核
    path('list/leaving/', LeaveListView.as_view()),  #請假列表
    path('list/leave-type/', LeaveTypeListView.as_view()),
    path('list/period/', PeriodListView.as_view()), 
    path('list/class/', ClassListView.as_view(), name='class-list'),
    path('list/days-of-week/', DaysOfWeekView.as_view(), name='days-of-week'),
    path('list/semester/', SemesterListView.as_view(), name='semester-list'),
    path('list/courses/', CourseListView.as_view(), name='semester-list'),
    path('class/<str:class_id>/students/', ClassStudentListView.as_view(), name='class-student-list'), # 班級學生清單,
    path('students/<str:student_id>/', StudentDetailView.as_view(), name='student-detail'), # 指定學生詳細資料
    path('course/manage/', CourseManagementView.as_view(), name='course-management'), #管理課程資料
    path('course/manage/<str:course_id>/', CourseManagementView.as_view(), name='course-management-detail'), #管理課程資料
    path('course/<str:course_id>/grade-input/', CourseGradeInputView.as_view(), name='course-grade-input'), #輸入儲存班級學生的成績
    path('course/<str:course_id>/class-grades/', ClassGradeRankView.as_view(), name='class-grade-rank-view'), #列出課程的所屬班級
    path('student/grades/', StudentGradeView.as_view(), name='student-grade-view'),
    path('student/semester-grades/<str:semester_id>/', SemesterGradeView.as_view(), name='semester-grade-view'),
    path('student/all-grades/', AllSemesterGradeView.as_view(), name='all-semester-grade-view')
]


