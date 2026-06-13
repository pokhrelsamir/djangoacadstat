"""
Normalize all teacher logins to firstname.lastname with default password "pass".

Usage:
    python manage.py sync_teacher_users
    python manage.py sync_teacher_users --keep-passwords
"""
from django.core.management.base import BaseCommand
from core.models import Teacher
from core.teacher_auth import TEACHER_DEFAULT_PASSWORD, ensure_teacher_user, generate_teacher_username


class Command(BaseCommand):
    help = 'Link/create user accounts for all teachers (firstname.lastname, password: pass)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--keep-passwords',
            action='store_true',
            help='Do not reset passwords for teachers who already have a linked user',
        )

    def handle(self, *args, **options):
        keep_passwords = options['keep_passwords']
        teachers = Teacher.objects.filter(is_active=True).order_by('id')
        if not teachers.exists():
            self.stdout.write(self.style.WARNING('No active teachers found.'))
            return

        self.stdout.write(self.style.SUCCESS('\nSyncing teacher login accounts...\n'))
        for teacher in teachers:
            password = None if keep_passwords and teacher.user_id else TEACHER_DEFAULT_PASSWORD
            username = generate_teacher_username(
                teacher.first_name,
                teacher.last_name,
                exclude_user_id=getattr(teacher.user, 'pk', None),
            )
            user = ensure_teacher_user(
                teacher,
                password=password,
                username=username,
                normalize_username=True,
            )
            pwd_note = '(password unchanged)' if keep_passwords and password is None else f'password: {TEACHER_DEFAULT_PASSWORD}'
            self.stdout.write(f'  OK {teacher.get_full_name():30} -> {user.username:25} {pwd_note}')

        self.stdout.write(self.style.SUCCESS(f'\nDone — {teachers.count()} teacher(s) synced.\n'))
