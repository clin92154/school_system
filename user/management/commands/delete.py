from user.models import *
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Delete all data from a specific model'

    def handle(self, *args, **kwargs):
        try:
            # 刪除所有資料
            deleted_count, _ = LeaveApplication.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Successfully deleted {deleted_count} records from {LeaveApplication._meta.model_name}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error occurred: {e}'))
