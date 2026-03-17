
from django.db import models
from django.contrib.auth.models import User

class Student(models.Model):
    name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    student_class = models.CharField(max_length=20)
    section = models.CharField(max_length=5)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

        # Link to Teacher
    teacher = models.ForeignKey(
        'Teacher',               # Use quotes if Teacher is defined below or imported
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )


    def __str__(self):
        return f"{self.name} ({self.roll_number})"
    
    #look carefully it is added later

class Teacher(models.Model):
    # Teacher name
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)

    # Subject they teach
    subject = models.CharField(max_length=100)

    # Optional: contact email
    email = models.EmailField(unique=True, null=True, blank=True)

    # Optional: joining date
    joining_date = models.DateField(auto_now_add=True)

    # Optional: phone number
    phone = models.CharField(max_length=15, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    #upto here
    

class Subject(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    marks = models.IntegerField()

    def __str__(self):
        return f"{self.student} - {self.subject}"
    
