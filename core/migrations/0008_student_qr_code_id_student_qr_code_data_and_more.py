# Generated migration for QR Code and Attendance features

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_result_marks_obtained_alter_subject_code'),
    ]

    operations = [
        # Add QR code fields to Student model
        migrations.AddField(
            model_name='student',
            name='qr_code_id',
            field=models.CharField(blank=True, max_length=100, unique=True),
        ),
        migrations.AddField(
            model_name='student',
            name='qr_code_data',
            field=models.TextField(blank=True, help_text='Unique QR code data for scanning'),
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
                ('student', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.student')),
            ],
            options={
                'ordering': ['-date', '-time'],
                'unique_together': {('student', 'date')},
            },
        ),
    ]
