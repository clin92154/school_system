from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from .models import *
from django.urls import reverse
from django.utils.html import format_html


class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('user_id', 'name', 'first_name', 'last_name', 'role', 'is_active', 'birthday', 'semester')
    list_filter = ('role', 'is_active')
    fieldsets = (
        (None, {'fields': ('user_id', 'name', 'first_name', 'last_name', 'password', 'birthday', 'role', 'gender', 'class_name', 'semester')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('user_id', 'name', 'first_name', 'last_name', 'gender', 'birthday', 'role', 'is_active')}
        ),
    )
    search_fields = ('user_id', 'name', 'first_name', 'last_name',)
    ordering = ('user_id',)

    def save_model(self, request, obj, form, change):
        # 如果是新建用戶且未設置密碼
        if not change and not obj.password:
            # 使用生日的月份和日期作為密碼的一部分
            month_day = obj.birthday.strftime("%m%d")
            default_password = f"{month_day}test!"  # 符合密碼規則的預設密碼
            obj.set_password(default_password)
        super().save_model(request, obj, form, change)

        # 自動分配群組
        if obj.role == 'admin':
            group = Group.objects.get(name='admins')
        if obj.role == 'teacher':
            group = Group.objects.get(name='teachers')
        elif obj.role == 'student':
            group = Group.objects.get(name='students')
        else:
            group = None

        if group:
            obj.groups.set([group])  # 清除現有群組並分配新群組
            obj.save()

class ClassAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
            form = super().get_form(request, obj, **kwargs)
            form.base_fields['class_id'].required = False  # 設置 semester_id 為非必填
            return form
    list_display = ('class_id', 'class_name', 'grade', 'teacher_id', 'year')
    search_fields = ('class_id', 'class_name', 'grade', 'year')
    ordering = ('year', 'grade', 'class_name')

class SemesterAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['semester_id'].required = False  # 設置 semester_id 為非必填
        return form
    list_display = ('semester_id', 'year', 'term')
    search_fields = ('semester_id', 'year')
    ordering = ('year', 'term')    
    
class CourseAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['course_id'].required = False  # 設置 semester_id 為非必填
        return form
    list_display = ('course_id', 'course_name', 'teacher_id', 'class_id', 'semester')
    search_fields = ('course_id', 'course_name', 'teacher_id__name', 'class_id__class_name')
    ordering = ('semester', 'course_id')

class CourseStudentAdmin(admin.ModelAdmin):
    list_display = ('course_id', 'student_id', 'semester', 'middle_score', 'final_score', 'average', 'rank')
    search_fields = ('course_id__course_name', 'student_id__name', 'semester__semester_id')
    ordering = ('semester', 'course_id', 'student_id')


class LeaveTypeAdmin(admin.ModelAdmin):
    list_display = ('type_name', )
    search_fields = ('type_name', )
    ordering =('type_name', )



class LeaveApplicationAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.base_fields['leave_id'].required = False  # 設置 semester_id 為非必填
        return form
    list_display = ('leave_id','student', 'leave_type', 'apply_date', 'status', 'approved_by')
    search_fields = ('leave_id', 'student__name', 'leave_type', 'status')
    ordering = ('apply_date', 'status')
    

class GuardianAdmin(admin.ModelAdmin):
    list_display = ('guardian_id', 'name', 'phone_number', 'relationship', 'address')
    search_fields = ('guardian_id__user_id', 'name', 'phone_number', 'relationship')
    ordering = ('name',)

class SubCategoryInline(admin.TabularInline):
    model = Category
    extra = 0

class CategoryAdmin(admin.ModelAdmin):
    inlines = [SubCategoryInline]
    list_display = ('name', 'parent_category', 'roles',)
    search_fields = ('parent_category__name', 'name', 'roles__name')
    ordering = ('parent_category', 'roles', 'name')


admin.site.register(User, CustomUserAdmin)
admin.site.register(Class, ClassAdmin)
admin.site.register(Semester, SemesterAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(CourseStudent, CourseStudentAdmin)
admin.site.register(LeaveApplication, LeaveApplicationAdmin)
admin.site.register(Guardian, GuardianAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(LeaveType,LeaveTypeAdmin)
admin.site.register(Period)