# Fix migration for QR Code fields - add without unique constraint first, then populate unique values, then add constraint

from django.db import migrations, models
import uuid


def generate_unique_qr_code_ids(apps, schema_editor):
    """Generate unique QR code IDs for all existing students"""
    Student = apps.get_model('core', 'Student')
    for student in Student.objects.all():
        if not student.qr_code_id:
            # Generate a unique ID using UUID
            student.qr_code_id = str(uuid.uuid4())[:12].upper()
            
            # Make sure it's unique in case of collision
            existing = Student.objects.filter(qr_code_id=student.qr_code_id)
            if student.id:
                existing = existing.exclude(id=student.id)
            
            counter = 1
            original_id = student.qr_code_id
            while existing.exists():
                student.qr_code_id = f"{original_id[:10]}{counter}"
                counter += 1
                existing = Student.objects.filter(qr_code_id=student.qr_code_id)
                if student.id:
                    existing = existing.exclude(id=student.id)
            
            student.save(update_fields=['qr_code_id'])


def reverse_qr_code_ids(apps, schema_editor):
    """Reverse operation - clear QR code IDs"""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_result_marks_obtained_alter_subject_code'),
    ]

    operations = [
        # First add the field without unique constraint
        migrations.AddField(
            model_name='student',
            name='qr_code_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='student',
            name='qr_code_data',
            field=models.TextField(blank=True, help_text='Unique QR code data for scanning'),
        ),
        
        # Generate unique QR code IDs for existing students
        migrations.RunPython(generate_unique_qr_code_ids, reverse_qr_code_ids),
        
        # Now add the unique constraint
        migrations.AlterField(
            model_name='student',
            name='qr_code_id',
            field=models.CharField(blank=True, max_length=100, unique=True),
        ),
        
        # Create Attendance model
        migrations.CreateModel(
            name='Attendance',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(auto_now_add=True)),
                ('time', models.TimeField(auto_now_add=True)),
                ('qr_scanned', models.BooleanField(default=True, help_text='Marked via QR code scan')),
                ('device_info', models.CharField(blank=True, help_text='Device/browser info', max_length=200)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('student', models.ForeignKey(on_delete=models.CASCADE, to='core.student')),
            ],
            options={
                'ordering': ['-date', '-time'],
                'unique_together': {('student', 'date')},
            },
        ),
    ]
