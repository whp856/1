from django.urls import path
from apps.departments import views

urlpatterns = [
    path('', views.department_list, name='department_list'),
    path('create/', views.department_create, name='department_create'),
    path('<int:pk>/edit/', views.department_edit, name='department_edit'),
    path('<int:pk>/delete/', views.department_delete, name='department_delete'),
]
