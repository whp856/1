from django.contrib import admin
from apps.medical.models import MedicalRecord, NursingRecord, Prescription, PrescriptionItem

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'doctor', 'diagnosis', 'created_at']
    search_fields = ['patient__name', 'diagnosis']

@admin.register(NursingRecord)
class NursingRecordAdmin(admin.ModelAdmin):
    list_display = ['patient', 'nurse', 'execution_status', 'executed_at', 'created_at']
    list_filter = ['execution_status']

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ['id', 'patient', 'doctor', 'total_amount', 'status', 'created_at']
    list_filter = ['status']

@admin.register(PrescriptionItem)
class PrescriptionItemAdmin(admin.ModelAdmin):
    list_display = ['prescription', 'medicine', 'quantity', 'dosage', 'subtotal']
