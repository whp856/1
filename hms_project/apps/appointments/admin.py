from django.contrib import admin
from apps.appointments.models import Appointment, DoctorSchedule

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'department', 'appointment_date', 'status', 'fee', 'payment_status']
    list_filter = ['status', 'payment_status', 'appointment_date']
    search_fields = ['patient__name', 'doctor__full_name']

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = ['doctor', 'date', 'max_patients', 'current_patients', 'is_available']
    list_filter = ['date', 'is_available']
