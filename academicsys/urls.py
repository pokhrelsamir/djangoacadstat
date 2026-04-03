from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),   # GLOBAL
    path('', include('core.urls')),    # send to app
]