from django.urls import path
from apps.pharmacy import views

urlpatterns = [
    path('medicines/', views.medicine_list, name='medicine_list'),
    path('medicines/create/', views.medicine_create, name='medicine_create'),
    path('medicines/<int:pk>/edit/', views.medicine_edit, name='medicine_edit'),
    path('stock-in/', views.stock_in, name='stock_in'),
    path('stock-in/list/', views.stock_in_list, name='stock_in_list'),
    path('stock-out/list/', views.stock_out_list, name='stock_out_list'),
    path('stock-check/', views.stock_check, name='stock_check'),
    path('stock-check/list/', views.stock_check_list, name='stock_check_list'),
    path('dispense/', views.dispense_workbench, name='dispense_workbench'),
    path('dispense/<int:prescription_id>/confirm/', views.dispense_confirm, name='dispense_confirm'),
    path('dispense/<int:prescription_id>/payment/', views.prescription_payment, name='prescription_payment'),
    path('dispense/<int:prescription_id>/reject/', views.prescription_reject, name='prescription_reject'),
]
