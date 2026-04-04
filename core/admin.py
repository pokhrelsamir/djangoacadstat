from django.contrib import admin
from .models import Student, Subject, Result, Teacher, Attendance


# Simple Admin Configuration
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_number', 'student_class', 'section', 'semester', 'teacher', 'qr_code_id')
    search_fields = ('name', 'roll_number', 'qr_code_id')
    list_filter = ('student_class', 'section', 'semester')
    ordering = ('name',)
    readonly_fields = ('qr_code_id', 'qr_code_data')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'terminal', 'marks_obtained', 'total_marks', 'created_at')
    list_filter = ('subject', 'terminal', 'created_at')
    search_fields = ('student__name', 'subject__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'subject', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('subject',)
    ordering = ('first_name',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time', 'qr_scanned')
    list_filter = ('date', 'qr_scanned')
    search_fields = ('student__name', 'student__roll_number')
    ordering = ('-date', '-time')
    date_hierarchy = 'date'
