from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from core.models import Student, Teacher


DEFAULT_PASSWORD = "password123"


@receiver(post_save, sender=Student)
def create_student_user(sender, instance, created, **kwargs):
    """Create a Django user when a new student is added"""
    if created:
        # Check if user already exists
        if not User.objects.filter(username=instance.name).exists():
            user = User.objects.create_user(
                username=instance.name,
                password=DEFAULT_PASSWORD,
                first_name=instance.name.split()[0] if instance.name else '',
                last_name=' '.join(instance.name.split()[1:]) if len(instance.name.split()) > 1 else '',
                email=instance.email or ''
            )
            print(f"Created user '{instance.name}' with default password '{DEFAULT_PASSWORD}'")
        else:
            print(f"User '{instance.name}' already exists")


@receiver(post_delete, sender=Student)
def delete_student_user(sender, instance, **kwargs):
    """Delete Django user when student is deleted"""
    try:
        user = User.objects.get(username=instance.name)
        user.delete()
        print(f"Deleted user '{instance.name}'")
    except User.DoesNotExist:
        pass


@receiver(post_save, sender=Teacher)
def create_teacher_user(sender, instance, created, **kwargs):
    """Create a Django user when a new teacher is added"""
    if created:
        username = f"{instance.first_name}{instance.last_name}".lower().replace(' ', '')
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                password=DEFAULT_PASSWORD,
                first_name=instance.first_name,
                last_name=instance.last_name,
                email=instance.email or ''
            )
            print(f"Created teacher user '{username}' with default password")
        else:
            print(f"Teacher user '{username}' already exists")
