from django import forms
from apps.appointments.models import Appointment, DoctorSchedule


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['patient', 'doctor', 'department', 'appointment_date', 'appointment_time', 'fee', 'payment_method']
        widgets = {
            'patient': forms.Select(attrs={'class': 'hms-select'}),
            'doctor': forms.Select(attrs={'class': 'hms-select'}),
            'department': forms.Select(attrs={'class': 'hms-select'}),
            'appointment_date': forms.DateInput(attrs={'class': 'hms-input', 'type': 'date'}),
            'appointment_time': forms.TimeInput(attrs={'class': 'hms-input', 'type': 'time'}),
            'fee': forms.NumberInput(attrs={'class': 'hms-input', 'placeholder': '挂号费', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'hms-select'}),
        }

    def clean(self):
        cleaned = super().clean()
        doctor = cleaned.get('doctor')
        appointment_date = cleaned.get('appointment_date')
        if doctor and appointment_date:
            schedule, _ = DoctorSchedule.objects.get_or_create(
                doctor=doctor,
                date=appointment_date,
                defaults={'max_patients': 30},
            )
            if schedule.is_full and not schedule.is_available:
                raise forms.ValidationError('该医生当日号源已满，请选择其他医生或日期')
        return cleaned


class DoctorScheduleForm(forms.ModelForm):
    class Meta:
        model = DoctorSchedule
        fields = ['doctor', 'date', 'max_patients', 'is_available']
        widgets = {
            'doctor': forms.Select(attrs={'class': 'hms-select'}),
            'date': forms.DateInput(attrs={'class': 'hms-input', 'type': 'date'}),
            'max_patients': forms.NumberInput(attrs={'class': 'hms-input', 'min': '1'}),
        }
