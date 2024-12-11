from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management import CommandError
from user.models import User

class Command(BaseCommand):
    help = '創建超級用戶'

    def add_arguments(self, parser):
        parser.add_argument('--user_id', required=True, help='指定超級用戶的 ID')
        parser.add_argument('--first_name', required=True, help='指定超級用戶的姓')
        parser.add_argument('--last_name', required=True, help='指定超級用戶的名')
        parser.add_argument('--password', required=True, help='指定超級用戶的密碼')
        parser.add_argument('--birthday', required=True, help='指定超級用戶的密碼')

    def handle(self, *args, **options):
        user_id = options['user_id']
        first_name = options['first_name']
        last_name = options['last_name']
        password = options['password']
        birthday = options['birthday']
        if User.objects.filter(user_id=user_id).exists():
            raise CommandError(f'user_id "{user_id}" is exist！')

        User.objects.create_superuser(user_id=user_id, first_name=first_name,last_name=last_name, password=password,birthday=birthday)
        self.stdout.write(self.style.SUCCESS(f'superuser "{user_id}" created successfully'))
