from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from datetime import datetime
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.crypto import get_random_string

# 自定義 User Manager
class UserManager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, user_id, first_name,last_name, birthday, password=None, **extra_fields):
        if not user_id:
            raise ValueError('The User ID must be set')
        user = self.model(user_id=user_id, first_name=first_name,last_name=last_name, birthday=birthday, **extra_fields)
        # 確保 birthday 是 datetime 物件
        if isinstance(birthday, str):
            birthday = datetime.strptime(birthday, "%Y-%m-%d").date()

        user = self.model(user_id=user_id, first_name=first_name, last_name=last_name, birthday=birthday, **extra_fields)
        if not password:
            # 使用生日的月份和日期作為密碼的一部分
            month_day = birthday.strftime("%m%d")
            default_password = f"{month_day}Test!"  # 符合密碼規則的預設密碼
            user.set_password(default_password)
        else:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, user_id, first_name,last_name, birthday, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(user_id, first_name,last_name, birthday, password, **extra_fields)

# 自定義 User 模型
class User(AbstractUser):
    user_id = models.CharField(max_length=20, unique=True)  # 學號或員工編號
    name = models.CharField(max_length=20)  # 用戶
    birthday = models.DateField()  # 生日
    eng_name = models.CharField(max_length=20, null=True, blank=True)  # 英文
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE, null=True, blank=True)  # 入職、入學學期
    role = models.CharField(max_length=10, choices=[('admin', 'Admin'), ('student', 'Student'), ('teacher', 'Teacher')])
    gender = models.CharField(max_length=10, choices=[('male', '男生'), ('female', '女生')])  # 性別
    class_name=models.ForeignKey('Class', on_delete=models.SET_NULL, null=True, blank=True)  # 所屬班級，選擇為 ForeignKey
    email = None  # 排除掉 email 欄位
    username = None  # 排除掉username
    USERNAME_FIELD = 'user_id'
    REQUIRED_FIELDS = ['birthday']

    objects = UserManager()
    def set_password(self, raw_password):
        """覆蓋 set_password 方法，確保密碼驗證"""
        if raw_password:
            validate_password(raw_password, self)  # 驗證密碼是否符合規範
        super().set_password(raw_password)

    def save(self, *args, **kwargs):
        self.name =f"{self.first_name}{self.last_name}"
        if not self.pk and not self.password:  # 如果是新建用戶或未設置密碼
            # 使用生日的月份和日期作為密碼的一部分
            month_day = self.birthday.strftime("%m%d")
            default_password = f"{month_day}Test!"  # 符合密碼規則的預設密碼
            self.set_password(default_password)
        else:
            try:
                validate_password(self.password, self)  # 驗證密碼是否符合規範（僅對已存在用戶）
            except ValidationError as e:
                raise ValueError(f"Password validation error: {e}")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.user_id

# 班級模型
class Class(models.Model):
    
    # 確保班級名稱只能是單一的字母 A 到 Z
    class_name = models.CharField(
        max_length=1,
        validators=[RegexValidator(regex='^[A-Z]$', message='Class name must be a single uppercase letter from A to Z.')]
    )
    class_id = models.CharField(max_length=10, primary_key=True)  # 班級 ID
    grade = models.PositiveIntegerField(choices=[(i, f"{i} 年級") for i in range(1, 7)])  # 年級，從 1 到 6
    teacher_id = models.OneToOneField(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='teacher_class')  # 班導師
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1900),  # 最小年份限制（可依需求修改）
            MaxValueValidator(datetime.now().year)  # 最大年份限制為當前年份
        ],
        help_text="請輸入年份，例如 2024"
    )

    def save(self, *args, **kwargs):
        
        # 自動生成 class_id，結合 semester, class_name
        self.class_id = f"{self.year}-{self.class_name}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.grade} 年級 {self.class_name} 班"

# 學期模型
class Semester(models.Model):
    semester_id = models.CharField(max_length=10, primary_key=True)  # 學期 ID，如 2023-1 表示 2023 年第一學期
    year = models.PositiveIntegerField(
        validators=[
            MinValueValidator(1900),  # 最小年份限制（可依需求修改）
            # MaxValueValidator(datetime.now().year)  # 最大年份限制為當前年份
        ],
        help_text="請輸入年份，例如 2024"
    )    
    term = models.CharField(max_length=10, choices=[('1', '第一學期'), ('2', '第二學期')])  # 學期名稱，如第一學期或第二學期
    begin_time = models.DateField(null=True, blank=True)  # 開始時間
    final_time = models.DateField(null=True, blank=True)  # 結束時間
    
    def save(self, *args, **kwargs):
        if self.final_time is not None and self.begin_time is not None:

            # 自動生成 semester_id，結合 year 和 term
            if self.final_time> self.begin_time:
                self.semester_id = f"{self.year}-{self.term}"
                super().save(*args, **kwargs)
                

    def __str__(self):
        return f"{self.year} - {self.get_term_display()}"

# 課程模型
class Course(models.Model):
    """course_id,course_name,course_description,class_id,period,semester"""
    course_id = models.CharField(max_length=20, primary_key=True)  # 課程 ID
    course_name = models.CharField(max_length=50)  # 課程名稱
    course_description = models.TextField(blank=True, null=True)  # 課程描述
    teacher_id = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})  # 授課老師
    class_id = models.ForeignKey(Class, on_delete=models.CASCADE)  # 所屬班級
    period = models.ManyToManyField('Period')  # 授課時段
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)  # 學期
    day_of_week = models.CharField(max_length=10, choices=[('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')])  # 星期幾

    def __str__(self):
        return f"{self.course_name} ({self.course_id})"

    def save(self, *args, **kwargs):
        # 自動生成 course_id
        if not(self.course_id):
            self.course_id = get_random_string(length=8).upper()

        super().save(*args, **kwargs)
        # 自動為該班級的每個學生創建成績表
        students = User.objects.filter(role='student', class_name=self.class_id)
        for student in students:
            CourseStudent.objects.get_or_create(course_id=self, student_id=student, semester=self.semester)

# 課程學生模型
class CourseStudent(models.Model):
    course_id = models.ForeignKey(Course, on_delete=models.CASCADE)  # 課程 ID
    student_id = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})  # 學生 ID
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)  # 學期
    middle_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # 期中成績
    final_score = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # 期末成績
    average = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)  # 平均成績
    rank = models.PositiveIntegerField(blank=True, null=True)  # 排名

    def __str__(self):
        return f"{self.student_id} in {self.course_id}"

    def save(self, *args, **kwargs):
        # 自動生成 course_id
        if self.middle_score and self.final_score:
            self.average = (self.middle_score+self.final_score)/2
        else:
            self.average = None
        super().save(*args, **kwargs)

class LeaveType(models.Model):
    type_name = models.CharField(max_length=10)  # 請假類型名稱

    def __str__(self):
        return self.type_name

class Period(models.Model):
    period_number = models.PositiveIntegerField()  # 第幾節次
    begin_time = models.TimeField(null=True, blank=True)  # 開始時間
    end_time = models.TimeField(null=True, blank=True)  # 結束時間

    def __str__(self):
        return f"第 {self.period_number} 節 ({self.begin_time} - {self.end_time})"

class LeaveApplication(models.Model):
    leave_id = models.CharField(max_length=20, primary_key=True)  # 請假 ID
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})  # 學生
    guardian = models.OneToOneField('Guardian', on_delete=models.CASCADE, null=True, blank=True)  # 監護人
    leave_type = models.ForeignKey(LeaveType, on_delete=models.CASCADE)  # 請假類型
    period = models.ManyToManyField(Period)  # 請假節次
    reason = models.TextField(max_length=255)  # 請假原因
    apply_date = models.DateField(default=timezone.now)  # 申請日期
    start_datetime = models.DateField(null=True, blank=True)  # 請假開始日期和時間
    end_datetime = models.DateField(null=True, blank=True)  # 請假結束日期和時間
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves', limit_choices_to={'role': 'teacher'})  # 審批人
    approved_date = models.DateField(blank=True, null=True)  # 審批日期
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')],default='pending')  # 審批狀態
    remark = models.TextField(blank=True, null=True)  # 備註

    def __str__(self):
        return f"Leave Application {self.leave_id}"
    
    def save(self, *args, **kwargs):
        # 自動生成 semester_id，結合 year 和 term
            if not self.pk:
                cnt = len(LeaveApplication.objects.filter(apply_date=self.apply_date))
                self.leave_id = f"{self.apply_date.strftime('%Y%m%d')}{self.leave_type.id}{self.student}{cnt}"
            super().save(*args, **kwargs)

class Guardian(models.Model):
    guardian_id = models.CharField(max_length=50, unique=True, editable=False, primary_key=True)  # 監護人 ID
    student = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'}, null=True, blank=True)  # 所屬學生
    name = models.CharField(max_length=20)  # 監護人姓名
    phone_number = models.CharField(max_length=20)  # 電話號碼
    relationship = models.CharField(max_length=10)  # 與學生的關係
    address = models.TextField()  # 地址
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.guardian_id = f"g{self.student.user_id}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.relationship})"


# 功能分類模型
class Category(models.Model):
    name = models.CharField(max_length=20)  # 功能分類名稱
    roles = models.CharField(max_length=20, choices=[('teachers', 'Teachers'),('students', 'Students')],null=True,blank=True)  # 審批狀態
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')  # 父分類，可選
    url = models.CharField(max_length=100,blank=True,null=True)

    def __str__(self):
        return f"{self.name} ({self.roles})"
