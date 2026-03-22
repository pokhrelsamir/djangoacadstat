from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_http_methods
from .forms import ResultForm
from .models import Result, Student, Subject, Attendance
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
import json
import qrcode
from io import BytesIO
import base64


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
    
    # Get today's attendance count
    today = timezone.now().date()
    today_attendance = Attendance.objects.filter(date=today).count()
    
    context = {
        'total_students': Student.objects.count(),
        'total_subjects': Subject.objects.count(),
        'total_marks': Result.objects.count(),
        'average_marks': avg_marks,
        'today_attendance': today_attendance,
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


# ============ QR CODE ATTENDANCE SYSTEM ============

# 📱 QR CODE LIST - View all students with their QR codes
@login_required
def qr_codes(request):
    """Display all students with their QR codes for printing/scanning"""
    students = Student.objects.all().order_by('name')
    
    # Generate QR codes for each student
    qr_codes_list = []
    for student in students:
        # Ensure QR code data exists - regenerate if missing
        if not student.qr_code_data or not student.qr_code_id:
            student.generate_qr_code()
            student.refresh_from_db()
        
        if student.qr_code_data:
            # Generate QR code image
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(student.qr_code_data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            qr_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            qr_codes_list.append({
                'student': student,
                'qr_code': f"data:image/png;base64,{qr_base64}",
                'qr_id': student.qr_code_id or 'N/A'
            })
    
    return render(request, 'dashboard/qr_codes.html', {'qr_codes': qr_codes_list})


# 📱 SINGLE STUDENT QR CODE - For printing individual QR codes
@login_required
def student_qr_code(request, student_id):
    """Generate QR code for a specific student"""
    student = get_object_or_404(Student, id=student_id)
    
    if not student.qr_code_data:
        student.save()  # Generate QR data
    
    # Generate QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(student.qr_code_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    
    return HttpResponse(buffer.getvalue(), content_type='image/png')


# 📱 QR ATTENDANCE SCANNER - Camera-based QR scanning
@login_required
def qr_scanner(request):
    """QR code scanner page with camera access"""
    return render(request, 'dashboard/qr_scanner.html')


# 📱 QR SCAN PROCESS - Process scanned QR code data
@login_required
@require_http_methods(["POST"])
def process_qr_scan(request):
    """Process QR code scan and mark attendance"""
    try:
        data = json.loads(request.body)
        qr_data = data.get('qr_data', '')
        device_info = data.get('device_info', '')
        
        # Parse QR code data - format: ACADSTAT_STUDENT|id|roll|name|qr_id
        if not qr_data.startswith('ACADSTAT_STUDENT'):
            return JsonResponse({
                'success': False, 
                'message': 'Invalid QR code. This is not a valid student QR code.'
            }, status=400)
        
        # Parse the QR data
        parts = qr_data.split('|')
        if len(parts) < 5:
            return JsonResponse({
                'success': False, 
                'message': 'Invalid QR code format. Please scan a valid student QR code.'
            }, status=400)
        
        # Get student ID from QR code
        student_id_str = parts[1]
        if not student_id_str or student_id_str == 'None':
            return JsonResponse({
                'success': False, 
                'message': 'QR code not properly configured. Please regenerate student QR code.'
            }, status=400)
        
        student_id = int(student_id_str)
        student = get_object_or_404(Student, id=student_id)
        
        # Check if already marked today
        today = timezone.now().date()
        if Attendance.objects.filter(student=student, date=today).exists():
            return JsonResponse({
                'success': False, 
                'message': f'Attendance already marked for {student.name} today!'
            })
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Create attendance record
        attendance = Attendance.objects.create(
            student=student,
            qr_scanned=True,
            device_info=device_info[:200],
            ip_address=ip_address
        )
        
        return JsonResponse({
            'success': True, 
            'message': f'Attendance marked successfully for {student.name}!',
            'student_name': student.name,
            'student_roll': student.roll_number or 'N/A',
            'time': attendance.time.strftime('%H:%M:%S')
        })
        
    except ValueError:
        return JsonResponse({
            'success': False, 
            'message': 'Invalid QR code data. Student ID is not a valid number.'
        }, status=400)
    except Student.DoesNotExist:
        return JsonResponse({
            'success': False, 
            'message': 'Student not found in database. Please check the QR code.'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'message': f'Error processing QR code: {str(e)}'
        }, status=400)


# 📱 ATTENDANCE LIST - View attendance records
@login_required
def attendance_list(request):
    """Display attendance records"""
    attendance_records = Attendance.objects.select_related('student').all()[:100]
    return render(request, 'dashboard/attendance_list.html', {'attendance': attendance_records})


# 📱 ATTENDANCE REPORT - Attendance statistics
@login_required
def attendance_report(request):
    """Attendance report with charts"""
    from django.db.models import Count
    
    # Get attendance by date
    attendance_by_date = Attendance.objects.values('date').annotate(
        count=Count('id')
    ).order_by('-date')[:30]
    
    # Get attendance by student
    top_attendance = Attendance.objects.values(
        'student__name', 'student__roll_number'
    ).annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'attendance_by_date': list(attendance_by_date),
        'top_attendance': list(top_attendance),
    }
    return render(request, 'dashboard/attendance_report.html', context)


# 📱 MOBILE SCANNER - Standalone mobile-friendly scanner
def mobile_scanner(request):
    """Mobile-friendly QR scanner for app integration"""
    return render(request, 'dashboard/mobile_scanner.html')


# 📱 REGENERATE ALL QR CODES
@login_required
def regenerate_qr_codes(request):
    """Regenerate QR codes for all students"""
    students = Student.objects.all()
    count = 0
    for student in students:
        student.generate_qr_code()
        count += 1
    
    return JsonResponse({
        'success': True, 
        'message': f'QR codes regenerated for {count} students'
    })