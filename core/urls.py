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
]