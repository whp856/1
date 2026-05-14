from django.contrib import admin
from apps.patients.models import Patient

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['name', 'id_card', 'gender', 'age', 'phone', 'created_at']
    search_fields = ['name', 'id_card', 'phone']
    list_filter = ['gender']
