"""
Management command to list all teachers with their IDs.

Usage:
    python manage.py list_teacher

This shows all teachers and their database IDs which you can use
with the create_teacher_user command.
"""
from django.core.management.base import BaseCommand
from core.models import Teacher


class Command(BaseCommand):
    help = 'List all teachers with their database IDs'

    def handle(self, *args, **options):
        teachers = Teacher.objects.all().order_by('id')
        
        if not teachers.exists():
            self.stdout.write(self.style.WARNING('No teachers found in the database!'))
            return
        
        self.stdout.write(self.style.SUCCESS('\nAll Teachers (Use ID in create_teacher_user command):\n'))
        self.stdout.write('-' * 50)
        
        for teacher in teachers:
            username = teacher.user.username if teacher.user_id else '(no login)'
            self.stdout.write(
                f'  ID: {teacher.id:3} | {teacher.get_full_name():28} | {username:22} | '
                f'Subjects: {", ".join([s.name for s in teacher.subjects.all()]) or "—"}'
            )

        self.stdout.write('-' * 80)
        self.stdout.write(f'\nTotal: {teachers.count()} teachers\n')
        self.stdout.write('Create / repair login (default password: pass):')
        self.stdout.write('  python manage.py create_teacher_user <id>')
        self.stdout.write('  python manage.py create_teacher_user <id> mypassword')
        self.stdout.write('\nSync all teachers to firstname.lastname + pass:')
        self.stdout.write('  python manage.py sync_teacher_users')
