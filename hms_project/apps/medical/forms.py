from django import forms
from apps.medical.models import MedicalRecord, NursingRecord, Prescription, PrescriptionItem


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = [
            'chief_complaint', 'present_illness', 'past_history',
            'physical_examination', 'diagnosis', 'treatment_plan', 'advice',
        ]
        widgets = {
            'chief_complaint': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '患者主要不适'}),
            'present_illness': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 3, 'placeholder': '现病史'}),
            'past_history': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '既往史'}),
            'physical_examination': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '体格检查结果'}),
            'diagnosis': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '诊断结果（必填）'}),
            'treatment_plan': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 3, 'placeholder': '治疗方案'}),
            'advice': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '医嘱建议'}),
        }


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ['medicine', 'quantity', 'dosage', 'unit_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'hms-select medicine-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'hms-input', 'min': '1'}),
            'dosage': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '如: 每日3次,每次1片'}),
            'unit_price': forms.NumberInput(attrs={'class': 'hms-input', 'step': '0.01', 'readonly': 'readonly'}),
        }


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['note']


class NursingRecordForm(forms.ModelForm):
    class Meta:
        model = NursingRecord
        fields = ['temperature', 'blood_pressure', 'heart_rate', 'medical_order', 'note']
        widgets = {
            'temperature': forms.NumberInput(attrs={'class': 'hms-input', 'step': '0.1', 'placeholder': '体温(℃)'}),
            'blood_pressure': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '如: 120/80'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'hms-input', 'placeholder': '心率(次/分)'}),
            'medical_order': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '医嘱内容'}),
            'note': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '护理备注'}),
        }
