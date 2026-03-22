from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .forms import ResultForm
from .models import Result, Student, Subject
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
import json


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
    all_marks = Result.objects.all().select_related('student', 'subject')
    return render(request, 'dashboard/marks_list.html', {'result': all_marks})

# ✏️ EDIT MARKS
@login_required
@require_http_methods(["POST"])
def edit_marks(request, mark_id):
    """API endpoint to update marks"""
    try:
        result = get_object_or_404(Result, id=mark_id)
        data = json.loads(request.body)
        
        result.marks_obtained = float(data.get('marks_obtained', 0))
        result.total_marks = float(data.get('total_marks', 100))
        result.save()
        
        return JsonResponse({'success': True, 'message': 'Marks updated successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)

# 🗑️ DELETE MARKS
@login_required
@require_http_methods(["POST"])
def delete_marks(request, mark_id):
    """API endpoint to delete marks"""
    try:
        result = get_object_or_404(Result, id=mark_id)
        result.delete()
        return JsonResponse({'success': True, 'message': 'Marks deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)