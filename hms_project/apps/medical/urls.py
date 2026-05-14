from django.urls import path
from apps.medical import views

urlpatterns = [
    path('workbench/', views.doctor_workbench, name='doctor_workbench'),
    path('record/<int:appointment_id>/save/', views.medical_record_save, name='medical_record_save'),
    path('prescription/<int:appointment_id>/', views.prescription_create, name='prescription_create'),
    path('prescription/<int:prescription_id>/item/add/', views.prescription_item_add, name='prescription_item_add'),
    path('prescription/item/<int:item_id>/delete/', views.prescription_item_delete, name='prescription_item_delete'),
    path('prescription/<int:prescription_id>/submit/', views.prescription_submit, name='prescription_submit'),
    path('prescription/<int:pk>/', views.prescription_detail, name='prescription_detail'),
    path('nurse/workbench/', views.nurse_workbench, name='nurse_workbench'),
    path('nurse/record/<int:appointment_id>/save/', views.nursing_record_save, name='nursing_record_save'),
    path('nurse/record/<int:record_id>/execute/', views.nursing_record_execute, name='nursing_record_execute'),
    path('api/medicine-search/', views.medicine_search_api, name='medicine_search_api'),
]
