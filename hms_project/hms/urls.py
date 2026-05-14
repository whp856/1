from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.accounts.urls')),
    path('departments/', include('apps.departments.urls')),
    path('patients/', include('apps.patients.urls')),
    path('appointments/', include('apps.appointments.urls')),
    path('medical/', include('apps.medical.urls')),
    path('pharmacy/', include('apps.pharmacy.urls')),
    path('finance/', include('apps.finance.urls')),
]
