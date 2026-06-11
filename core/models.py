from django.db import models
import uuid

# 1. SUBJECT MODEL
class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    def __str__(self):
        return self.name

<<<<<<< HEAD
# 2. TEACHER MODEL
=======
# ─────────────────────────────────────────────────────────────────────────────
# 2. EDUCATION LEVEL MODEL
# ─────────────────────────────────────────────────────────────────────────────
class EducationLevel(models.Model):
    SCHOOL = 'school'
    COLLEGE = 'college'
    BACHELOR = 'bachelor'
    LEVEL_CHOICES = [
        (SCHOOL, 'School Level (1-10)'),
        (COLLEGE, 'College Level (XI-XII)'),
        (BACHELOR, 'Bachelor Level'),
    ]
    code = models.CharField(max_length=20, primary_key=True, choices=LEVEL_CHOICES)
    name = models.CharField(max_length=50)

    class Meta:
        ordering = ['code']

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        return dict(self.LEVEL_CHOICES).get(self.code, self.name)

# ─────────────────────────────────────────────────────────────────────────────
# 3. SEMESTER MODEL
# ─────────────────────────────────────────────────────────────────────────────
class Semester(models.Model):
    SEMESTER_CHOICES = [(i, f'Semester {i}') for i in range(1, 9)]
    number = models.PositiveSmallIntegerField(primary_key=True, choices=SEMESTER_CHOICES)
    label = models.CharField(max_length=20, default='')

    class Meta:
        ordering = ['number']

    def __str__(self):
        return f'Semester {self.number}'

# ─────────────────────────────────────────────────────────────────────────────
# 4. ACADEMIC YEAR MODEL
# ─────────────────────────────────────────────────────────────────────────────
class AcademicYear(models.Model):
    name = models.CharField(max_length=20, unique=True, help_text="e.g. 2025-2026")
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if self.is_current:
            AcademicYear.objects.exclude(id=self.id).update(is_current=False)
        super().save(*args, **kwargs)

# ─────────────────────────────────────────────────────────────────────────────
# 5. DEPARTMENT MODEL
# ─────────────────────────────────────────────────────────────────────────────
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    head = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, blank=True, related_name='headed_departments')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

# ─────────────────────────────────────────────────────────────────────────────
# 6. GRADE SCALE MODEL
# ─────────────────────────────────────────────────────────────────────────────
class GradeScale(models.Model):
    name = models.CharField(max_length=50, unique=True, help_text="e.g. Standard, Division, GPA 4.0")
    pass_mark_percent = models.FloatField(default=40.0, help_text="Minimum % to pass")
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_grade(self, percentage):
        from core.grading_utils import grade_info_for_percentage
        return grade_info_for_percentage(percentage)['grade']

    def get_grade_point(self, percentage):
        from core.grading_utils import grade_info_for_percentage
        return grade_info_for_percentage(percentage)['subject_gpa']

    @property
    def grade_labels(self):
        return ['A+', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F']

# ─────────────────────────────────────────────────────────────────────────────
# 7. TEACHER MODEL
# ─────────────────────────────────────────────────────────────────────────────
>>>>>>> 801959c (Latest Commit)
class Teacher(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    email = models.EmailField(unique=True, null=True, blank=True)
    joining_date = models.DateField(auto_now_add=True)
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# 3. STUDENT MODEL
class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    student_class = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    semester = models.CharField(max_length=20, null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    image = models.ImageField(upload_to='student_images/', null=True, blank=True, help_text="Student photo")
    created_at = models.DateTimeField(auto_now_add=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Contact information
    email = models.EmailField(null=True, blank=True, help_text="Student email for notifications")
    phone = models.CharField(max_length=20, null=True, blank=True, help_text="Student phone number")
    
    qr_code_id = models.CharField(max_length=100, unique=True, blank=True)
    qr_code_data = models.TextField(blank=True, help_text="Unique QR code data for scanning")
    
    def save(self, *args, **kwargs):
        if not self.qr_code_id:
            self.qr_code_id = str(uuid.uuid4())[:12].upper()
        super().save(*args, **kwargs)
        qr_data = f"ACADSTAT_STUDENT|{self.id}|{self.roll_number or ''}|{self.name or ''}|{self.qr_code_id}"
        if self.qr_code_data != qr_data:
            Student.objects.filter(id=self.id).update(qr_code_data=qr_data)
            self.qr_code_data = qr_data

    def __str__(self):
        return f"{self.name} ({self.roll_number})"


# 4. TERMINAL EXAM CHOICES
TERMINAL_CHOICES = [
    ('1st', '1st Terminal'),
    ('2nd', '2nd Terminal'),
    ('3rd', '3rd Terminal'),
    ('Final', 'Final Terminal'),
]

# 5. RESULT MODEL
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    terminal = models.CharField(max_length=10, choices=TERMINAL_CHOICES, default='1st')
    marks_obtained = models.FloatField()
    total_marks = models.FloatField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'subject', 'terminal']

    def __str__(self):
        return f"{self.student.name} - {self.subject.name} ({self.get_terminal_display()}): {self.marks_obtained}"
    
    @property
    def percentage(self):
        if self.total_marks > 0:
            return round((self.marks_obtained / self.total_marks) * 100, 2)
        return 0

# 6. ATTENDANCE MODEL
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)
    qr_scanned = models.BooleanField(default=True)
    device_info = models.CharField(max_length=200, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', '-time']
    
    def __str__(self):
        return f"{self.student.name} - {self.date} ({self.time})"