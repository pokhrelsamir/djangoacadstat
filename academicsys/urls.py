from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home_view, name='home'),  # Landing page (no login required)
    path('dashboard/', views.dashboard, name='dashboard'),  # Dashboard (requires login)
    path('add-marks/', views.add_marks, name='add_marks'),
    path('marks-list/', views.marks_list, name='marks_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # QR Code & Attendance
    path('qr-codes/', views.qr_codes, name='qr_codes'),
    path('qr-codes/<int:student_id>/', views.student_qr_code, name='student_qr_code'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('mobile-scanner/', views.mobile_scanner, name='mobile_scanner'),
    path('process-qr-scan/', views.process_qr_scan, name='process_qr_scan'),
    path('regenerate-qr/', views.regenerate_qr_codes, name='regenerate_qr_codes'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),
    # Mark Sheet URLs
    path('mark-sheet/', views.mark_sheet, name='mark_sheet'),
    path('mark-sheet/<int:student_id>/<str:terminal>/', views.mark_sheet, name='mark_sheet_terminal'),
    path('mark-sheet/<int:student_id>/', views.mark_sheet, name='mark_sheet_student'),
    # Student Analysis URL
    path('student-analysis/', views.student_analysis, name='student_analysis'),
    # Chart Data API
    path('chart-data/', views.chart_data, name='chart_data'),
]
