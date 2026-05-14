from django.urls import path
from apps.finance import views

urlpatterns = [
    path('income/', views.income_report, name='income_report'),
    path('dispense/', views.dispense_report, name='dispense_report'),
    path('dashboard/', views.data_dashboard, name='data_dashboard'),
]
