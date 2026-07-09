# Generated manually to align Student.user with an existing database column.

import re

import django.db.models.deletion
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.db import migrations, models


def ensure_student_user_column(apps, schema_editor):
    table_name = 'core_student'
    column_name = 'user_id'
    existing_columns = {
        column.name
        for column in schema_editor.connection.introspection.get_table_description(
            schema_editor.connection.cursor(),
            table_name,
        )
    }
    if column_name in existing_columns:
        return

    quoted_table = schema_editor.quote_name(table_name)
    quoted_column = schema_editor.quote_name(column_name)
    schema_editor.execute(f'ALTER TABLE {quoted_table} ADD COLUMN {quoted_column} integer NULL')


def _student_username(name, roll_number, User):
    base = roll_number or name or 'student'
    base = re.sub(r'[^a-zA-Z0-9_]+', '_', base.lower()).strip('_') or 'student'
    if not base.startswith('student_'):
        base = f'student_{base}'

    username = base[:150]
    counter = 1
    while User.objects.filter(username=username).exists():
        suffix = f'_{counter}'
        username = f'{base[:150 - len(suffix)]}{suffix}'
        counter += 1
    return username


def populate_missing_student_users(apps, schema_editor):
    User = apps.get_model('auth', 'User')
    cursor = schema_editor.connection.cursor()
    quoted_table = schema_editor.quote_name('core_student')
    cursor.execute(
        f'SELECT id, name, roll_number, email FROM {quoted_table} WHERE user_id IS NULL ORDER BY id'
    )
    rows = cursor.fetchall()

    for student_id, name, roll_number, email in rows:
        name_parts = name.split() if name else []
        user = User.objects.create(
            username=_student_username(name, roll_number, User),
            password=make_password('student123'),
            email=email or '',
            first_name=name_parts[0] if name_parts else '',
            last_name=' '.join(name_parts[1:]) if len(name_parts) > 1 else '',
            is_active=True,
        )
        cursor.execute(
            f'UPDATE {quoted_table} SET user_id = %s WHERE id = %s',
            [user.pk, student_id],
        )


def enforce_student_user_constraints(apps, schema_editor):
    if schema_editor.connection.vendor != 'postgresql':
        return

    quoted_table = schema_editor.quote_name('core_student')
    schema_editor.execute(f'ALTER TABLE {quoted_table} ALTER COLUMN user_id SET NOT NULL')
    schema_editor.execute(
        'CREATE UNIQUE INDEX IF NOT EXISTS core_student_user_id_unique '
        f'ON {quoted_table} (user_id)'
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('core', '0015_class_student_class_section_subject_classes'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(ensure_student_user_column, migrations.RunPython.noop),
                migrations.RunPython(populate_missing_student_users, migrations.RunPython.noop),
                migrations.RunPython(enforce_student_user_constraints, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name='student',
                    name='user',
                    field=models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name='student_profile',
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
