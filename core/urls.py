from django.urls import path
from . import views
from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # main page after login
    path('add-marks/', views.add_marks, name='add_marks'),
    path('marks-list/', views.marks_list, name='marks_list'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
]