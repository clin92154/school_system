from django.contrib.auth.management.commands.createsuperuser import Command as BaseCreateSuperuserCommand
from django.core.management import CommandError
from user.models import User

class Command(BaseCreateSuperuserCommand):
    help = 'Create a superuser with user_id and password, no email required.'

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--user_id', required=True, help='Specifies the user ID for the superuser.')
        parser.add_argument('--password', required=True, help='Specifies the password for the superuser.')

    def handle(self, *args, **options):
        user_id = options.get('user_id')
        password = options.get('password')

        if User.objects.filter(user_id=user_id).exists():
            raise CommandError(f'User with user_id "{user_id}" already exists.')

        superuser = User.objects.create_superuser(user_id=user_id, password=password, name="Admin")
        self.stdout.write(self.style.SUCCESS(f'Superuser "{user_id}" created successfully.'))
