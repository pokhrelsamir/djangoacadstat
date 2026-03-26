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
from django.contrib import messages


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
    # Check if user is a student (has username matching a student)
    username = request.user.username.lower().strip()
    
    # Try to find student by exact name match (case-insensitive)
    students = Student.objects.all()
    for student in students:
        if student.name.lower().strip() == username:
            # Redirect students to their own dashboard
            return student_dashboard(request, student.id)
    
    # Also try partial match
    for student in students:
        if username in student.name.lower() or student.name.lower() in username:
            return student_dashboard(request, student.id)
    
    # Get all results for calculations (for admin/teachers)
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
        'is_admin': True,
    }
    return render(request, 'dashboard/dashboard.html', context)


# 🎓 STUDENT DASHBOARD (Limited Access)
@login_required
def student_dashboard(request, student_id=None):
    """Student dashboard with limited access - shows only their own data"""
    import qrcode
    from io import BytesIO
    import base64
    
    # If student_id is provided, use that, otherwise find by username
    if student_id:
        student = get_object_or_404(Student, id=student_id)
    else:
        # Try to find student by username
        try:
            student = Student.objects.get(name=request.user.username)
        except Student.DoesNotExist:
            return render(request, 'dashboard/student_dashboard.html', {
                'error': 'Student profile not found. Please contact admin.'
            })
    
    # Get student's own results
    student_results = Result.objects.filter(student=student).select_related('subject')
    
    # Calculate own stats
    total_marks_obtained = sum(r.marks_obtained for r in student_results)
    total_marks = sum(r.total_marks for r in student_results)
    overall_percentage = (total_marks_obtained / total_marks * 100) if total_marks > 0 else 0
    
    # Get attendance count
    student_attendance = Attendance.objects.filter(student=student)
    total_attendance = student_attendance.count()
    
    # Get marks by terminal for chart
    terminal_data = {}
    for terminal in ['1st', '2nd', '3rd', 'Final']:
        terminal_results = student_results.filter(terminal=terminal)
        if terminal_results.exists():
            t_marks = sum(r.marks_obtained for r in terminal_results)
            t_total = sum(r.total_marks for r in terminal_results)
            t_percentage = (t_marks / t_total * 100) if t_total > 0 else 0
            terminal_data[terminal] = {
                'obtained': t_marks,
                'total': t_total,
                'percentage': round(t_percentage, 1)
            }
    
    # Get subject-wise performance
    subject_data = {}
    for result in student_results:
        if result.subject.name not in subject_data:
            subject_data[result.subject.name] = []
        percentage = (result.marks_obtained / result.total_marks * 100) if result.total_marks > 0 else 0
        subject_data[result.subject.name].append({
            'terminal': result.terminal,
            'percentage': round(percentage, 1),
            'marks': result.marks_obtained,
            'total': result.total_marks
        })
    
    # Generate QR code for student
    if student.qr_code_data:
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
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
    else:
        qr_code_base64 = None
    
    context = {
        'student': student,
        'student_results': student_results,
        'total_subjects': student_results.values('subject').distinct().count(),
        'total_marks_obtained': total_marks_obtained,
        'total_marks': total_marks,
        'overall_percentage': round(overall_percentage, 1),
        'total_attendance': total_attendance,
        'terminal_data': terminal_data,
        'subject_data': subject_data,
        'terminal_data_json': json.dumps(terminal_data),
        'subject_data_json': json.dumps(subject_data),
        'qr_code': qr_code_base64,
        'user': request.user,
        'is_student': True,
    }
    
    return render(request, 'dashboard/student_dashboard.html', context)


# ➕ ADD MARKS
@login_required
def add_marks(request):
    if request.method == "POST":
        form = ResultForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Marks added successfully!")

            # Handle terminal from form data if not in form
            terminal = request.POST.get('terminal', '1st')
            result = form.save(commit=False)
            result.terminal = terminal
            result.save()

            return redirect('/marks-list/')
        
        else:
            messages.error(request, "Please correct the error below. (Perhaps marks for this student/subject already exist?)")
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


# 📊 CHART DATA API
@login_required
def chart_data(request):
    """Get chart data for dashboard visualization"""
    from django.db.models import Avg, Count
    
    # Get marks distribution by percentage ranges
    results = Result.objects.all()
    
    distribution = {
        'labels': ['0-40%', '40-60%', '60-75%', '75-90%', '90-100%'],
        'data': [0, 0, 0, 0, 0]
    }
    
    for result in results:
        percentage = (result.marks_obtained / result.total_marks * 100) if result.total_marks > 0 else 0
        if percentage < 40:
            distribution['data'][0] += 1
        elif percentage < 60:
            distribution['data'][1] += 1
        elif percentage < 75:
            distribution['data'][2] += 1
        elif percentage < 90:
            distribution['data'][3] += 1
        else:
            distribution['data'][4] += 1
    
    # Get average marks by subject
    subject_averages = Result.objects.values('subject__name').annotate(
        avg_marks=Avg('marks_obtained')
    ).order_by('-avg_marks')[:10]
    
    subject_data = {
        'labels': [s['subject__name'] for s in subject_averages],
        'data': [round(s['avg_marks'], 1) for s in subject_averages]
    }
    
    # Get top 5 students by average
    student_averages = Result.objects.values(
        'student__id', 'student__name'
    ).annotate(
        avg_marks=Avg('marks_obtained')
    ).order_by('-avg_marks')[:5]
    
    top_students = {
        'labels': [s['student__name'] for s in student_averages],
        'data': [round(s['avg_marks'], 1) for s in student_averages]
    }
    
    # Get attendance by date (last 7 days)
    from django.utils import timezone
    from datetime import timedelta
    
    dates = []
    attendance_counts = []
    for i in range(7):
        date = timezone.now().date() - timedelta(days=i)
        count = Attendance.objects.filter(date=date).count()
        dates.append(date.strftime('%b %d'))
        attendance_counts.append(count)
    
    dates.reverse()
    attendance_counts.reverse()
    
    return JsonResponse({
        'distribution': distribution,
        'subject_averages': subject_data,
        'top_students': top_students,
        'attendance': {
            'labels': dates,
            'data': attendance_counts
        },
        'total_students': Student.objects.count(),
        'total_results': Result.objects.count(),
        'average_percentage': round(sum([r for r in distribution['data'] if r > 0]) / len([r for r in distribution['data'] if r > 0]) if any(d > 0 for d in distribution['data']) else 0, 1)
    })


# 📄 MARK SHEET VIEW
@login_required
def mark_sheet(request, student_id=None, terminal=None):
    """Generate official mark sheet for a student with terminal filter"""
    import qrcode
    from io import BytesIO
    import base64
    from datetime import datetime
    
    # Get all students for selection dropdown
    students = Student.objects.all().order_by('name')
    
    if student_id and terminal:
        # Get specific student's results for a specific terminal
        results = Result.objects.filter(
            student_id=student_id,
            terminal=terminal
        ).select_related('student', 'subject')
        selected_student = Student.objects.get(id=student_id)
    elif student_id:
        # Get specific student's results (all terminals)
        results = Result.objects.filter(student_id=student_id).select_related('student', 'subject')
        selected_student = Student.objects.get(id=student_id)
        terminal = 'All'
    else:
        results = []
        selected_student = None
        terminal = 'All'
    
    # Calculate totals
    total_subjects = len(results) if results else 0
    total_marks_obtained = sum(r.marks_obtained for r in results)
    total_marks = sum(r.total_marks for r in results)
    overall_percentage = (total_marks_obtained / total_marks * 100) if total_marks > 0 else 0
    
    # Determine overall pass/fail (all subjects must have >= 40%)
    all_passed = all((r.marks_obtained / r.total_marks * 100) >= 40 for r in results) if results else False
    
    # Build results list with grade and percentage attributes
    results_with_grades = []
    for r in results:
        pct = (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0
        results_with_grades.append({
            'result': r,
            'grade': 'P' if pct >= 40 else 'F',
            'percentage': round(pct, 1)
        })
    
    # Generate college QR code
    college_data = "SOCH_COLLEGE_OF_IT|RANIPAWA-12|POKHARA|ESTD:2020"
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(college_data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    college_qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    # Get current academic year
    academic_year = datetime.now().year
    
    # Generate document ID
    doc_id = f"SOCH-{datetime.now().strftime('%Y%m%d')}-{student_id or 'DEMO'}"
    
    context = {
        'students': students,
        'student_results': results_with_grades,
        'selected_student': selected_student,
        'selected_terminal': terminal,
        'total_subjects': total_subjects,
        'total_marks_obtained': total_marks_obtained,
        'total_marks': total_marks,
        'overall_percentage': round(overall_percentage, 2),
        'all_passed': all_passed,
        'academic_year': f"{academic_year}-{academic_year + 1}",
        'college_qr_code': college_qr_code,
        'doc_id': doc_id,
    }
    
    return render(request, 'dashboard/mark_sheet.html', context)


# 📋 SELECT STUDENT FOR MARK SHEET
@login_required
def select_mark_sheet(request):
    """Student selection page for mark sheet generation"""
    students = Student.objects.all().order_by('name')
    
    # Get unique terminals
    terminals = Result.objects.values_list('terminal', flat=True).distinct()
    
    context = {
        'students': students,
        'terminals': terminals,
    }
    
    return render(request, 'dashboard/select_mark_sheet.html', context)


#  STUDENT ANALYSIS VIEW
@login_required
def student_analysis(request):
    """AI-powered analysis of student performance, focusing on students with low marks"""
    
    # Get filter parameters
    filter_type = request.GET.get('filter', 'attention')
    selected_class = request.GET.get('class', '')
    sort_by = request.GET.get('sort', 'lowest')
    
    # Get all students with their results
    students = Student.objects.all().prefetch_related('result_set')
    
    student_analyses = []
    all_classes = []
    needs_attention_count = 0
    at_risk_count = 0
    total_percentage = 0
    student_count = 0
    
    for student in students:
        results = list(student.result_set.select_related('subject').all())
        
        if not results:
            continue
            
        all_classes.append(student.student_class)
        
        # Calculate percentage
        total_obtained = sum(r.marks_obtained for r in results)
        total_possible = sum(r.total_marks for r in results)
        percentage = (total_obtained / total_possible * 100) if total_possible > 0 else 0
        
        total_percentage += percentage
        student_count += 1
        
        # Find weak subjects (below 50%)
        weak_subjects = []
        for r in results:
            r_percentage = (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0
            if r_percentage < 50:
                weak_subjects.append(r)
        
        # Count students needing attention
        if percentage < 60:
            needs_attention_count += 1
        if percentage < 40:
            at_risk_count += 1
        
        # Add to analyses if matches filter
        should_add = False
        
        if filter_type == 'all':
            should_add = True
        elif filter_type == 'critical' and percentage < 40:
            should_add = True
        elif filter_type == 'warning' and 40 <= percentage < 60:
            should_add = True
        elif filter_type == 'attention' and percentage < 60:
            should_add = True
        
        # Filter by class
        if selected_class and student.student_class != selected_class:
            should_add = False
        
        if should_add:
            # Generate AI Summary
            ai_summary = generate_ai_summary(student, results, percentage, weak_subjects)
            
            # Generate Recommendations
            recommendations = generate_recommendations(student, results, percentage, weak_subjects)
            
            student_analyses.append({
                'student': student,
                'percentage': round(percentage, 2),
                'weak_subjects': weak_subjects,
                'total_attempts': len(results),
                'ai_summary': ai_summary,
                'recommendations': recommendations,
            })
    
    # Sort analyses
    if sort_by == 'lowest':
        student_analyses.sort(key=lambda x: x['percentage'])
    elif sort_by == 'highest':
        student_analyses.sort(key=lambda x: x['percentage'], reverse=True)
    elif sort_by == 'name':
        student_analyses.sort(key=lambda x: x['student'].name)
    
    # Calculate class average
    class_average = (total_percentage / student_count) if student_count > 0 else 0
    
    # Get unique classes
    all_classes = sorted(set(all_classes))
    
    context = {
        'student_analyses': student_analyses,
        'total_students': student_count,
        'needs_attention_count': needs_attention_count,
        'at_risk_count': at_risk_count,
        'class_average': class_average,
        'classes': all_classes,
        'selected_class': selected_class,
        'filter_type': filter_type,
        'sort_by': sort_by,
    }
    
    return render(request, 'dashboard/student_analysis.html', context)


def generate_ai_summary(student, results, percentage, weak_subjects):
    """Generate AI-powered summary for a student"""
    
    total_obtained = sum(r.marks_obtained for r in results)
    total_possible = sum(r.total_marks for r in results)
    
    # Determine performance level
    if percentage < 40:
        level = "critical"
        intro = f"🚨 {student.name} is showing concerning performance with an overall average of {percentage:.1f}%. "
    elif percentage < 60:
        level = "warning"
        intro = f"⚠️ {student.name}'s performance needs improvement. Current average is {percentage:.1f}%. "
    elif percentage < 75:
        level = "good"
        intro = f"👍 {student.name} is performing at a satisfactory level with {percentage:.1f}% average. "
    else:
        level = "excellent"
        intro = f"🌟 {student.name} is performing excellently with {percentage:.1f}% average! "
    
    # Add subject-specific analysis
    subject_analysis = ""
    if weak_subjects:
        weak_names = [f"**{ws.subject.name}** ({ws.marks_obtained}/{ws.total_marks})" for ws in weak_subjects[:3]]
        if len(weak_names) > 1:
            subject_analysis = f" Areas of concern include {', '.join(weak_names[:-1])} and {weak_names[-1]}."
        else:
            subject_analysis = f" Primary area of concern is {weak_names[0]}."
    
    # Add best subject
    best_result = max(results, key=lambda r: (r.marks_obtained / r.total_marks * 100) if r.total_marks > 0 else 0)
    best_percentage = (best_result.marks_obtained / best_result.total_marks * 100) if best_result.total_marks > 0 else 0
    if best_percentage >= 80:
        subject_analysis += f" Shows strong performance in **{best_result.subject.name}** ({best_percentage:.1f}%)."
    
    # Add summary
    if level == "critical":
        summary = "Immediate intervention is required. Student's current trajectory may lead to academic failure."
    elif level == "warning":
        summary = "With targeted improvement in weak areas, student can significantly improve performance."
    elif level == "good":
        summary = "Student is on track. Focus on weak subjects can help achieve distinction."
    else:
        summary = "Excellent performance! Student should be encouraged to maintain this standard."
    
    return intro + subject_analysis + " " + summary


def generate_recommendations(student, results, percentage, weak_subjects):
    """Generate personalized recommendations for a student"""
    
    recommendations = []
    
    # Priority recommendations based on performance
    if percentage < 40:
        recommendations.append({
            'priority': 'high',
            'title': '🔴 Immediate Parent Meeting Required',
            'description': 'Schedule urgent meeting with parents/guardians to discuss academic intervention strategies.'
        })
        recommendations.append({
            'priority': 'high',
            'title': '📚 Mandatory Tutoring Sessions',
            'description': 'Student requires additional support through remedial classes or private tutoring.'
        })
    elif percentage < 60:
        recommendations.append({
            'priority': 'medium',
            'title': '🟡 Schedule Academic Counseling',
            'description': 'Arrange meeting to identify specific learning challenges and set improvement goals.'
        })
    
    # Subject-specific recommendations
    for weak in weak_subjects[:2]:
        weak_percentage = (weak.marks_obtained / weak.total_marks * 100) if weak.total_marks > 0 else 0
        rec_title = f"Focus on {weak.subject.name}"
        
        if weak_percentage < 30:
            rec_desc = f"Critical weakness in {weak.subject.name} (scored {weak.marks_obtained}/{weak.total_marks}). Consider remedial classes."
        elif weak_percentage < 40:
            rec_desc = f"Weak performance in {weak.subject.name}. Recommend extra practice and teacher consultations."
        else:
            rec_desc = f"{weak.subject.name} needs improvement. Suggest focused study plan and regular assessments."
            
        recommendations.append({
            'priority': 'medium' if weak_percentage < 40 else 'low',
            'title': rec_title,
            'description': rec_desc
        })
    
    # General recommendations
    if percentage >= 40:
        recommendations.append({
            'priority': 'low',
            'title': '📖 Establish Study Schedule',
            'description': 'Create a structured daily study routine with dedicated time for each subject.'
        })
    
    recommendations.append({
        'priority': 'low',
        'title': '💪 Encourage Participation',
        'description': 'Promote active engagement in class discussions and practical activities.'
    })
    
    return recommendations[:5]  # Return top 5 recommendations