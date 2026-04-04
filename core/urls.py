from django.contrib.auth import views as auth_views
from django.urls import path
from core import views

app_name= "core"

urlpatterns = [
    path('', views.home_view, name='home'),

    path('dashboard/', views.dashboard, name='dashboard'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('add-marks/', views.add_marks, name='add_marks'),
    path('marks-list/', views.marks_list, name='marks_list'),

    # QR & Attendance
    path('qr-codes/', views.qr_codes, name='qr_codes'),
    path('qr-codes/<int:student_id>/', views.student_qr_code, name='student_qr_code'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('mobile-scanner/', views.mobile_scanner, name='mobile_scanner'),
    path('process-qr-scan/', views.process_qr_scan, name='process_qr_scan'),
    path('regenerate-qr/', views.regenerate_qr_codes, name='regenerate_qr_codes'),

    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),

    # Marksheet
    path('mark-sheet/', views.mark_sheet, name='mark_sheet'),
    path('mark-sheet/<int:student_id>/<str:terminal>/', views.mark_sheet, name='mark_sheet_terminal'),
    path('mark-sheet/<int:student_id>/', views.mark_sheet, name='mark_sheet_student'),

    # Analysis
    path('student-analysis/', views.student_analysis, name='student_analysis'),

    # API
    path('chart-data/', views.chart_data, name='chart_data'),
    path('api/add-marks-bulk/', views.add_marks_bulk, name='add_marks_bulk'),
    path('api/student-info/<int:student_id>/', views.student_info, name='student_info'),
]
