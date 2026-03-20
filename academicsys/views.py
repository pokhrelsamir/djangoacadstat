from django.shortcuts import render

def dashboard_home(request):
    context = {
        'student_name': 'Ram Kumar Sharma'  # You can replace with actual DB data
    }
    return render(request, 'dashboard/home.html', context)