"""
Teacher login helpers — username format firstname.lastname, default password "pass".
"""
from __future__ import annotations

import re

from django.contrib.auth import get_user_model

TEACHER_DEFAULT_PASSWORD = 'pass'


def _username_base(first_name: str, last_name: str) -> str:
    first = re.sub(r'[^a-z0-9]', '', (first_name or '').strip().split()[0].lower())
    last = re.sub(r'[^a-z0-9]', '', (last_name or '').strip().lower())
    if not first or not last:
        return ''
    return f'{first}.{last}'


def generate_teacher_username(first_name: str, last_name: str, exclude_user_id=None) -> str:
    """Build username like bishwa.gurung from first + last name."""
    base = _username_base(first_name, last_name)
    if not base:
        raise ValueError('Teacher first and last name are required to build a username.')
    User = get_user_model()
    username = base
    suffix = 2
    while User.objects.filter(username=username).exclude(pk=exclude_user_id).exists():
        username = f'{base}{suffix}'
        suffix += 1
    return username


def username_matches_teacher(username: str, teacher) -> bool:
    """True if username matches this teacher (dot or legacy underscore format)."""
    uname = (username or '').lower().strip().replace('_', '.')
    expected = _username_base(teacher.first_name, teacher.last_name)
    legacy_underscore = (
        f"{teacher.first_name.replace(' ', '').lower()}.{teacher.last_name.replace(' ', '').lower()}"
    )
    return uname == expected or uname == legacy_underscore or uname.startswith(expected)


def ensure_teacher_user(teacher, password=None, username=None, normalize_username=False):
    """
    Create or link Django User for a Teacher profile.
    Returns the User instance.
    """
    User = get_user_model()
    password = password if password is not None else TEACHER_DEFAULT_PASSWORD

    if teacher.user_id:
        user = teacher.user
        if normalize_username:
            new_username = username or generate_teacher_username(
                teacher.first_name, teacher.last_name, exclude_user_id=user.pk
            )
            if user.username != new_username and not User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                user.username = new_username
        user.email = teacher.email or user.email or ''
        user.first_name = teacher.first_name
        user.last_name = teacher.last_name
        user.is_active = True
        if password:
            user.set_password(password)
        user.save()
        return user

    if username:
        desired = username
    else:
        desired = generate_teacher_username(teacher.first_name, teacher.last_name)

    existing = User.objects.filter(username=desired).first()
    if not existing:
        existing = User.objects.filter(username=desired.replace('.', '_')).first()

    if existing:
        try:
            if existing.teacher_profile.pk != teacher.pk:
                desired = generate_teacher_username(teacher.first_name, teacher.last_name)
                existing = User.objects.filter(username=desired).first()
        except Exception:
            pass

    if existing:
        user = existing
        user.email = teacher.email or user.email or ''
        user.first_name = teacher.first_name
        user.last_name = teacher.last_name
        user.is_active = True
        if password:
            user.set_password(password)
        user.save()
    else:
        user = User.objects.create_user(
            username=desired,
            password=password,
            email=teacher.email or '',
            first_name=teacher.first_name,
            last_name=teacher.last_name,
            is_active=True,
        )

    teacher.user = user
    teacher.save(update_fields=['user'])
    return user


def link_teacher_by_username(user):
    """If user matches a teacher name pattern but is unlinked, attach and return teacher."""
    from core.models import Teacher

    try:
        return Teacher.objects.get(user=user, is_active=True)
    except Teacher.DoesNotExist:
        pass

    for teacher in Teacher.objects.filter(is_active=True):
        if teacher.user_id and teacher.user_id != user.pk:
            continue
        if username_matches_teacher(user.username, teacher):
            teacher.user = user
            teacher.save(update_fields=['user'])
            return teacher
    return None
