from django.contrib import admin
from .models import Student, Subject, Result, Teacher


# Simple Admin Configuration
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name', 'roll_number', 'student_class', 'section', 'teacher')
    search_fields = ('name', 'roll_number')
    list_filter = ('student_class', 'section')
    ordering = ('name',)


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'code')
    search_fields = ('name', 'code')
    ordering = ('name',)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject', 'marks_obtained', 'total_marks', 'created_at')
    list_filter = ('subject', 'created_at')
    search_fields = ('student__name', 'subject__name')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'subject', 'email', 'phone')
    search_fields = ('first_name', 'last_name', 'email')
    list_filter = ('subject',)
    ordering = ('first_name',)
