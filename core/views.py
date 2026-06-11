from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
<<<<<<< HEAD
from django.views.decorators.http import require_http_methods
from .forms import ResultForm
from .models import Result, Student, Subject, Attendance
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
=======
from django.views.decorators.csrf import csrf_exempt
from .forms import (ResultForm, GradeScaleForm, TeacherEvaluationForm, InvoiceQuickCreateForm,
                    SupportTicketForm, CertificateGenerateForm, LessonPlanForm, SyllabusCoverageForm,
                    GradingRubricForm, RubricCriterionForm, ExamSeatingPlanForm, QuestionBankForm,
                    QuestionPaperTemplateForm, ReminderForm, SubscriptionForm, InvoiceForm,
                    CertificateTemplateForm, TicketCommentForm, ParentUserForm,
                    UserRoleForm, UserProfileForm, ResultPublishSessionForm, ResultSessionRemarkForm)
from .models import (
    Result, Student, Subject, Teacher, CourseMaterial, Notification,
    GradeScale, TeacherEvaluation, ActivityLog,
    LessonPlan, SyllabusCoverage,
    GradingRubric, RubricCriterion, RubricScoreEntry, RubricTemplate,
    OnlineExam, Question, ExamAttempt, ExamAnswer,
    ExamSeatingPlan, SeatAllocation,
    TeacherLeave,
    AssignmentSubmission,
    Subscription, Invoice, Certificate, CertificateTemplate,
    APIKey, WebhookEndpoint, WebhookDeliveryLog,
    SupportTicket, TicketComment, SSOProvider, SystemConfig,
    UserProfile, LicenseKey, SystemBackup, UserRole, ParentUser,
    ResultPublishSession, ResultSessionEntry,
    Parent,
)
from core.models import (
    Assignment, Attendance, Exam, Fee, Announcement, StudentNote, MLPrediction,
    EducationLevel, Department, Semester, AcademicYear,
)
# missing new models
from core.models import (
    QRCodeAttendance, FaceAttendance, GPSAttendance, LateEntryLog, AttendanceReport,
    PlagiarismReport, MCQAutoGrade, RecheckingRequest,
    LiveClass, LiveClassAttendance, LiveClassRecording,
    DisciplineRecord, ParticipationScore, BehavioralAnalytics,
    SkillCourse, StudentSkill, Achievement, StudentAchievement, Leaderboard, LeaderboardEntry, DailyStreak,
    StudyGroup, StudyGroupMessage, SharedNote,
    StudentGoal, StudentIDCard, VideoLecture,
    CareerPortalListing, StudentApplication,
    AIQuiz, AILessonPlan,
    ParentNotification, ParentMeeting,
    BusRoute, BusStop, StudentTransportCard, TransportMonitor,
    HostelRoom, HostelAllocation,
    AIRecommendation, AIStudentReport,
    IoTDevice, SmartEnergyLog,
    Institution, InstitutionUser,
    Timetable, TimetableEntry, TimetableConflict, ExamRoom,
)
from django.db.models import Q, Sum, Avg, Count, F, FloatField, ExpressionWrapper, Case, When, Max, Min
from django.http import FileResponse
from django.conf import settings
from django.template import loader
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table as RLTable, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
try:
    import face_recognition
    HAS_FACE_RECOGNITION = True
except ImportError:
    HAS_FACE_RECOGNITION = False
import os
from core.models import UserProfile, LicenseKey, SystemBackup, SystemConfig
from core.models import UserRole, ParentUser, ResultPublishSession, ResultSessionEntry
from django.db.models import Q, Sum, Avg, Count, F, FloatField, ExpressionWrapper, Case, When
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from functools import wraps
>>>>>>> 801959c (Latest Commit)
import json
import qrcode
from io import BytesIO
import base64
from django.contrib import messages

def home_view(request):
    """Landing page - accessible without login"""
    return render(request, 'core/dashboard/home.html')


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
            return render(request, 'core/registration/login.html', {
                'error': 'Invalid username or password'
            })

    return render(request, 'core/registration/login.html')


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
    return render(request, 'core/dashboard/dashboard.html', context)


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
            return render(request, 'core/dashboard/student_dashboard.html', {
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
    
    return render(request, 'core/dashboard/student_dashboard.html', context)


# ➕ ADD MARKS
@login_required
<<<<<<< HEAD
def add_marks(request):
    subjects = Subject.objects.all().values('id', 'name')
    subject_options = list(subjects)
    
    SEMESTER_CHOICES = [
        ('1', 'Semester 1'),
        ('2', 'Semester 2'),
        ('3', 'Semester 3'),
        ('4', 'Semester 4'),
        ('5', 'Semester 5'),
        ('6', 'Semester 6'),
        ('7', 'Semester 7'),
        ('8', 'Semester 8'),
    ]
    
    if request.method == "POST":
        form = ResultForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            subject = form.cleaned_data['subject']
            terminal = request.POST.get('terminal', '1st')
            marks_obtained = form.cleaned_data['marks_obtained']
            total_marks = form.cleaned_data.get('total_marks', 100)
            
            existing = Result.objects.filter(
                student_id=student.id,
                subject_id=subject.id,
                terminal=terminal
            ).first()
            
            if existing:
                existing.marks_obtained = marks_obtained
                existing.total_marks = total_marks
                existing.save()
                messages.success(request, f"Marks updated successfully for {student.name}!")
            else:
                Result.objects.create(
                    student=student,
                    subject=subject,
                    terminal=terminal,
                    marks_obtained=marks_obtained,
                    total_marks=total_marks
                )
                messages.success(request, "Marks added successfully!")
            
            return redirect('/marks-list/')
        else:
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    field_label = form.fields[field].label if form.fields[field].label else field
                    error_messages.append(f"{field_label}: {error}")
            
            if not error_messages:
                error_messages = ["Please correct the errors below."]
            
            for msg in error_messages:
                messages.error(request, msg)
    else:
        form = ResultForm()
=======
def student_gpa_forecasting(request):
    """GPA / CGPA forecasting, goals, recovery planner, and risk analysis for students."""
    from core.gpa_forecasting import build_gpa_forecast

    if get_teacher_profile(request.user):
        messages.info(request, 'GPA Forecasting is available on the student dashboard.')
        return redirect('core:dashboard')

    student = get_student_for_user(request.user)
    if not student:
        messages.error(request, 'Student profile not found.')
        return redirect('core:dashboard')

    target_raw = request.GET.get('target', '3.5').strip()
    try:
        target_cgpa = max(0.0, min(4.0, float(target_raw)))
    except (ValueError, TypeError):
        target_cgpa = 3.5

    forecast = build_gpa_forecast(student, target_cgpa)
    context = {
        'student': student,
        'user': request.user,
        'is_student': True,
        'target_cgpa': target_cgpa,
        **forecast,
    }
    return render(request, 'core/dashboard/gpa_forecasting.html', context)


@login_required
def student_analytics(request):
    """Detailed marks analytics and charts for the logged-in student."""
    if get_teacher_profile(request.user):
        messages.info(request, 'Subject analytics is available on the teacher dashboard.')
        return redirect('core:subject_analytics')

    student = get_student_for_user(request.user)
    if not student:
        messages.error(request, 'Student profile not found.')
        return redirect('core:dashboard')

    terminal = request.GET.get('terminal', 'all')
    subject_id_raw = request.GET.get('subject', '').strip()
    terminals = ['1st', '2nd', '3rd', 'Final']
    run_terminals = terminals if terminal == 'all' else (
        [terminal] if terminal in terminals else terminals
    )

    subject_id = int(subject_id_raw) if subject_id_raw.isdigit() else None
    filtered_qs = Result.objects.filter(student=student).select_related('subject')
    if subject_id is not None:
        filtered_qs = filtered_qs.filter(subject_id=subject_id)

    stats_qs = filtered_qs
    if terminal != 'all' and terminal in terminals:
        stats_qs = stats_qs.filter(terminal=terminal)

    pct_list = []
    for r in stats_qs:
        pct = _analytics_result_pct(r)
        if pct is not None:
            pct_list.append(pct)

    total = len(pct_list)
    avg_pct = round(sum(pct_list) / total, 1) if total else 0
    highest_pct = round(max(pct_list), 1) if pct_list else 0
    lowest_pct = round(min(pct_list), 1) if pct_list else 0
    pass_count = sum(1 for p in pct_list if p >= 40)
    pass_rate = round((pass_count / total) * 100, 1) if total else 0
    below_40 = sum(1 for p in pct_list if p < 40)

    insight_lines = [
        f'Analysing {student.name} (Class {student.student_class} — Section {student.section}).',
    ]
    if below_40 > 0:
        s = 's' if below_40 > 1 else ''
        insight_lines.append(
            f'{below_40} result{s} below 40% — focus revision on weaker subjects.'
        )
    if avg_pct >= 80:
        insight_lines.append(f'Excellent average at {avg_pct}%.')
    elif avg_pct >= 70:
        insight_lines.append(f'Good progress — average is {avg_pct}%.')
    elif avg_pct >= 50:
        insight_lines.append(f'Average is {avg_pct}%. Focus on weaker subjects.')
    elif total:
        insight_lines.append(f'Average is {avg_pct}%. Needs attention — review study plan.')

    seen_subject_ids = set()
    chart_subjects = []
    for r in filtered_qs.order_by('subject__name'):
        if r.subject_id not in seen_subject_ids:
            seen_subject_ids.add(r.subject_id)
            chart_subjects.append(r.subject)

    available_subjects = list(
        Subject.objects.filter(result__student=student).distinct().order_by('name')
    )
    subject_colors = ANALYTICS_CHART_COLORS
    term_colors = ANALYTICS_TERMINAL_COLORS

    terminal_wise_datasets = []
    for i, subj in enumerate(chart_subjects):
        color = subject_colors[i % len(subject_colors)]
        terminal_wise_datasets.append(
            _analytics_line_dataset(
                subj.name,
                [
                    _analytics_avg_pct(filtered_qs.filter(subject=subj, terminal=t))
                    for t in run_terminals
                ],
                color,
                fill=False,
            )
        )

    subject_wise_datasets = []
    for t in run_terminals:
        color = term_colors.get(t, subject_colors[len(subject_wise_datasets) % len(subject_colors)])
        subject_wise_datasets.append(
            _analytics_line_dataset(
                f'{t} Terminal',
                [
                    _analytics_avg_pct(filtered_qs.filter(subject=subj, terminal=t))
                    for subj in chart_subjects
                ],
                color,
                fill=False,
            )
        )

    dist_bins = [
        ('0–39% (Fail)', 0, 39),
        ('40–59%', 40, 59),
        ('60–79%', 60, 79),
        ('80–100%', 80, 100),
    ]
    distribution_chart = {
        'labels': [b[0] for b in dist_bins],
        'datasets': [{
            'label': 'Your results',
            'data': [
                sum(1 for p in pct_list if lo <= p <= hi)
                for _, lo, hi in dist_bins
            ],
            'backgroundColor': ['#ef4444', '#f59e0b', '#10b981', '#6366f1'],
            'borderRadius': 6,
        }],
    }

    pass_fail_chart = {
        'labels': ['Pass (≥40%)', 'Fail (<40%)'],
        'datasets': [{
            'data': [pass_count, total - pass_count],
            'backgroundColor': ['#10b981', '#ef4444'],
            'borderWidth': 0,
        }],
    }

    term_indices = list(range(1, len(run_terminals) + 1))
    student_pcts = [
        _analytics_avg_pct(filtered_qs.filter(terminal=t))
        for t in run_terminals
    ]
    reg_line, reg_slope = _analytics_linear_regression(term_indices, student_pcts)
    regression_chart = {
        'labels': run_terminals,
        'scatter': [{'x': i, 'y': y} for i, y in zip(term_indices, student_pcts) if y is not None],
        'regression': reg_line,
        'slope': reg_slope,
        'title': f'{student.name} — regression trend',
    }

    section_results = Result.objects.filter(
        student__student_class=student.student_class,
        student__section=student.section,
    )
    class_avg_by_term = [
        _analytics_avg_pct(section_results.filter(terminal=t))
        for t in run_terminals
    ]
    student_terminal_chart = {
        'labels': run_terminals,
        'datasets': [{
            'label': 'Your average',
            'data': student_pcts,
            'backgroundColor': [
                _analytics_hex_rgba(term_colors.get(t, '#6366f1'), 0.85)
                for t in run_terminals
            ],
            'borderColor': [term_colors.get(t, '#6366f1') for t in run_terminals],
            'borderWidth': 2,
            'borderRadius': 6,
        }],
    }

    comparison_chart = {
        'labels': run_terminals,
        'datasets': [
            {
                'label': 'Your average',
                'data': student_pcts,
                'backgroundColor': _analytics_hex_rgba('#6366f1', 0.85),
                'borderColor': '#6366f1',
                'borderWidth': 2,
                'borderRadius': 6,
            },
            {
                'label': 'Section average',
                'data': class_avg_by_term,
                'backgroundColor': _analytics_hex_rgba('#f59e0b', 0.85),
                'borderColor': '#f59e0b',
                'borderWidth': 2,
                'borderRadius': 6,
            },
        ],
    }

    breakdown_terminal = run_terminals[-1] if terminal == 'all' else terminal
    subject_breakdown_chart = {
        'labels': [s.name for s in chart_subjects],
        'datasets': [{
            'label': f'{breakdown_terminal} Terminal %' if terminal != 'all' else 'Latest terminal %',
            'data': [
                _analytics_avg_pct(
                    filtered_qs.filter(subject=subj, terminal=breakdown_terminal)
                )
                for subj in chart_subjects
            ],
            'backgroundColor': [
                subject_colors[i % len(subject_colors)] for i in range(len(chart_subjects))
            ],
        }],
    }

    trend_rows = []
    for subj in chart_subjects:
        mbt = {}
        for r in filtered_qs.filter(subject=subj):
            pct = _analytics_result_pct(r)
            if pct is not None:
                mbt[r.terminal] = pct
        prev_vals = [mbt.get(t) for t in run_terminals if mbt.get(t) is not None]
        if len(prev_vals) >= 2:
            diff = prev_vals[-1] - prev_vals[-2]
            arrow = 'up' if diff > 0.5 else ('down' if diff < -0.5 else 'same')
        else:
            arrow = 'same'
        marks_list = [mbt.get(t) for t in run_terminals]
        trend_rows.append({
            'subject': subj,
            'marks_list': marks_list,
            'mark_tuples': list(zip(run_terminals, marks_list)),
            'arrow': arrow,
        })

    return render(request, 'core/dashboard/student_analytics.html', {
        'student': student,
        'user': request.user,
        'is_student': True,
        'subject_obj': Subject.objects.filter(id=subject_id).first() if subject_id else None,
        'subject_id': subject_id_raw,
        'terminal': terminal,
        'terminals': terminals,
        'run_terminals': run_terminals,
        'available_subjects': available_subjects,
        'total': total,
        'avg_pct': avg_pct,
        'highest_pct': highest_pct,
        'lowest_pct': lowest_pct,
        'pass_rate': pass_rate,
        'pass_count': pass_count,
        'below_40': below_40,
        'insight_lines': insight_lines,
        'trend_rows': trend_rows,
        'terminal_wise_chart': {
            'labels': run_terminals,
            'datasets': terminal_wise_datasets,
        },
        'subject_wise_chart': {
            'labels': [s.name for s in chart_subjects],
            'datasets': subject_wise_datasets,
        },
        'distribution_chart': distribution_chart,
        'regression_chart': regression_chart,
        'pass_fail_chart': pass_fail_chart,
        'student_terminal_chart': student_terminal_chart,
        'comparison_chart': comparison_chart,
        'subject_breakdown_chart': subject_breakdown_chart,
        'chart_color_legend': {
            'subjects': [
                {'name': s.name, 'color': subject_colors[i % len(subject_colors)]}
                for i, s in enumerate(chart_subjects)
            ],
            'terminals': [
                {
                    'name': f'{t} Terminal',
                    'color': term_colors.get(t, subject_colors[i % len(subject_colors)]),
                }
                for i, t in enumerate(run_terminals)
            ],
        },
    })


# 👨‍🏫 TEACHER DASHBOARD
@teacher_required
def teacher_dashboard(request):
    """Teacher dashboard with restricted access to their subjects"""
    teacher = getattr(request, 'teacher', None) or get_teacher_profile(request.user)
    request.teacher = teacher

    # Get teacher's subjects
    teacher_subjects = teacher.subjects.all()

    # Get students assigned to this teacher
    teacher_students = teacher.students.all()

    # Get results for teacher's subjects and students
    teacher_results = Result.objects.filter(
        subject__in=teacher_subjects,
        student__in=teacher_students
    ).select_related('student', 'subject')

    # Calculate stats for teacher's data only
    avg_marks = 0
    if teacher_results.exists():
        total = sum(r.marks_obtained for r in teacher_results)
        avg_marks = round(total / teacher_results.count(), 1)

    context = {
        'teacher': teacher,
        'total_students': teacher_students.count(),
        'total_subjects': teacher_subjects.count(),
        'total_marks': teacher_results.count(),
        'average_marks': avg_marks,
        'user': request.user,
        'is_teacher': True,
        'show_add_marks': True,
        'teacher_subjects': teacher_subjects,
        'teacher_students': teacher_students[:10],  # Show recent students
        'no_subjects_assigned': not teacher_subjects.exists(),
        'no_students_assigned': not teacher_students.exists(),
    }
    return render(request, 'core/dashboard/teacher_dashboard.html', context)


# 👥 TEACHERS LIST - Admin view to see all teachers
@login_required
def teachers_list(request):
    """Admin view to list all teachers and their assignments"""
    if is_teacher(request.user):
        # Teachers can't access this view
        messages.error(request, "Access denied. Admin privileges required.")
        return redirect('/dashboard/')

    # Get all teachers with their assignments
    teachers = Teacher.objects.select_related('user').prefetch_related('subjects', 'students').filter(is_active=True)

    # Calculate statistics
    total_teachers = teachers.count()
    teachers_with_subjects = teachers.filter(subjects__isnull=False).distinct().count()
    teachers_with_students = teachers.filter(students__isnull=False).distinct().count()

    context = {
        'teachers': teachers,
        'total_teachers': total_teachers,
        'teachers_with_subjects': teachers_with_subjects,
        'teachers_with_students': teachers_with_students,
        'user': request.user,
        'is_admin': True,
    }

    return render(request, 'core/dashboard/teachers_list.html', context)


# ➕ ADD MARKS - Teachers only
@teacher_required
def add_marks(request):
    from core.models import TERMINAL_CHOICES

    teacher = getattr(request, 'teacher', None) or get_teacher_profile(request.user)
    request.teacher = teacher

    subject_options = list(teacher.subjects.all().order_by('name').values('id', 'name', 'total_marks', 'code'))
    student_rows = list(teacher.students.all().order_by('name').values('id', 'name', 'roll_number', 'student_class', 'section'))
    classes = sorted({s['student_class'] for s in student_rows if s['student_class']})
    sections_by_class = {}
    for s in student_rows:
        cls = s['student_class']
        if cls not in sections_by_class:
            sections_by_class[cls] = []
        if s['section'] and s['section'] not in sections_by_class[cls]:
            sections_by_class[cls].append(s['section'])
    for cls in sections_by_class:
        sections_by_class[cls].sort()
    subject_total_map = {str(s['id']): s['total_marks'] for s in subject_options}
    subject_name_map = {str(s['id']): s['name'] for s in subject_options}

    if not subject_options:
        messages.warning(request, 'No subjects assigned to you yet. Ask admin to assign subjects in the admin panel.')
    if not student_rows:
        messages.warning(request, 'No students assigned to you yet. Ask admin to assign students in the admin panel.')
>>>>>>> 801959c (Latest Commit)

    return render(request, 'core/dashboard/add_marks.html', {
        'form': form,
        'subject_options': subject_options,
<<<<<<< HEAD
        'semester_choices': SEMESTER_CHOICES
=======
        'student_rows': student_rows,
        'classes': classes,
        'sections_by_class': sections_by_class,
        'is_teacher': True,
        'teacher': teacher,
        'subject_total_map_json': json.dumps(subject_total_map),
        'subject_name_map_json': json.dumps(subject_name_map),
        'terminal_choices': TERMINAL_CHOICES,
        'has_subjects': bool(subject_options),
        'has_students': bool(student_rows),
>>>>>>> 801959c (Latest Commit)
    })


# 📊 API: Bulk Add Marks
@login_required
@require_http_methods(["POST"])
def add_marks_bulk(request):
    try:
        data = json.loads(request.body)
        marks_list = data.get('marks', [])
        
        if not marks_list:
            return JsonResponse({'success': False, 'message': 'No marks data provided'})
        
        errors = []
        success_count = 0
        updated_count = 0
        
        for idx, mark_data in enumerate(marks_list):
            student_id = mark_data.get('student')
            subject_id = mark_data.get('subject')
            terminal = mark_data.get('terminal', '1st')
            marks_obtained = mark_data.get('marks_obtained')
            total_marks = mark_data.get('total_marks', 100)
            
            if not student_id or not subject_id:
                errors.append(f"Row {idx + 1}: Student and Subject are required")
                continue
            
            if marks_obtained is None:
                errors.append(f"Row {idx + 1}: Marks obtained is required")
                continue
            
            existing = Result.objects.filter(
                student_id=student_id,
                subject_id=subject_id,
                terminal=terminal
            ).first()
            
            if existing:
                existing.marks_obtained = float(marks_obtained)
                existing.total_marks = float(total_marks)
                existing.save()
                updated_count += 1
            else:
                Result.objects.create(
                    student_id=student_id,
                    subject_id=subject_id,
                    terminal=terminal,
                    marks_obtained=float(marks_obtained),
                    total_marks=float(total_marks)
                )
                success_count += 1
        
        if errors:
            return JsonResponse({
                'success': True,
                'message': f'{success_count} new marks added, {updated_count} updated. {len(errors)} entries have issues.',
                'errors': errors
            })
        
        if updated_count > 0:
            message = f'{success_count} new marks added, {updated_count} updated successfully!'
        else:
            message = f'{success_count} marks added successfully!'
        
        return JsonResponse({
            'success': True,
            'message': message
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


# 📤 API: Get Student Info
@login_required
def student_info(request, student_id):
    try:
        student = get_object_or_404(Student, id=student_id)
        image_url = None
        if student.image:
            image_url = student.image.url
        
        return JsonResponse({
            'success': True,
            'student': {
                'id': student.id,
                'name': student.name,
                'roll_number': student.roll_number,
                'class': student.student_class,
                'section': student.section,
                'image_url': image_url
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=404)


# 📋 MARKS LIST
@login_required
def marks_list(request):
    all_marks = Result.objects.all().select_related('student', 'subject')
    return render(request, 'core/dashboard/marks_list.html', {'result': all_marks})

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
        student_name = result.student.name
        subject_name = result.subject.name
        result.delete()
        return JsonResponse({'success': True, 'message': f'Marks for {student_name} in {subject_name} deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)


# QR CODE ATTENDANCE SYSTEM 

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
    
    return render(request, 'core/dashboard/qr_codes.html', {'qr_codes': qr_codes_list})


#SINGLE STUDENT QR CODE - For printing individual QR codes
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
    return render(request, 'core/dashboard/qr_scanner.html')


#QR SCAN PROCESS - Process scanned QR code data
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


#ATTENDANCE LIST - View attendance records
@login_required
def attendance_list(request):
    """Display attendance records"""
    attendance_records = Attendance.objects.select_related('student').all()[:100]
    return render(request, 'core/dashboard/attendance_list.html', {'attendance': attendance_records})


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
    return render(request, 'core/dashboard/attendance_report.html', context)


#MOBILE SCANNER - Standalone mobile-friendly scanner
def mobile_scanner(request):
    """Mobile-friendly QR scanner for app integration"""
    return render(request, 'core/dashboard/mobile_scanner.html')


#REGENERATE ALL QR CODES
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


#CHART DATA API
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


def _marksheet_verify_payload(doc_id):
    """Resolve marksheet authenticity from doc_id against live Result records."""
    import re
    from django.utils import timezone

    valid_format = bool(re.match(r'^ACAD-\d{8}-\d+-[\w-]+$', doc_id))
    parts = doc_id.split('-') if valid_format else []
    student_id = parts[2] if len(parts) >= 3 and parts[2].isdigit() else None
    student = Student.objects.filter(id=student_id).first() if student_id else None
    terminal_raw = '-'.join(parts[3:]) if len(parts) > 3 else ''
    if terminal_raw in ('1st', '2nd', '3rd', 'Final'):
        terminal_display = terminal_raw
    elif terminal_raw:
        terminal_display = terminal_raw.replace('-', ' ').title()
    else:
        terminal_display = 'Exam'

    results = []
    has_marks = False
    if student and terminal_raw:
        terminal_key = terminal_raw if terminal_raw in ('1st', '2nd', '3rd', 'Final') else None
        if not terminal_key and terminal_raw == 'all':
            results = list(Result.objects.filter(student=student).select_related('subject'))
            has_marks = bool(results)
        elif terminal_key:
            results = list(
                Result.objects.filter(student=student, terminal=terminal_key).select_related('subject')
            )
            has_marks = bool(results)

    all_passed = False
    overall_percentage = 0
    if results:
        total_obt = sum(r.marks_obtained for r in results)
        total_pos = sum(r.total_marks for r in results)
        overall_percentage = round((total_obt / total_pos * 100) if total_pos > 0 else 0, 1)
        all_passed = all(
            (r.marks_obtained / r.total_marks * 100) >= 40 for r in results if r.total_marks > 0
        )

    is_valid = valid_format and (student is not None) and has_marks
    return {
        'valid': is_valid,
        'doc_id': doc_id,
        'student_id': student.id if student else None,
        'student_name': student.name if student else None,
        'student_class': student.student_class if student else None,
        'student_section': student.section if student else None,
        'terminal': terminal_raw,
        'terminal_display': terminal_display,
        'subjects_count': len(results),
        'overall_percentage': overall_percentage,
        'result': 'PASS' if all_passed else ('FAIL' if results else None),
        'verified_at': timezone.now().isoformat(),
    }


# MARK SHEET VIEW
@login_required
def mark_sheet(request, student_id=None, terminal=None):
    """Generate official mark sheet for a student with terminal filter"""
    import qrcode
    from io import BytesIO
    import base64
    from datetime import datetime
<<<<<<< HEAD
=======
    from django.urls import reverse

    if not student_id:
        return redirect('core:select_mark_sheet')

    # Check teacher permissions
    teacher = get_teacher_profile(request.user)
    if teacher and not teacher.is_admin:
        student = get_object_or_404(Student, id=student_id)
        if not teacher.students.filter(id=student.id).exists():
            return JsonResponse({'success': False, 'message': 'Access denied'}, status=403)
>>>>>>> 801959c (Latest Commit)
    
    # Get all students for selection dropdown
    students = Student.objects.all().order_by('name')
    
    if student_id and terminal:
        # Get specific student's results for a specific terminal
        results = Result.objects.filter(
            student_id=student_id,
            terminal=terminal
        ).select_related('student', 'subject').order_by('subject__name')
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
    
    from core.grading_utils import summarize_terminal_results

    summary = summarize_terminal_results(results)
    results_with_grades = summary['student_results']
    total_subjects = summary['total_subjects']
    total_marks_obtained = summary['total_marks_obtained']
    total_marks = summary['total_marks']
    overall_percentage = summary['overall_percentage']
    gpa = summary['gpa']
    all_passed = summary['all_passed']
    overall_grade = summary['overall_grade']
    
    # Get current academic year
    academic_year = datetime.now().year
    terminal_slug = (terminal or 'all').replace(' ', '-')

    # Generate document ID & verification QR (scan → verify page → Soch College website)
    doc_id = f"ACAD-{datetime.now().strftime('%Y%m%d')}-{student_id}-{terminal_slug}"
    verify_url = request.build_absolute_uri(
        reverse('core:marksheet_verify', kwargs={'doc_id': doc_id})
    )
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#0a0a0a", back_color="white")
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    college_qr_code = base64.b64encode(buffer.getvalue()).decode()
    
    verify_api_url = request.build_absolute_uri(
        reverse('core:marksheet_verify_api', kwargs={'doc_id': doc_id})
    )

    context = {
        'students': students,
        'student_results': results_with_grades,
        'selected_student': selected_student,
        'selected_terminal': terminal,
        'total_subjects': total_subjects,
        'total_marks_obtained': total_marks_obtained,
        'total_marks': total_marks,
        'overall_percentage': round(overall_percentage, 2),
        'gpa': gpa,
        'all_passed': all_passed,
        'overall_grade': overall_grade,
        'academic_year': f"{academic_year}-{academic_year + 1}",
        'college_qr_code': college_qr_code,
        'doc_id': doc_id,
<<<<<<< HEAD
=======
        'verify_url': verify_url,
        'verify_api_url': verify_api_url,
        'soch_college_url': 'https://sochcollege.edu.np/',
        'is_teacher': teacher is not None,
        'teacher': teacher,
>>>>>>> 801959c (Latest Commit)
    }

    return render(request, 'core/dashboard/mark_sheet.html', context)


def marksheet_verify_api(request, doc_id):
    """Public JSON endpoint — live authenticity check for QR scans and on-page status."""
    payload = _marksheet_verify_payload(doc_id)
    status = 200 if payload['valid'] else 404
    return JsonResponse(payload, status=status)


def marksheet_verify(request, doc_id):
    """Public QR verification — confirms authenticity then redirects to Soch College."""
    from datetime import datetime

    payload = _marksheet_verify_payload(doc_id)
    verified_at = datetime.fromisoformat(payload['verified_at'])

    return render(request, 'core/dashboard/marksheet_verify.html', {
        'doc_id': doc_id,
        'is_valid': payload['valid'],
        'student_name': payload['student_name'],
        'terminal_display': payload['terminal_display'],
        'subjects_count': payload['subjects_count'],
        'overall_percentage': payload['overall_percentage'],
        'result': payload['result'],
        'verified_at': verified_at,
        'soch_college_url': 'https://sochcollege.edu.np/',
    })


# SELECT STUDENT FOR MARK SHEET
@login_required
def select_mark_sheet(request):
    """Student selection page for mark sheet generation"""
<<<<<<< HEAD
    students = Student.objects.all().order_by('name')
    
    # Get unique terminals
    terminals = Result.objects.values_list('terminal', flat=True).distinct()
    
    context = {
        'students': students,
        'terminals': terminals,
    }
    
    return render(request, 'core/dashboard/select_mark_sheet.html', context)
=======
    teacher = get_teacher_profile(request.user)

    if teacher and not teacher.is_admin:
        students_qs = teacher.students.all().order_by('name')
    else:
        students_qs = Student.objects.all().order_by('name')

    student_rows = list(students_qs.values(
        'id', 'name', 'roll_number', 'student_class', 'section'
    ))
    classes = sorted({s['student_class'] for s in student_rows if s['student_class']})
    sections_by_class = {}
    for s in student_rows:
        cls = s['student_class']
        if cls not in sections_by_class:
            sections_by_class[cls] = []
        if s['section'] and s['section'] not in sections_by_class[cls]:
            sections_by_class[cls].append(s['section'])
    for cls in sections_by_class:
        sections_by_class[cls].sort()

    terminals = ['1st', '2nd', '3rd', 'Final']

    return render(request, 'core/dashboard/select_mark_sheet.html', {
        'student_rows': student_rows,
        'classes': classes,
        'sections_by_class': sections_by_class,
        'terminals': terminals,
        'is_teacher': teacher is not None,
        'teacher': teacher,
    })
>>>>>>> 801959c (Latest Commit)


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
    
    return render(request, 'core/dashboard/student_analysis.html', context)


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


# AI INTEGRATION VIEWS

@login_required
def ai_analyze_student(request, student_id):
    """API endpoint for real-time AI analysis of a student"""
    from core.ai_integration import ai_integration
    from core.models import Attendance
    
    student = get_object_or_404(Student, id=student_id)
    results = student.result_set.all()
    attendance_count = Attendance.objects.filter(student=student).count()
    
    analysis = ai_integration.analyze_student_performance(student, results, attendance_count)
    
    return JsonResponse({
        'success': True,
        'student': {
            'id': student.id,
            'name': student.name,
            'roll_number': student.roll_number,
            'class': student.student_class
        },
        'analysis': analysis
    })


@login_required
def send_student_notification(request, student_id):
    """Send AI analysis notification to a specific student"""
    from core.ai_integration import ai_integration
    from core.models import Attendance
    from django.views.decorators.http import require_http_methods
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
    
    student = get_object_or_404(Student, id=student_id)
    results = student.result_set.all()
    attendance_count = Attendance.objects.filter(student=student).count()
    
    analysis = ai_integration.analyze_student_performance(student, results, attendance_count)
    
    method = request.POST.get('method', 'email')
    sent = ai_integration.send_student_notification(student, analysis, method=method)
    
    if sent:
        return JsonResponse({'success': True, 'message': f'Notification sent to {student.name}'})
    else:
        return JsonResponse({'success': False, 'message': 'Failed to send notification. Check email configuration.'})


@login_required
def notify_all_students(request):
    """Notify all students who need attention (below threshold)"""
    from core.ai_integration import automation
    from django.views.decorators.http import require_http_methods
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'Only POST method allowed'}, status=405)
    
    threshold = float(request.POST.get('threshold', 60))
    notified = automation.notify_students_needing_attention(threshold=threshold)
    
    return JsonResponse({
        'success': True,
        'message': f'Notifications sent to {len(notified)} students',
        'notified': notified
    })


@login_required
def daily_report(request):
    """Get daily summary report"""
    from core.ai_integration import automation
    
    report = automation.generate_daily_report()
    
    return JsonResponse({
        'success': True,
        'report': report
    })


@login_required
@require_http_methods(["POST"])
def change_password(request):
    """Allow students to change their password"""
    try:
        data = json.loads(request.body)
<<<<<<< HEAD
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        if not current_password or not new_password:
            return JsonResponse({'success': False, 'message': 'Both passwords are required'}, status=400)
        
        if len(new_password) < 4:
            return JsonResponse({'success': False, 'message': 'Password must be at least 4 characters'}, status=400)
        
        user = request.user
        
        # Verify current password
        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Current password is incorrect'}, status=400)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Re-login the user with new password
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)
        
        return JsonResponse({'success': True, 'message': 'Password changed successfully!'})
        
=======
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)

    attendance_data = data.get('attendance', [])
    marks_data = data.get('marks', [])

    summary = {'attendance_created': 0, 'attendance_updated': 0, 'attendance_errors': 0,
               'marks_created': 0, 'marks_updated': 0, 'marks_errors': 0, 'errors': []}

    for att_entry in attendance_data:
        student_id = att_entry.get('student_id')
        status = att_entry.get('status', 'present')
        date_str = att_entry.get('date', '')
        if not student_id or not date_str:
            summary['attendance_errors'] += 1
            summary['errors'].append(f'Attendance: missing student_id or date')
            continue
        try:
            student = Student.objects.get(id=student_id)
            att_date = date.fromisoformat(date_str)
            subj_id = att_entry.get('subject_id')
            subj = Subject.objects.get(id=subj_id) if subj_id else None
            att, created = Attendance.objects.update_or_create(
                student=student, subject=subj, date=att_date,
                defaults={
                    'status': status,
                    'recorded_by': teacher if teacher else None,
                },
            )
            if created:
                summary['attendance_created'] += 1
            else:
                summary['attendance_updated'] += 1
        except (Student.DoesNotExist, Subject.DoesNotExist, ValueError) as e:
            summary['attendance_errors'] += 1
            summary['errors'].append(f'Attendance student {student_id}: {str(e)}')

    for mark_entry in marks_data:
        student_id = mark_entry.get('student_id')
        subject_id = mark_entry.get('subject_id')
        terminal = mark_entry.get('terminal', '1st')
        marks_obtained = mark_entry.get('marks_obtained')
        total_marks = mark_entry.get('total_marks', 100)

        if not student_id or not subject_id or marks_obtained is None:
            summary['marks_errors'] += 1
            summary['errors'].append(f'Marks: missing required fields')
            continue

        try:
            student = Student.objects.get(id=student_id)
            subject = Subject.objects.get(id=subject_id)
            result, created = Result.objects.update_or_create(
                student=student, subject=subject, terminal=terminal,
                defaults={'marks_obtained': float(marks_obtained), 'total_marks': float(total_marks)},
            )
            if created:
                summary['marks_created'] += 1
            else:
                summary['marks_updated'] += 1
        except (Student.DoesNotExist, Subject.DoesNotExist, ValueError) as e:
            summary['marks_errors'] += 1
            summary['errors'].append(f'Marks student {student_id}: {str(e)}')

    total_errors = summary['attendance_errors'] + summary['marks_errors']
    if total_errors == 0:
        return JsonResponse({'success': True, 'message': 'Sync completed successfully.', 'summary': summary})
    return JsonResponse({'success': True, 'message': f'Synced with {total_errors} errors.', 'summary': summary})


# %% T8 SMART QUESTION BANK %%
@teacher_required
def question_bank(request):
    from core.models import QuestionBank, QUESTION_TYPE_CHOICES, DIFFICULTY_CHOICES
    qs = QuestionBank.objects.filter(teacher=request.teacher).select_related("subject")
    subject_id   = request.GET.get("subject", "").strip()
    chapter      = request.GET.get("chapter", "").strip()
    difficulty   = request.GET.get("difficulty", "").strip()
    qtype        = request.GET.get("type", "").strip()
    if subject_id:   qs = qs.filter(subject_id=subject_id)
    if chapter:      qs = qs.filter(chapter__icontains=chapter)
    if difficulty:   qs = qs.filter(difficulty=difficulty)
    if qtype:        qs = qs.filter(question_type=qtype)

    if request.GET.get("export") == "csv":
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = "attachment; filename=question_bank.csv"
        writer = csv.writer(response)
        writer.writerow(["Subject", "Type", "Question", "Options", "Correct", "Difficulty", "Chapter", "Marks"])
        for q in qs:
            opts = "; ".join("{key}: {text}".format(key=o.get("key",""), text=o.get("text","")) for o in (q.options or []))
            writer.writerow([q.subject.code, q.get_question_type_display(), q.question_text,
                             opts, q.correct_answer, q.get_difficulty_display(), q.chapter, q.marks])
        return response

    subjects = request.teacher.subjects.all()
    chapters = sorted(set(QuestionBank.objects.filter(teacher=request.teacher)
                         .values_list("chapter", flat=True).exclude(chapter="")))

    context = {
        "questions": qs, "subjects": subjects, "chapters": chapters,
        "difficulties": DIFFICULTY_CHOICES, "qtypes": QUESTION_TYPE_CHOICES,
        "filter_subject": subject_id, "filter_chapter": chapter,
        "filter_difficulty": difficulty, "filter_type": qtype,
    }
    return render(request, "core/dashboard/question_bank.html", context)


def _qb_form(request, qid=None):
    """Shared form handler for question_bank_add and question_bank_edit"""
    from core.models import QuestionBank, QUESTION_TYPE_CHOICES, DIFFICULTY_CHOICES
    question = None
    if qid:
        question = get_object_or_404(QuestionBank, id=qid, teacher=request.teacher)

    if request.method == "POST":
        subject_id     = request.POST.get("subject")
        question_text  = request.POST.get("question_text", "").strip()
        question_type  = request.POST.get("question_type", "")
        options_raw    = request.POST.get("options_json", "[]")
        correct_answer = request.POST.get("correct_answer", "").strip()
        difficulty     = request.POST.get("difficulty", "medium")
        chapter        = request.POST.get("chapter", "").strip()
        marks          = int(request.POST.get("marks") or 1)
        tags           = request.POST.get("tags", "").strip()
        try:
            options = json.loads(options_raw)
        except (json.JSONDecodeError, ValueError):
            options = question.options if question else []

        if qid:
            question.subject_id = subject_id
            question.question_text = question_text
            question.question_type = question_type
            question.options = options
            question.correct_answer = correct_answer
            question.difficulty = difficulty
            question.chapter = chapter
            question.marks = marks
            question.tags = tags
            question.save()
            messages.success(request, "Question updated successfully.")
        else:
            subject = get_object_or_404(Subject, id=subject_id)
            QuestionBank.objects.create(
                teacher=request.teacher, subject=subject,
                question_text=question_text, question_type=question_type,
                options=options, correct_answer=correct_answer,
                difficulty=difficulty, chapter=chapter, marks=marks, tags=tags,
            )
            messages.success(request, "Question added successfully.")
        return redirect("core:question_bank")

    subjects = request.teacher.subjects.all()
    ctx = {
        "question": question, "subjects": subjects,
        "qtypes": QUESTION_TYPE_CHOICES, "difficulties": DIFFICULTY_CHOICES,
        "options_json": json.dumps(question.options or []) if question else "[]",
    }
    return render(request, "core/dashboard/question_bank_add.html", ctx)


@teacher_required
def question_bank_add(request):
    return _qb_form(request, qid=None)


@teacher_required
def question_bank_edit(request, qid):
    return _qb_form(request, qid=qid)


@teacher_required
def question_bank_delete(request, qid):
    question = get_object_or_404(QuestionBank, id=qid, teacher=request.teacher)
    question.delete()
    messages.success(request, "Question deleted successfully.")
    return redirect("core:question_bank")


@teacher_required
def question_bank_import(request):
    from core.models import QuestionBank
    if request.method == "POST":
        uploaded = request.FILES.get("file")
        if not uploaded:
            messages.error(request, "Please select a file.")
            return redirect("core:question_bank_import")

        try:
            data = json.loads(uploaded.read().decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            try:
                data = json.loads(uploaded.read().decode("latin-1", errors="replace"))
            except json.JSONDecodeError:
                messages.error(request, "Invalid file format. Upload a valid JSON file.")
                return redirect("core:question_bank_import")

        if not isinstance(data, list):
            messages.error(request, "JSON root must be an array of question objects.")
            return redirect("core:question_bank_import")

        created = 0
        for item in data:
            subj_code = item.get("subject") or item.get("subject_code")
            subj = Subject.objects.filter(code=subj_code).first() if subj_code else None
            if not subj or not request.teacher.subjects.filter(id=subj.id).exists():
                continue
            QuestionBank.objects.update_or_create(
                subject=subj,
                question_text=item.get("question_text", "").strip(),
                defaults={
                    "teacher": request.teacher,
                    "question_type": item.get("question_type", "short_answer"),
                    "options": item.get("options", []),
                    "correct_answer": item.get("correct_answer", ""),
                    "difficulty": item.get("difficulty", "medium"),
                    "chapter": item.get("chapter", ""),
                    "marks": int(item.get("marks", 1)),
                    "tags": item.get("tags", ""),
                },
            )
            created += 1
        messages.success(request, f"{created} questions imported successfully.")
        return redirect("core:question_bank")

    return render(request, "core/dashboard/question_bank_import.html")


# ── T8. PAPER TEMPLATE ──────────────────────────────────────────────────────────

@teacher_required
def paper_template_list(request):
    from core.models import QuestionPaperTemplate
    templates = QuestionPaperTemplate.objects.filter(teacher=request.teacher).select_related("subject")
    return render(request, "core/dashboard/paper_template_list.html", {"templates": templates})


@teacher_required
def paper_template_create(request):
    from core.models import QuestionPaperTemplate as QPT
    if request.method == "POST":
        name             = request.POST.get("name", "").strip()
        subject_id       = request.POST.get("subject")
        total_marks      = int(request.POST.get("total_marks") or 100)
        duration_minutes = int(request.POST.get("duration_minutes") or 90)
        try:
            distribution = json.loads(request.POST.get("distribution_json", "{}"))
        except (ValueError, json.JSONDecodeError):
            distribution = {}
        try:
            chapters = json.loads(request.POST.get("chapters_json", "[]"))
        except (ValueError, json.JSONDecodeError):
            chapters = []
        subject = get_object_or_404(Subject, id=subject_id)
        QPT.objects.create(
            name=name, subject=subject, total_marks=total_marks,
            duration_minutes=duration_minutes, distribution=distribution,
            chapters=chapters, teacher=request.teacher,
        )
        messages.success(request, "Paper template created.")
        return redirect("core:paper_template_list")

    subjects = request.teacher.subjects.all()
    return render(request, "core/dashboard/paper_template_create.html", {"subjects": subjects})


@teacher_required
def paper_template_generate(request, tid):
    from core.models import QuestionPaperTemplate as QPT
    template = get_object_or_404(QPT, id=tid, teacher=request.teacher)
    dist = template.distribution or {}
    qs = QuestionBank.objects.filter(
        teacher=request.teacher, subject=template.subject, difficulty__in=["easy", "medium", "hard"]
    )
    if template.chapters:
        qs = qs.filter(chapter__in=template.chapters)
    selected = []
    for diff, cnt in dist.items():
        selected.extend(list(qs.filter(difficulty=diff)[:int(cnt)]))
    total_marks = sum(q.marks for q in selected)
    return render(request, "core/dashboard/paper_template_generate.html", {
        "template": template, "questions": selected, "total_marks": total_marks,
    })


# %% T9 REMINDER SCHEDULER %%
@teacher_required
def reminder_list(request):
    from core.models import Reminder
    reminders = Reminder.objects.filter(teacher=request.teacher).select_related("student", "subject")
    return render(request, "core/dashboard/reminder_list.html", {"reminders": reminders})


@teacher_required
def reminder_create(request):
    from core.models import Reminder, REMINDER_TYPE_CHOICES, RECURRENCE_CHOICES
    if request.method == "POST":
        reminder_type    = request.POST.get("reminder_type", "")
        student_id       = request.POST.get("student", "").strip()
        subject_id       = request.POST.get("subject", "").strip()
        title            = request.POST.get("title", "").strip()
        message          = request.POST.get("message", "").strip()
        scheduled_for    = request.POST.get("scheduled_for", "").strip()
        recurrence       = request.POST.get("recurrence", "none")
        recurrence_until = request.POST.get("recurrence_until", "").strip()
        student = Student.objects.filter(id=student_id).first() if student_id else None
        subject = Subject.objects.filter(id=subject_id).first() if subject_id else None
        ru_date = None
        if recurrence_until:
            try:
                ru_date = datetime.strptime(recurrence_until, "%Y-%m-%d").date()
            except ValueError:
                pass
        Reminder.objects.create(
            teacher=request.teacher, student=student, subject=subject,
            reminder_type=reminder_type, title=title, message=message,
            scheduled_for=scheduled_for, recurrence=recurrence,
            recurrence_until=ru_date,
        )
        messages.success(request, "Reminder created.")
        return redirect("core:reminder_list")

    subjects = request.teacher.subjects.all()
    students = request.teacher.students.all().order_by("name")
    return render(request, "core/dashboard/reminder_create.html", {
        "subjects": subjects, "students": students,
        "rtypes": REMINDER_TYPE_CHOICES, "recurrences": RECURRENCE_CHOICES,
    })


@teacher_required
@require_http_methods(["POST"])
def reminder_delete(request, reminder_id):
    reminder = get_object_or_404(Reminder, id=reminder_id, teacher=request.teacher)
    reminder.delete()
    messages.success(request, "Reminder deleted.")
    return redirect("core:reminder_list")


@_admin_required
def scheduled_tasks_list(request):
    from core.models import ScheduledTask, SCHEDULED_TASK_TYPE_CHOICES
    tasks = ScheduledTask.objects.all().order_by("-scheduled_for")[:200]
    return render(request, "core/dashboard/scheduled_tasks_list.html", {
        "tasks": tasks, "task_types": SCHEDULED_TASK_TYPE_CHOICES,
    })


# %% T10 SMART SUBJECT ANALYSIS %%

def _analytics_result_pct(result):
    if result.total_marks > 0:
        return round(result.marks_obtained / result.total_marks * 100, 1)
    return None


def _analytics_avg_pct(results):
    values = [_analytics_result_pct(r) for r in results]
    values = [v for v in values if v is not None]
    return round(sum(values) / len(values), 1) if values else None


def _analytics_linear_regression(xs, ys):
    pairs = [(x, y) for x, y in zip(xs, ys) if y is not None]
    if len(pairs) < 2:
        return [None for _ in xs], None
    xs_clean = [p[0] for p in pairs]
    ys_clean = [p[1] for p in pairs]
    n = len(xs_clean)
    x_mean = sum(xs_clean) / n
    y_mean = sum(ys_clean) / n
    num = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs_clean, ys_clean))
    den = sum((x - x_mean) ** 2 for x in xs_clean)
    if den == 0:
        return [round(y_mean, 1) for _ in xs], 0.0
    slope = num / den
    intercept = y_mean - slope * x_mean
    return [round(slope * x + intercept, 1) for x in xs], round(slope, 2)


ANALYTICS_CHART_COLORS = [
    "#6366f1", "#10b981", "#f59e0b", "#ef4444",
    "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16",
    "#f97316", "#14b8a6", "#3b82f6", "#a855f7",
]

ANALYTICS_TERMINAL_COLORS = {
    "1st": "#6366f1",
    "2nd": "#10b981",
    "3rd": "#f59e0b",
    "Final": "#ef4444",
}


def _analytics_hex_rgba(hex_color, alpha=0.15):
    hex_color = hex_color.lstrip("#")
    if len(hex_color) != 6:
        return f"rgba(99, 102, 241, {alpha})"
    r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
    return f"rgba({r}, {g}, {b}, {alpha})"


def _analytics_line_dataset(label, data, color, fill=True):
    return {
        "label": label,
        "data": data,
        "borderColor": color,
        "backgroundColor": _analytics_hex_rgba(color, 0.18) if fill else color,
        "pointBackgroundColor": "#ffffff",
        "pointBorderColor": color,
        "pointBorderWidth": 2,
        "pointRadius": 5,
        "pointHoverRadius": 7,
        "tension": 0.35,
        "fill": fill,
    }


@teacher_required
def subject_analytics(request):
    teacher = request.teacher
    subject_id_raw = request.GET.get("subject", "").strip()
    terminal = request.GET.get("terminal", "all")
    analysis_mode = request.GET.get("analysis_mode", "bulk")
    class_section_raw = request.GET.get("class_section", "").strip()
    student_id_raw = request.GET.get("student_id", "").strip()

    if analysis_mode not in ("bulk", "single"):
        analysis_mode = "bulk"

    subject_id = int(subject_id_raw) if subject_id_raw.isdigit() else None
    student_id = int(student_id_raw) if student_id_raw.isdigit() else None

    teacher_subjects = teacher.subjects.all()
    teacher_students = teacher.students.all()
    all_subjects = list(teacher_subjects.order_by("name"))
    terminals = ["1st", "2nd", "3rd", "Final"]
    run_terminals = terminals if terminal == "all" else (
        [terminal] if terminal in terminals else terminals
    )

    class_sections = []
    seen_sections = set()
    for st in teacher_students.order_by("student_class", "section", "name"):
        key = (st.student_class, st.section)
        if key in seen_sections:
            continue
        seen_sections.add(key)
        class_sections.append({
            "value": f"{st.student_class}|{st.section}",
            "label": f"Class {st.student_class} — Section {st.section}",
        })

    available_students = list(
        teacher_students.order_by("name").values(
            "id", "name", "roll_number", "student_class", "section"
        )
    )

    scope_students = teacher_students
    selected_student = None
    if analysis_mode == "bulk" and class_section_raw and "|" in class_section_raw:
        cls, sec = class_section_raw.split("|", 1)
        scope_students = scope_students.filter(student_class=cls, section=sec)
    elif analysis_mode == "single":
        if student_id is not None:
            selected_student = teacher_students.filter(id=student_id).first()
            scope_students = (
                teacher_students.filter(id=student_id)
                if selected_student else teacher_students.none()
            )
        else:
            scope_students = teacher_students.none()

    filtered_qs = Result.objects.filter(
        student__in=scope_students,
        subject__in=teacher_subjects,
    ).select_related("student", "subject")
    if subject_id is not None:
        filtered_qs = filtered_qs.filter(subject_id=subject_id)

    stats_qs = filtered_qs
    if terminal != "all" and terminal in terminals:
        stats_qs = stats_qs.filter(terminal=terminal)

    pct_list = []
    for r in stats_qs:
        pct = _analytics_result_pct(r)
        if pct is not None:
            pct_list.append(pct)

    total = len(pct_list)
    avg_pct = round(sum(pct_list) / total, 1) if total else 0
    highest_pct = round(max(pct_list), 1) if pct_list else 0
    lowest_pct = round(min(pct_list), 1) if pct_list else 0
    pass_count = sum(1 for p in pct_list if p >= 40)
    pass_rate = round((pass_count / total) * 100, 1) if total else 0
    below_40 = sum(1 for p in pct_list if p < 40)

    insight_lines = []
    mode_label = "class section" if analysis_mode == "bulk" else "student"
    if analysis_mode == "single" and selected_student:
        insight_lines.append(
            f"Analysing {selected_student.name} "
            f"(Class {selected_student.student_class}-{selected_student.section})."
        )
    elif analysis_mode == "bulk" and class_section_raw:
        insight_lines.append(f"Bulk analysis for selected class section ({mode_label}).")
    if below_40 > 0:
        s = "s" if below_40 > 1 else ""
        insight_lines.append(
            f"{below_40} result{s} below 40% — consider targeted intervention."
        )
    if avg_pct >= 80:
        insight_lines.append(f"Excellent average at {avg_pct}%.")
    elif avg_pct >= 70:
        insight_lines.append(f"Good progress — average is {avg_pct}%.")
    elif avg_pct >= 50:
        insight_lines.append(f"Average is {avg_pct}%. Focus on weaker performers.")
    elif total:
        insight_lines.append(f"Average is {avg_pct}%. Needs attention.")

    chart_subjects = all_subjects
    if subject_id is not None:
        chart_subjects = [s for s in all_subjects if s.id == subject_id]

    subject_colors = ANALYTICS_CHART_COLORS
    term_colors = ANALYTICS_TERMINAL_COLORS

    terminal_wise_datasets = []
    for i, subj in enumerate(chart_subjects):
        color = subject_colors[i % len(subject_colors)]
        terminal_wise_datasets.append(
            _analytics_line_dataset(
                subj.name,
                [
                    _analytics_avg_pct(filtered_qs.filter(subject=subj, terminal=t))
                    for t in run_terminals
                ],
                color,
            )
        )

    subject_wise_datasets = []
    for t in run_terminals:
        color = term_colors.get(t, subject_colors[len(subject_wise_datasets) % len(subject_colors)])
        subject_wise_datasets.append(
            _analytics_line_dataset(
                f"{t} Terminal",
                [
                    _analytics_avg_pct(filtered_qs.filter(subject=subj, terminal=t))
                    for subj in chart_subjects
                ],
                color,
            )
        )

    dist_bins = [
        ("0–39% (Fail)", 0, 39),
        ("40–59%", 40, 59),
        ("60–79%", 60, 79),
        ("80–100%", 80, 100),
    ]
    distribution_chart = {
        "labels": [b[0] for b in dist_bins],
        "datasets": [{
            "label": "Results",
            "data": [
                sum(1 for p in pct_list if lo <= p <= hi)
                for _, lo, hi in dist_bins
            ],
            "backgroundColor": ["#ef4444", "#f59e0b", "#10b981", "#6366f1"],
            "borderRadius": 6,
        }],
    }

    term_indices = list(range(1, len(run_terminals) + 1))
    if analysis_mode == "single" and selected_student:
        student_pcts = [
            _analytics_avg_pct(
                filtered_qs.filter(student=selected_student, terminal=t)
            )
            for t in run_terminals
        ]
        reg_line, reg_slope = _analytics_linear_regression(term_indices, student_pcts)
        regression_chart = {
            "labels": run_terminals,
            "scatter": [{"x": i, "y": y} for i, y in zip(term_indices, student_pcts) if y is not None],
            "regression": reg_line,
            "slope": reg_slope,
            "title": f"{selected_student.name} — terminal progression",
        }
        class_avg_by_term = [
            _analytics_avg_pct(
                Result.objects.filter(
                    student__in=teacher_students,
                    subject__in=teacher_subjects,
                    terminal=t,
                )
            )
            for t in run_terminals
        ]
        comparison_chart = {
            "labels": run_terminals,
            "datasets": [
                {
                    "label": selected_student.name,
                    "data": student_pcts,
                    "backgroundColor": _analytics_hex_rgba("#6366f1", 0.85),
                    "borderColor": "#6366f1",
                    "borderWidth": 2,
                    "borderRadius": 6,
                },
                {
                    "label": "Class average",
                    "data": class_avg_by_term,
                    "backgroundColor": _analytics_hex_rgba("#f59e0b", 0.85),
                    "borderColor": "#f59e0b",
                    "borderWidth": 2,
                    "borderRadius": 6,
                },
            ],
        }
        subject_breakdown_chart = {
            "labels": [s.name for s in chart_subjects],
            "datasets": [{
                "label": "Latest terminal %" if terminal == "all" else f"{terminal} Terminal %",
                "data": [
                    _analytics_avg_pct(
                        filtered_qs.filter(
                            student=selected_student,
                            subject=subj,
                            terminal=run_terminals[-1] if terminal == "all" else terminal,
                        )
                    )
                    for subj in chart_subjects
                ],
                "backgroundColor": [
                    subject_colors[i % len(subject_colors)] for i in range(len(chart_subjects))
                ],
            }],
        }
    else:
        class_avg_by_term = [
            _analytics_avg_pct(filtered_qs.filter(terminal=t))
            for t in run_terminals
        ]
        reg_line, reg_slope = _analytics_linear_regression(term_indices, class_avg_by_term)
        regression_chart = {
            "labels": run_terminals,
            "scatter": [{"x": i, "y": y} for i, y in zip(term_indices, class_avg_by_term) if y is not None],
            "regression": reg_line,
            "slope": reg_slope,
            "title": "Class average — regression trend",
        }
        comparison_chart = None
        subject_breakdown_chart = {
            "labels": [s.name for s in chart_subjects],
            "datasets": [{
                "label": "Section average %",
                "data": [
                    _analytics_avg_pct(
                        filtered_qs.filter(
                            subject=subj,
                            terminal=run_terminals[-1] if terminal == "all" else terminal,
                        )
                    )
                    for subj in chart_subjects
                ],
                "backgroundColor": [
                    subject_colors[i % len(subject_colors)] for i in range(len(chart_subjects))
                ],
            }],
        }

    pass_fail_chart = {
        "labels": ["Pass (≥40%)", "Fail (<40%)"],
        "datasets": [{
            "data": [pass_count, total - pass_count],
            "backgroundColor": ["#10b981", "#ef4444"],
            "borderWidth": 0,
        }],
    }

    trender = {}
    for r in filtered_qs.order_by("student__name", "terminal"):
        sid = r.student.id
        if sid not in trender:
            trender[sid] = {"student": r.student, "marks_by_term": {}}
        pct = _analytics_result_pct(r)
        if pct is not None:
            trender[sid]["marks_by_term"][r.terminal] = pct

    trend_rows = []
    for sid in sorted(trender, key=lambda s: trender[s]["student"].name):
        info = trender[sid]
        mbt = info["marks_by_term"]
        prev_vals = [mbt.get(t) for t in run_terminals if mbt.get(t) is not None]
        if len(prev_vals) >= 2:
            diff = prev_vals[-1] - prev_vals[-2]
            arrow = "up" if diff > 0.5 else ("down" if diff < -0.5 else "same")
        else:
            arrow = "same"
        marks_list = [mbt.get(t) for t in run_terminals]
        trend_rows.append({
            "student": info["student"],
            "marks_list": marks_list,
            "mark_tuples": list(zip(run_terminals, marks_list)),
            "arrow": arrow,
        })

    return render(request, "core/dashboard/subject_analytics.html", {
        "subject_obj": Subject.objects.filter(id=subject_id).first() if subject_id is not None else None,
        "subject_id": subject_id_raw,
        "terminal": terminal,
        "analysis_mode": analysis_mode,
        "class_section": class_section_raw,
        "student_id": student_id_raw,
        "selected_student": selected_student,
        "class_sections": class_sections,
        "available_students": available_students,
        "run_terminals": run_terminals,
        "total": total,
        "avg_pct": avg_pct,
        "highest_pct": highest_pct,
        "lowest_pct": lowest_pct,
        "pass_rate": pass_rate,
        "pass_count": pass_count,
        "below_40": below_40,
        "trend_rows": trend_rows,
        "insight_lines": insight_lines,
        "available_subjects": all_subjects,
        "terminals": terminals,
        "is_teacher": True,
        "terminal_wise_chart": {
            "labels": run_terminals,
            "datasets": terminal_wise_datasets,
        },
        "subject_wise_chart": {
            "labels": [s.name for s in chart_subjects],
            "datasets": subject_wise_datasets,
        },
        "distribution_chart": distribution_chart,
        "regression_chart": regression_chart,
        "pass_fail_chart": pass_fail_chart,
        "comparison_chart": comparison_chart,
        "subject_breakdown_chart": subject_breakdown_chart,
        "chart_color_legend": {
            "subjects": [
                {"name": s.name, "color": subject_colors[i % len(subject_colors)]}
                for i, s in enumerate(chart_subjects)
            ],
            "terminals": [
                {"name": f"{t} Terminal", "color": term_colors.get(t, subject_colors[i % len(subject_colors)])}
                for i, t in enumerate(run_terminals)
            ],
        },
    })


# %% A12 AUTOMATED DIGESTS (admin-triggered) %%
@_admin_required
def trigger_weekly_digest(request):
    from core.models import ScheduledTask
    from datetime import timedelta
    now  = timezone.now()
    count = 0
    for student in Student.objects.all():
        ScheduledTask.objects.create(
            task_type="sms_digest",
            scheduled_for=now + timedelta(minutes=count),
            payload={"student_id": student.id, "type": "weekly_attendance"},
        )
        count += 1
    messages.success(request, f"Queued {count} weekly attendance digest tasks.")
    return redirect("core:scheduled_tasks_list")


@_admin_required
def trigger_monthly_report(request):
    from core.models import ScheduledTask
    from datetime import timedelta
    now  = timezone.now()
    count = 0
    for student in Student.objects.all():
        ScheduledTask.objects.create(
            task_type="sms_digest",
            scheduled_for=now + timedelta(minutes=count),
            payload={"student_id": student.id, "type": "monthly_report"},
        )
        count += 1
    messages.success(request, f"Queued {count} monthly report tasks.")
    return redirect("core:scheduled_tasks_list")


# ═════════════════════════════════════════════════════════════════════════════
# A3 — INVOICE BILLING / SUBSCRIPTION MODULE
# ═════════════════════════════════════════════════════════════════════════════

@_admin_required
def subscription_management(request):
    """List subscriptions and allow creating/upgrading."""
    subscriptions = Subscription.objects.select_related('created_by').all()
    selected_sub = None
    if request.GET.get('id'):
        selected_sub = Subscription.objects.filter(id=request.GET['id']).first()
    if request.method == 'POST':
        inst = request.POST.get('institution', '').strip()
        plan = request.POST.get('plan', 'starter')
        price = request.POST.get('monthly_price', '0')
        expires = request.POST.get('expires_at', '')
        renew = request.POST.get('auto_renew') == 'on'
        active = request.POST.get('is_active') == 'on'
        sub = Subscription.objects.create(
            institution=inst, plan=plan, monthly_price=price or 0,
            is_active=active, auto_renew=renew,
            created_by=request.user,
            expires_at=timezone.make_aware(datetime.fromisoformat(expires)) if expires else None,
        )
        messages.success(request, f'Subscription created for {inst}.')
        return redirect('core:subscription_management')
    return render(request, 'core/dashboard/subscription_management.html', {
        'subscriptions': subscriptions, 'selected_sub': selected_sub,
        'plan_choices': Subscription.PLAN_CHOICES,
    })


@_admin_required
def invoice_list(request):
    """List all invoices with status filter."""
    status = request.GET.get('status', '')
    invoices = Invoice.objects.select_related('subscription', 'created_by').all()
    if status:
        invoices = invoices.filter(status=status)
    return render(request, 'core/dashboard/invoice_list.html', {
        'invoices': invoices,
        'status_filter': status,
        'status_choices': Invoice.INVOICE_STATUS_CHOICES,
    })


@_admin_required
def invoice_create(request):
    """Create a manual invoice with line items."""
    if request.method == 'POST':
        form = InvoiceQuickCreateForm(request.POST)
        if form.is_valid():
            try:
                line_items = json.loads(form.cleaned_data['line_items'] or '[]')
            except json.JSONDecodeError:
                line_items = []

            sub_id = form.cleaned_data.get('subscription')
            subscription = None
            if sub_id:
                try:
                    subscription = Subscription.objects.get(id=sub_id)
                except Subscription.DoesNotExist:
                    pass

            inv = Invoice.objects.create(
                subscription=subscription,
                issued_to=form.cleaned_data['issued_to'],
                amount=form.cleaned_data['amount'],
                tax_amount=form.cleaned_data.get('tax_amount') or 0,
                issue_date=form.cleaned_data['issue_date'],
                due_date=form.cleaned_data['due_date'],
                status='DRAFT',
                line_items=line_items,
                created_by=request.user,
            )
            messages.success(request, f'Invoice {inv.invoice_number} created.')
            return redirect('core:invoice_detail', invoice_number=inv.invoice_number)
    else:
        form = InvoiceQuickCreateForm()

    subs = Subscription.objects.filter(is_active=True)
    form.fields['subscription'].choices = [('', '— No subscription —')] + [
        (str(s.id), f'{s.institution} ({s.get_plan_display()})') for s in subs
    ]
    return render(request, 'core/dashboard/invoice_create.html', {
        'form': form, 'status_choices': Invoice.INVOICE_STATUS_CHOICES,
    })


@_admin_required
def invoice_detail(request, invoice_number):
    """Invoice preview/print page."""
    inv = get_object_or_404(Invoice.objects.select_related('subscription', 'created_by'), invoice_number=invoice_number)
    return render(request, 'core/dashboard/invoice_detail.html', {
        'invoice': inv,
    })


@_admin_required
def invoice_pdf(request, invoice_number):
    """PDF download using ReportLab."""
    from django.http import FileResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER

    inv = get_object_or_404(Invoice.objects.select_related('subscription', 'created_by'), invoice_number=invoice_number)
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2*cm, rightMargin=2*cm)
    styles = getSampleStyleSheet()
    accent = colors.HexColor('#4F46E5')

    title_style = ParagraphStyle('_title', parent=styles['Title'], textColor=accent, fontSize=22, spaceAfter=4)
    body_style  = ParagraphStyle('_body',  parent=styles['Normal'],  fontSize=10, spaceAfter=2)
    hdr_style   = ParagraphStyle('_hdr',   parent=styles['Normal'],  fontSize=9,  textColor=colors.grey, spaceAfter=2)

    elems = []
    elems.append(Paragraph('ACADEMIC MANAGEMENT SYSTEM', title_style))
    elems.append(Paragraph('Invoice', ParagraphStyle('_inv', parent=styles['Normal'], fontSize=16, textColor=accent, spaceAfter=2)))
    elems.append(Spacer(1, 0.5*cm))
    elems.append(HRFlowable(width='100%', thickness=2, color=accent, spaceAfter=0.5*cm))

    # Info table
    info = [
        ['Invoice #', inv.invoice_number],
        ['Issued To', inv.issued_to],
        ['Issue Date', inv.issue_date.strftime('%d %B %Y') if inv.issue_date else '—'],
        ['Due Date',   inv.due_date.strftime('%d %B %Y') if inv.due_date else '—'],
        ['Status',     inv.get_status_display()],
    ]
    info_rows = [[Paragraph(k, body_style), Paragraph(str(v), body_style)] for k, v in info]
    info_tbl = Table(info_rows, colWidths=[5*cm, 11*cm])
    info_tbl.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#EEF2FF')),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
    ]))
    elems.append(info_tbl)
    elems.append(Spacer(1, 0.5*cm))

    # Line items
    items = inv.line_items or []
    if items:
        elems.append(Paragraph('Line Items', body_style))
        item_hdr = Table(
            [[Paragraph(h, body_style) for h in ['Description','Qty','Unit Price','Total']]],
            colWidths=[8*cm, 2*cm, 3*cm, 3*cm]
        )
        item_hdr.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), accent),
            ('TEXTCOLOR', (0,0), (-1,-1), colors.white),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        elems.append(item_hdr)
        for li in items:
            desc   = li.get('description', '')
            qty    = str(li.get('qty', 1))
            uprice = str(li.get('unit_price', 0))
            total  = str(li.get('total', 0))
            row_tbl = Table(
                [[Paragraph(desc, body_style), Paragraph(qty, body_style),
                  Paragraph(uprice, body_style), Paragraph(total, body_style)]],
                colWidths=[8*cm, 2*cm, 3*cm, 3*cm]
            )
            row_tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                ('TOPPADDING', (0,0), (-1,-1), 5),
                ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ]))
            elems.append(row_tbl)
        elems.append(Spacer(1, 0.3*cm))

    # Totals
    tot_data = [
        ['Subtotal:', f'Rs. {inv.amount:,.2f}'],
        ['Tax:',       f'Rs. {inv.tax_amount:,.2f}'],
        ['TOTAL:',     f'Rs. {inv.total_amount:,.2f}'],
    ]
    tot_rows = [[Paragraph(k, body_style), Paragraph(str(v), body_style)] for k, v in tot_data]
    tot_table = Table(tot_rows, colWidths=[8*cm, 8*cm], hAlign='RIGHT')
    tot_table.setStyle(TableStyle([
        ('BACKGROUND', (0,2), (-1,2), colors.HexColor('#EEF2FF')),
        ('FONTNAME',   (0,2), (-1,2), 'Helvetica-Bold'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    elems.append(tot_table)
    elems.append(Spacer(1, 1*cm))
    elems.append(HRFlowable(width='100%', thickness=1, color=colors.grey, spaceAfter=0.3*cm))
    elems.append(Paragraph(f'Generated on  {timezone.now().strftime("%d %B %Y %H:%M")}', hdr_style))

    doc.build(elems)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{inv.invoice_number}.pdf')


@_admin_required
def invoice_mark_paid(request, invoice_id):
    """POST-only: mark invoice as paid."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    inv = get_object_or_404(Invoice, id=invoice_id)
    inv.status = 'PAID'
    inv.paid_date = timezone.now().date()
    inv.save()
    messages.success(request, f'Invoice {inv.invoice_number} marked as paid.')
    return redirect('core:invoice_list')


# ═════════════════════════════════════════════════════════════════════════════
# A8 — ANALYTICS EXPORT BUNDLE
# ═════════════════════════════════════════════════════════════════════════════

@_admin_required
def export_smart_dashboard_pdf(request):
    """Generate a PDF export of the smart analytics dashboard."""
    if not SystemConfig.get_bool('enable_export_bundle', True):
        messages.warning(request, 'Export bundle is disabled by system configuration.')
        return redirect('core:smart_dashboard')
    # Enforce same filters as smart_dashboard
    req_args = {'path': request.path, 'GET': request.GET.copy()}
    return export_utils.export_smart_dashboard_pdf(request)


@_admin_required
def export_smart_dashboard_excel(request):
    """Generate an Excel workbook export of the smart analytics dashboard."""
    if not SystemConfig.get_bool('enable_export_bundle', True):
        messages.warning(request, 'Export bundle is disabled by system configuration.')
        return redirect('core:smart_dashboard')
    # Build context by calling the same idea as smart_dashboard but manually
    from django.db.models import Avg, Sum as _Sum
    period = request.GET.get('period', 'all')
    selected_class = request.GET.get('student_class', '')
    all_results = Result.objects.select_related('student', 'subject')
    if selected_class:
        all_results = all_results.filter(student__student_class=selected_class)

    gs = GradeScale.objects.filter(is_active=True).first()
    pass_mark_pct = gs.pass_mark_percent if gs else 40.0

    student_scores = []
    for stu in Student.objects.prefetch_related('result_set'):
        res = stu.result_set.all()
        if not res.exists():
            continue
        obt = sum(r.marks_obtained for r in res)
        pos = sum(r.total_marks for r in res)
        p = (obt / pos * 100) if pos > 0 else 0
        student_scores.append({'student': stu, 'percentage': round(p, 1), 'obtained': obt, 'total': pos})
    student_scores.sort(key=lambda x: x['percentage'], reverse=True)
    top_students    = student_scores[:10]
    weak_students   = [s for s in student_scores if s['percentage'] < pass_mark_pct][:10]

    subj_stats = []
    for subj in Subject.objects.all():
        s_res = all_results.filter(subject=subj)
        if s_res.exists():
            avg = s_res.aggregate(av=Avg('marks_obtained'))['av'] or 0
            pos_sum = s_res.aggregate(s=_Sum('total_marks'))['s'] or 0
            obt_sum = s_res.aggregate(s=_Sum('marks_obtained'))['s'] or 0
            pct = (obt_sum / pos_sum * 100) if pos_sum > 0 else 0
            subj_stats.append({'subject': subj.name, 'avg': round(avg,1), 'percentage': round(pct,1)})
    subj_stats.sort(key=lambda x: x['percentage'])

    class_stats = []
    for cls in Student.objects.values_list('student_class', flat=True).distinct().order_by('student_class'):
        cls_res = all_results.filter(student__student_class=cls)
        if cls_res.exists():
            pos = cls_res.aggregate(s=_Sum('total_marks'))['s'] or 0
            obt = cls_res.aggregate(s=_Sum('marks_obtained'))['s'] or 0
            pct = (obt / pos * 100) if pos > 0 else 0
            class_stats.append({'class': cls, 'students': Student.objects.filter(student_class=cls).count(), 'percentage': round(pct,1)})

    term_stats = []
    for term in ['1st','2nd','3rd','Final']:
        t_res = all_results.filter(terminal=term)
        if t_res.exists():
            pos = t_res.aggregate(s=_Sum('total_marks'))['s'] or 0
            obt = t_res.aggregate(s=_Sum('marks_obtained'))['s'] or 0
            pct = (obt / pos * 100) if pos > 0 else 0
            term_stats.append({'terminal': term, 'percentage': round(pct,1)})

    att_present = Attendance.objects.filter(status='present').count()
    att_total   = Attendance.objects.count()
    att_pct     = round((att_present / att_total * 100), 1) if att_total > 0 else 0

    context = {
        'total_students':   Student.objects.count(),
        'total_subjects':   Subject.objects.count(),
        'total_results':    all_results.count(),
        'total_teachers':   Teacher.objects.filter(is_active=True).count(),
        'top_students':     top_students,
        'weak_students':    weak_students,
        'subj_stats':       subj_stats,
        'class_stats':      class_stats,
        'term_stats':       term_stats,
        'att_present':      att_present,
        'att_total':        att_total,
        'att_pct':          att_pct,
        'selected_class':   selected_class,
        'pass_mark_pct':    pass_mark_pct,
    }
    return export_utils.export_smart_dashboard_excel(request, context)


# ═════════════════════════════════════════════════════════════════════════════
# A9 — CERTIFICATE GENERATOR
# ═════════════════════════════════════════════════════════════════════════════

@_admin_required
def certificate_templates(request):
    """List / edit HTML certificate templates."""
    templates = CertificateTemplate.objects.all()
    if request.method == 'POST':
        tpl_id = request.POST.get('tpl_id')
        html = request.POST.get('html_content', '')
        if tpl_id:
            tpl = get_object_or_404(CertificateTemplate, id=tpl_id)
            tpl.html_content = html
            tpl.is_active = request.POST.get('is_active') == 'on'
            tpl.save()
            messages.success(request, f'Template "{tpl.name}" updated.')
        return redirect('core:certificate_templates')
    return render(request, 'core/dashboard/certificate_templates.html', {
        'templates': templates,
    })


@_admin_required
def generate_certificate(request):
    """Generate a new certificate PDF-ready record."""
    if request.method == 'POST':
        form = CertificateGenerateForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']
            cert_type = form.cleaned_data['certificate_type']
            template = CertificateTemplate.objects.filter(
                name__icontains=cert_type.lower(), is_active=True
            ).first()
            if not template:
                template = CertificateTemplate.objects.filter(is_active=True).first()
            if not template:
                messages.error(request, 'No active certificate template found. Create one first.')
                return redirect('core:certificate_templates')

            # Build QR verification string
            qr_str = f"ACADSTAT:CERT:{student.roll_number}:{student.name}:{cert_type}"

            cert = Certificate.objects.create(
                student=student,
                template=template,
                certificate_type=cert_type,
                issued_by=request.user,
                qr_data_string=qr_str,
                status='ISSUED',
            )
            try:
                NotificationService.log_activity(
                    request.user, 'other',
                    f'Certificate generated: {cert.certificate_number} for {student.name}',
                )
            except Exception:
                pass
            messages.success(request, f'Certificate {cert.certificate_number} issued for {student.name}.')
            return redirect('core:certificate_list')
    else:
        form = CertificateGenerateForm()
    return render(request, 'core/dashboard/generate_certificate.html', {
        'form': form,
    })


@_admin_required
def certificate_list(request):
    """List all issued/draft certificates."""
    status = request.GET.get('status', '')
    certs = Certificate.objects.select_related('student', 'template', 'issued_by')
    if status:
        certs = certs.filter(status=status)
    return render(request, 'core/dashboard/certificate_list.html', {
        'certificates': certs.order_by('-created_at'),
        'status_filter': status,
        'status_choices': Certificate.CERT_STATUS_CHOICES,
    })


@_admin_required
def certificate_view(request, cert_number):
    """Rendered certificate page."""
    cert = get_object_or_404(Certificate.objects.select_related('student', 'template', 'issued_by'),
                              certificate_number=cert_number)
    return render(request, 'core/dashboard/certificate_view.html', {
        'cert': cert,
    })


@_admin_required
def certificate_pdf(request, cert_number):
    """Generate PDF blob for a certificate using ReportLab."""
    from django.http import FileResponse
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    import qrcode as qr_gen
    from io import BytesIO

    cert = get_object_or_404(Certificate.objects.select_related('student', 'template', 'issued_by'),
                              certificate_number=cert_number)
    student = cert.student

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
        leftMargin=2*cm, rightMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    gold   = colors.HexColor('#D4A017')
    navy   = colors.HexColor('#1E3A5F')
    white  = colors.white
    black  = colors.HexColor('#1a1a1a')

    T = ParagraphStyle('_T', fontName='Helvetica-Bold',  fontSize=24, textColor=gold,
                       alignment=TA_CENTER, spaceAfter=6)
    S = ParagraphStyle('_S', fontName='Helvetica-Bold',  fontSize=14, textColor=navy,
                       alignment=TA_CENTER, spaceAfter=4)
    SN = ParagraphStyle('_SN', fontName='Helvetica', fontSize=12, textColor=black,
                        alignment=TA_CENTER, spaceAfter=2)
    FN = ParagraphStyle('_FN', fontName='Helvetica', fontSize=10, textColor=colors.grey,
                        alignment=TA_CENTER)
    SFN = ParagraphStyle('_SFN', fontName='Helvetica-Bold', fontSize=10, textColor=black,
                         alignment=TA_CENTER)

    # QR code
    qr_buf = BytesIO()
    qr_img = qr_gen.make(cert.qr_data_string or cert.certificate_number)
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)

    elems = []
    elems.append(Spacer(1, 0.5*cm))
    elems.append(Paragraph('ACADEMIC MANAGEMENT SYSTEM', ParagraphStyle(
        '_inst', fontName='Helvetica-Bold', fontSize=12, textColor=navy, alignment=TA_CENTER, spaceAfter=4)))
    elems.append(Paragraph(cert.get_certificate_type_display(), T))
    elems.append(Spacer(1, 0.3*cm))
    elems.append(HRFlowable(width='100%', thickness=2, color=gold, spaceAfter=0.3*cm))
    elems.append(Spacer(1, 0.3*cm))
    elems.append(Paragraph('This is to certify that', SN))
    elems.append(Paragraph(student.name, S))
    elems.append(Spacer(1, 0.2*cm))
    elems.append(Paragraph(f'Roll No: {student.roll_number or "N/A"}', FN))
    elems.append(Paragraph(f'Class   : {student.student_class} {student.section}', FN))
    elems.append(Spacer(1, 0.3*cm))
    elems.append(HRFlowable(width='100%', thickness=0.5, color=gold, spaceAfter=0.3*cm))
    elems.append(Spacer(1, 0.3*cm))
    elems.append(Paragraph(f'Certificate No: {cert.certificate_number}', FN))
    elems.append(Paragraph(f'Issued Date   : {cert.issued_date.strftime("%d %B %Y") if cert.issued_date else "—"}', FN))
    issued_name = cert.issued_by.get_full_name() if cert.issued_by else 'Administrator'
    elems.append(Paragraph(f'Issued By     : {issued_name}', FN))
    elems.append(Spacer(1, 1*cm))

    # QR + signature
    qr_tbl = Table(
        [[Paragraph(f'Scan to verify:<br/>{cert.certificate_number}', FN), None]],
        colWidths=[5*cm, 5*cm]
    )
    qr_data = qr_buf.read()
    from reportlab.platypus import Image as RLImage
    qr_img_rl = RLImage(io.BytesIO(qr_data), width=2.5*cm, height=2.5*cm)
    qr_tbl = Table([[qr_img_rl, Paragraph('Authorised Signature', FN)]], colWidths=[5*cm, 9*cm])
    qr_tbl.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'), ('ALIGN', (0,0), (0,-1), 'CENTER'),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    elems.append(qr_tbl)
    elems.append(Spacer(1, 0.5*cm))
    elems.append(HRFlowable(width='100%', thickness=1, color=gold))
    elems.append(Paragraph(f'Verified at AcadStat — {timezone.now().strftime("%d %B %Y")}', FN))

    doc.build(elems)
    buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f'{cert.certificate_number}.pdf')


def verify_certificate(request):
    """Public (or login): search by certificate number and show certificate or 'not found'."""
    cert_number = request.GET.get('certificate_number', '').strip() or request.POST.get('certificate_number', '').strip()
    cert = None
    if cert_number:
        cert = Certificate.objects.select_related('student', 'template').filter(
            certificate_number=cert_number
        ).first()
    return render(request, 'core/dashboard/verify_certificate.html', {
        'cert_number': cert_number, 'cert': cert,
    })


# ═════════════════════════════════════════════════════════════════════════════
# A5 — SUPPORT TICKET SYSTEM
# ═════════════════════════════════════════════════════════════════════════════

@login_required
def ticket_list(request):
    """Students see their own tickets, teachers see all, admins see all."""
    is_admin = _is_admin_user(request.user)
    teacher = get_teacher_profile(request.user)
    qs = SupportTicket.objects.select_related('reported_by', 'assigned_to', 'resolved_by')
    if not is_admin and teacher:
        qs = qs.filter(Q(reported_by=request.user) | Q(assigned_to=teacher))
    elif not is_admin:
        qs = qs.filter(reported_by=request.user)
    tickets = qs.order_by('-created_at')
    return render(request, 'core/dashboard/ticket_list.html', {
        'tickets': tickets, 'is_admin': is_admin, 'is_teacher': bool(teacher),
        'status_choices': SupportTicket.TICKET_STATUS_CHOICES,
        'priority_choices': SupportTicket.TICKET_PRIORITY_CHOICES,
    })


@login_required
def ticket_create(request):
    """Create a new support ticket."""
    if request.method == 'POST':
        form = SupportTicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.reported_by = request.user
            ticket.status = 'Open'
            ticket.save()
            messages.success(request, f'Ticket {ticket.ticket_id} created successfully.')
            return redirect('core:ticket_detail', ticket_id=ticket.ticket_id)
    else:
        form = SupportTicketForm()
    return render(request, 'core/dashboard/ticket_create.html', {
        'form': form,
    })


@login_required
def ticket_detail(request, ticket_id):
    """Full ticket thread with comments, status change."""
    ticket = get_object_or_404(SupportTicket.objects.select_related(
        'reported_by', 'assigned_to', 'resolved_by'), ticket_id=ticket_id)
    if request.method == 'POST':
        # Comment
        if 'comment' in request.POST:
            body = request.POST.get('body', '').strip()
            if body:
                TicketComment.objects.create(
                    ticket=ticket, author=request.user, body=body,
                    is_internal=request.POST.get('is_internal') == 'on',
                )
                messages.success(request, 'Comment added.')
            return redirect('core:ticket_detail', ticket_id=ticket_id)

        # Status update
        if 'update_status' in request.POST:
            new_status = request.POST.get('status', '').strip()
            if new_status in dict(SupportTicket.TICKET_STATUS_CHOICES):
                ticket.status = new_status
                ticket.priority = request.POST.get('priority', ticket.priority)
                if new_status == 'Resolved':
                    ticket.resolved_at = timezone.now()
                    ticket.resolved_by = request.user
                    if not ticket.resolution_notes:
                        ticket.resolution_notes = request.POST.get('resolution_notes', '')
                if request.POST.get('assigned_to'):
                    try:
                        ticket.assigned_to = Teacher.objects.get(
                            id=int(request.POST['assigned_to']))
                    except (Teacher.DoesNotExist, ValueError):
                        pass
                ticket.save()
                if new_status == 'Resolved':
                    ticket_notify(ticket)
                NotificationService.log_activity(
                    request.user, 'other',
                    f'Status updated: Ticket {ticket.ticket_id} → {Ticket.objects.filter(id=ticket.id).get()}',
                )
                messages.success(request, f'Ticket status updated to {new_status}.')
            return redirect('core:ticket_detail', ticket_id=ticket_id)

    comments = ticket.comments.select_related('author').all()
    teachers = Teacher.objects.filter(is_active=True).order_by('first_name')
    return render(request, 'core/dashboard/ticket_detail.html', {
        'ticket': ticket, 'comments': comments, 'teachers': teachers,
    })


@login_required
def ticket_update_status(request, ticket_id):
    """POST-only: update ticket status/priority/assignment."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    new_status = request.POST.get('status', '').strip()
    if new_status in dict(SupportTicket.TICKET_STATUS_CHOICES):
        ticket.status = new_status
        ticket.priority = request.POST.get('priority', ticket.priority)
        if new_status == 'Resolved':
            ticket.resolved_at = timezone.now()
            ticket.resolved_by = request.user
        if request.POST.get('assigned_to'):
            try:
                ticket.assigned_to = Teacher.objects.get(id=int(request.POST['assigned_to']))
            except (Teacher.DoesNotExist, ValueError):
                pass
        ticket.save()
        if new_status == 'Resolved':
            ticket_notify(ticket)
        return JsonResponse({'success': True, 'status': ticket.status})
    return JsonResponse({'success': False, 'message': 'Invalid status'}, status=400)


@login_required
def ticket_comment(request, ticket_id):
    """POST-only: add a comment to a ticket."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    ticket = get_object_or_404(SupportTicket, ticket_id=ticket_id)
    body = request.POST.get('body', '').strip()
    if not body:
        return JsonResponse({'success': False, 'message': 'Body required'}, status=400)
    TicketComment.objects.create(
        ticket=ticket, author=request.user, body=body,
        is_internal=request.POST.get('is_internal') == 'on',
    )
    return JsonResponse({'success': True})


def ticket_notify(ticket):
    """When a ticket is resolved, email the reporter."""
    try:
        reporter = ticket.reported_by
        ticket_title = ticket.title
        ticket_id = ticket.ticket_id
        if reporter and reporter.email:
            notify_student(
                Student.objects.filter(email=reporter.email).first() or Student.objects.get(name=reporter.username) if Student.objects.filter(email=reporter.email).exists() else None,
                title=f'Ticket Resolved: {ticket_title}',
                message=f'Your ticket ({ticket_id}) has been resolved. {ticket.resolution_notes or "Thank you for your patience."}',
            ) if False else _email_ticket_notify_helper(ticket)
    except Exception as exc:
        logger = __import__('logging').getLogger(__name__)
        logger.warning(f'ticket_notify: {exc}')


def _email_ticket_notify_helper(ticket):
    from core.email_service import send_mail
    reporter = ticket.reported_by
    if reporter and reporter.email:
        send_mail(
            subject=f'Ticket Resolved: {ticket.title}',
            body=f'Your ticket {ticket.ticket_id} has been resolved.\n\n{ticket.resolution_notes}',
            recipient_list=[reporter.email],
        )


# ═════════════════════════════════════════════════════════════════════════════
# A14 — API KEY & WEBHOOK SYSTEM (DEVELOPER PORTAL)
# ═════════════════════════════════════════════════════════════════════════════

@_admin_required
def developer_portal(request):
    """Overview: API usage summary, active keys, active webhooks, failures."""
    keys   = APIKey.objects.all()
    active_keys = keys.filter(is_active=True).count()
    total_keys  = keys.count()
    webhooks    = WebhookEndpoint.objects.all()
    active_webhooks = webhooks.filter(is_active=True).count()
    failures    = list(WebhookDeliveryLog.objects.filter(success=False).order_by('-delivered_at')[:20])
    daily_logs  = WebhookEndpoint.objects.select_related('created_by').prefetch_related(
        'deliveries').all().order_by('-last_triggered_at')[:10]

    return render(request, 'core/dashboard/developer_portal.html', {
        'total_keys': total_keys, 'active_keys': active_keys,
        'active_webhooks': active_webhooks, 'total_webhooks': webhooks.count(),
        'recent_failures': list(failures),
        'daily_logs': daily_logs,
    })


@_admin_required
def manage_api_keys(request):
    """CRUD on API keys."""
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create':
            prefix = request.POST.get('prefix', 'acad_').strip()
            name = request.POST.get('name', '').strip()
            scopes_raw = request.POST.get('scopes', '').strip()
            scopes = [s.strip() for s in scopes_raw.split(',') if s.strip()]
            ip_whitelist_raw = request.POST.get('allowed_ips', '').strip()
            allowed_ips = [ip.strip() for ip in ip_whitelist_raw.split(',') if ip.strip()]
            expires_raw = request.POST.get('expires_at', '')
            expires_at = timezone.make_aware(datetime.fromisoformat(expires_raw)) if expires_raw else None

            raw_key = uuid.uuid4().hex + uuid.uuid4().hex
            full_key = f"{prefix}{raw_key[:32]}"
            APIKey.objects.create(
                key=full_key, name=name, prefix=prefix,
                scopes=scopes, allowed_ips=allowed_ips,
                expires_at=expires_at,
                created_by=request.user,
            )
            activity_log_flat(request.user, 'other', f'Created API key: {name}')
            messages.success(request, f'API key created: {full_key[:16]}...')
            return redirect('core:manage_api_keys')

        if action == 'revoke':
            key_id = request.POST.get('key_id')
            k = APIKey.objects.filter(id=key_id).first()
            if k:
                k.is_active = False
                k.save()
                messages.success(request, f'API key "{k.name}" revoked.')
            return redirect('core:manage_api_keys')

    keys = APIKey.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'core/dashboard/manage_api_keys.html', {
        'keys': keys,
    })


@_admin_required
def manage_webhooks(request):
    """CRUD on webhook endpoints."""
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'create':
            url = request.POST.get('url', '').strip()
            events_raw = request.POST.get('events', '').strip()
            events = [e.strip() for e in events_raw.split(',') if e.strip()]
            if not url:
                messages.error(request, 'URL is required.')
            else:
                secret = uuid.uuid4().hex
                WebhookEndpoint.objects.create(
                    url=url, secret=secret, events=events, created_by=request.user,
                )
                messages.success(request, f'Webhook endpoint created: {url}')
            return redirect('core:manage_webhooks')
        if action == 'toggle':
            wh_id = request.POST.get('webhook_id')
            wh = WebhookEndpoint.objects.filter(id=wh_id).first()
            if wh:
                wh.is_active = not wh.is_active
                wh.save()
            return redirect('core:manage_webhooks')

    webhooks = WebhookEndpoint.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'core/dashboard/manage_webhooks.html', {
        'webhooks': webhooks,
    })


@_admin_required
def api_docs(request):
    """Render interactive API documentation page."""
    docs = [
        {
            'method': 'GET', 'path': '/api/students/',
            'desc': 'List all enrolled students. Optionally filter by student_id.',
            'params': 'student_id (int, optional)',
        },
        {
            'method': 'GET', 'path': '/api/results/',
            'desc': 'List all stored results. Optionally filter by student, subject, or terminal.',
            'params': 'student_id (int, optional), subject_id (int, optional), terminal (str, optional)',
        },
        {
            'method': 'GET', 'path': '/api/results/<id>/',
            'desc': 'Get a single result record with full details.',
            'params': 'id (int)',
        },
        {
            'method': 'GET', 'path': '/api/student-notifications/',
            'desc': 'Fetch notifications for the current logged-in student.',
            'params': 'unread_only (bool, GET param)',
        },
        {
            'method': 'POST', 'path': '/api/mark-notification-read/',
            'desc': 'Mark a notification as read.',
            'params': 'notification_id (int), student_id (int)',
        },
        {
            'method': 'POST', 'path': '/api/search/',
            'desc': 'Global search across students, teachers, and subjects.',
            'params': 'q (str, min 2 chars)',
        },
        {
            'method': 'GET', 'path': '/developer/api-keys/',
            'desc': 'List all API keys. Admin only.',
            'params': 'none',
        },
        {
            'method': 'POST', 'path': '/developer/webhooks/',
            'desc': 'Register a new webhook endpoint.',
            'params': 'url, events (comma-separated)',
        },
    ]
    return render(request, 'core/dashboard/api_docs.html', {'docs': docs})


def api_key_verify(request):
    """Public GET: test if an API key is valid and return its scopes."""
    raw_key = request.GET.get('key', '')
    if not raw_key:
        return JsonResponse({'valid': False, 'message': 'No key provided'}, status=400)
    k = APIKey.objects.filter(key=raw_key, is_active=True).first()
    if not k:
        return JsonResponse({'valid': False, 'message': 'Key not found or inactive'})
    expired = k.expires_at and (k.expires_at < timezone.now())
    if expired:
        return JsonResponse({'valid': False, 'message': 'Key expired', 'echo': k.prefix + '...'})
    k.last_used_at = timezone.now()
    k.save(update_fields=['last_used_at'])
    return JsonResponse({'valid': True, 'name': k.name, 'scopes': k.scopes, 'prefix': k.prefix})


def webhook_deliver(request):
    """Public POST: dispatch an event to all matching active webhooks."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'message': 'POST required'}, status=405)
    event_type = request.POST.get('event_type', request.headers.get('X-Webhook-Event', ''))
    raw_payload = request.POST.get('payload', '')
    try:
        payload = json.loads(raw_payload) if raw_payload else {}
>>>>>>> 801959c (Latest Commit)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid request data'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)