
from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
path('admin/', admin.site.urls),
path('accounts/', include('django.contrib.auth.urls')),
path('', views.home, name='home'),
path('dashboard/', views.dashboard, name='dashboard'),
]
