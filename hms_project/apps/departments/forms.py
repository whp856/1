from django import forms
from apps.departments.models import Department


class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '科室名称'}),
            'description': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 3, 'placeholder': '科室描述（选填）'}),
        }
