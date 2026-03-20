from django.shortcuts import render, redirect
from .forms import ResultForm
from .models import Result, Student, Subject
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout


# 🏠 HOME VIEW (LANDING PAGE)
def home_view(request):
    """Landing page - accessible without login"""
    return render(request, 'dashboard/home.html')


# 🔐 LOGIN VIEW
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('/dashboard/')  # ✅ go to dashboard
        else:
            return render(request, 'registration/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'registration/login.html')


# 🚪 LOGOUT VIEW
def logout_view(request):
    logout(request)
    return redirect('/')


# 📊 DASHBOARD (MAIN PAGE AFTER LOGIN)
@login_required
def dashboard(request):
    # Get all results for calculations
    results = Result.objects.all()
    
    # Calculate average marks
    avg_marks = 0
    if results.exists():
        total = sum(r.marks_obtained for r in results)
        avg_marks = round(total / results.count(), 1)
    
    context = {
        'total_students': Student.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_marks': Result.objects.count(),
        'average_marks': avg_marks,
        'user': request.user,
    }
    return render(request, 'dashboard/dashboard.html', context)


# ➕ ADD MARKS
@login_required
def add_marks(request):
    if request.method == "POST":
        form = ResultForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/marks-list/')
    else:
        form = ResultForm()

    return render(request, 'dashboard/add_marks.html', {'form': form})


# 📋 MARKS LIST
@login_required
def marks_list(request):
    all_marks = Result.objects.all()
    return render(request, 'dashboard/marks_list.html', {'result': all_marks})