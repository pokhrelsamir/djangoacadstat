
from django.db import models
import uuid

# Subject Model
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20,)

    def __str__(self):
        return self.name

# Teacher Model
class Teacher(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    email = models.EmailField(unique=True, null=True, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# Student Model with QR Code
class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    student_class = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    # QR Code fields
    qr_code_id = models.CharField(max_length=100, unique=True, blank=True)
    qr_code_data = models.TextField(blank=True, help_text="Unique QR code data for scanning")
    
    def save(self, *args, **kwargs):
        # Generate QR code ID first
        if not self.qr_code_id:
            self.qr_code_id = str(uuid.uuid4())[:12].upper()
        
        # Save to get the ID first, then generate QR data
        super().save(*args, **kwargs)
        
        # Now generate QR data with the actual ID
        qr_data = f"ACADSTAT_STUDENT|{self.id}|{self.roll_number or ''}|{self.name or ''}|{self.qr_code_id}"
        if self.qr_code_data != qr_data:
            Student.objects.filter(id=self.id).update(qr_code_data=qr_data)
            self.qr_code_data = qr_data

    def generate_qr_code(self):
        """Generate QR code data for this student"""
        if not self.id:
            return None
        self.qr_code_id = self.qr_code_id or str(uuid.uuid4())[:12].upper()
        self.qr_code_data = f"ACADSTAT_STUDENT|{self.id}|{self.roll_number or ''}|{self.name or ''}|{self.qr_code_id}"
        self.save()
        return self.qr_code_data

    def __str__(self):
        return f"{self.name} ({self.roll_number})"

# Terminal Exam Choices
TERMINAL_CHOICES = [
    ('1st', '1st Terminal'),
    ('2nd', '2nd Terminal'),
    ('3rd', '3rd Terminal'),
    ('Final', 'Final Terminal'),
]

# Marks / Result Model
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    terminal = models.CharField(max_length=10, choices=TERMINAL_CHOICES, default='1st')
    marks_obtained = models.FloatField()
    total_marks = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'subject']

    def __str__(self):
        return f"{self.student.name} - {self.subject.name}: {self.marks_obtained}/{self.total_marks} ({self.terminal})"
    
    @property
    def percentage(self):
        if self.total_marks > 0:
            return round((self.marks_obtained / self.total_marks) * 100, 2)
        return 0

# Attendance Model for QR Code Scanning
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    qr_scanned = models.BooleanField(default=True, help_text="Marked via QR code scan")
    device_info = models.CharField(max_length=200, blank=True, help_text="Device/browser info")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.student.name} - {self.date} ({self.time})"
