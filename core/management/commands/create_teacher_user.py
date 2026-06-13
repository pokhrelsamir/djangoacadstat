"""
Create or repair a Django login for a teacher (firstname.lastname / default pass).

Usage:
    python manage.py create_teacher_user <teacher_id>
    python manage.py create_teacher_user <teacher_id> mypassword
    python manage.py create_teacher_user <teacher_id> --username custom.name

Default password: pass
"""
from django.core.management.base import BaseCommand
from core.models import Teacher
from core.teacher_auth import TEACHER_DEFAULT_PASSWORD, ensure_teacher_user, generate_teacher_username


class Command(BaseCommand):
    help = 'Create or link a teacher login (username: firstname.lastname, default password: pass)'

    def add_arguments(self, parser):
        parser.add_argument('teacher_id', type=int, help='Teacher database ID')
        parser.add_argument(
            'password',
            nargs='?',
            default=TEACHER_DEFAULT_PASSWORD,
            help=f'Password (default: {TEACHER_DEFAULT_PASSWORD})',
        )
        parser.add_argument('--username', type=str, help='Custom username (default: firstname.lastname)')
        parser.add_argument(
            '--normalize',
            action='store_true',
            help='Rename existing username to firstname.lastname format',
        )

    def handle(self, *args, **options):
        teacher_id = options['teacher_id']
        password = options['password']
        custom_username = options.get('username')
        normalize = options['normalize']

        try:
            teacher = Teacher.objects.get(id=teacher_id)
        except Teacher.DoesNotExist:
            self.stderr.write(self.style.ERROR(f'Teacher with ID {teacher_id} not found!'))
            return

        if not custom_username:
            custom_username = generate_teacher_username(
                teacher.first_name,
                teacher.last_name,
                exclude_user_id=getattr(teacher.user, 'pk', None),
            )

        user = ensure_teacher_user(
            teacher,
            password=password,
            username=custom_username,
            normalize_username=normalize,
        )

        self.stdout.write(self.style.SUCCESS(
            f'Login ready for {teacher.get_full_name()}\n'
            f'  Username: {user.username}\n'
            f'  Password: {password}\n'
            f'  Teacher ID: {teacher_id}\n'
            f'  Login URL: /login/\n'
            f'  Dashboard: /dashboard/ (teacher view)'
        ))
