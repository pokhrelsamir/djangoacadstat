
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Result

def home(request):
    return render(request, 'dashboard/home.html')

@login_required
def dashboard(request):
    results = Result.objects.all()
    labels = [r.subject.name for r in results]
    data = [r.marks for r in results]

    return render(request, 'dashboard/dashboard.html', {
        'labels': labels,
        'data': data
    })
