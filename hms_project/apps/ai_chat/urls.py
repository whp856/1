from django.urls import path
from apps.ai_chat import views

urlpatterns = [
    path('', views.chat_page, name='ai_chat'),
    path('api/chat/', views.chat_api, name='ai_chat_api'),
    path('api/health/', views.health_check_api, name='ai_chat_health'),
]
