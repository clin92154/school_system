# 創建功能分類的指令
from django.core.management.base import BaseCommand
from user.models import *
class Command(BaseCommand):
    help = '創建功能分類和子分類'

    def handle(self, *args, **options):
        # 老師功能分類
        query = Category.objects.create(name='查詢',url='search')
        Category.objects.create(name='學生檔案', roles='teachers', parent_category=query,url='profile/students')
        Category.objects.create(name='課表', parent_category=query,url='class/schedule')
        Category.objects.create(name='歷年成績', roles='students', parent_category=query,url='class/schedule')
        Category.objects.create(name='個人成績', roles='students', parent_category=query,url='score/history')
        Category.objects.create(name='班級課表', roles='students', parent_category=query,url='score')
        Category.objects.create(name='請假狀態', roles='students', parent_category=query,url='leaving/status/')
        Category.objects.create(name='假單審核', roles='teachers', parent_category=query,url='leaving/approving/')


        register = Category.objects.create(name='登錄', roles='teachers',url='register')
        Category.objects.create(name='課程成績登錄', roles='teachers', parent_category=register,url='score')

        settings = Category.objects.create(name='設定',url='setting')
        Category.objects.create(name='課程管理', parent_category=settings,url='course/manage')
        Category.objects.create(name='更改密碼', parent_category=settings,url='reset-password')
        Category.objects.create(name='個人檔案', parent_category=settings,url='profile')

        # 學生功能分類

        student_apply = Category.objects.create(name='申請', roles='student',url='apply')
        Category.objects.create(name='假單申請', roles='student', parent_category=student_apply,url='leaving')


        self.stdout.write(self.style.SUCCESS('功能分類和子分類已成功創建'))