from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # main page after login
    path('add-marks/', views.add_marks, name='add_marks'),
    path('marks-list/', views.marks_list, name='marks_list'),
    path('edit-marks/<int:mark_id>/', views.edit_marks, name='edit_marks'),
    path('delete-marks/<int:mark_id>/', views.delete_marks, name='delete_marks'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # QR Code & Attendance URLs
    path('qr-codes/', views.qr_codes, name='qr_codes'),
    path('qr-codes/<int:student_id>/', views.student_qr_code, name='student_qr_code'),
    path('qr-scanner/', views.qr_scanner, name='qr_scanner'),
    path('mobile-scanner/', views.mobile_scanner, name='mobile_scanner'),
    path('process-qr-scan/', views.process_qr_scan, name='process_qr_scan'),
    path('regenerate-qr/', views.regenerate_qr_codes, name='regenerate_qr_codes'),
    path('attendance/', views.attendance_list, name='attendance_list'),
    path('attendance-report/', views.attendance_report, name='attendance_report'),
]