from django.contrib import admin
from .models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'full_name', 'role', 'department', 'phone', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'department']
    search_fields = ['username', 'full_name', 'phone']
    ordering = ['-date_joined']
