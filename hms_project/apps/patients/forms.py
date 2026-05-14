from django import forms
from apps.patients.models import Patient


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = ['id_card', 'name', 'gender', 'age', 'phone', 'allergy_history']
        widgets = {
            'id_card': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '18位身份证号', 'maxlength': '18'}),
            'name': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '患者姓名'}),
            'gender': forms.Select(attrs={'class': 'hms-select'}),
            'age': forms.NumberInput(attrs={'class': 'hms-input', 'placeholder': '年龄', 'min': '0', 'max': '150'}),
            'phone': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '联系电话', 'maxlength': '20'}),
            'allergy_history': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '过敏史（选填）'}),
        }

    def clean_id_card(self) -> str:
        id_card = self.cleaned_data['id_card']
        if len(id_card) != 18:
            raise forms.ValidationError('身份证号必须为18位')
        qs = Patient.objects.filter(id_card=id_card)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('该身份证号已建档')
        return id_card

    def clean_phone(self) -> str:
        phone = self.cleaned_data['phone']
        if not phone.isdigit() or len(phone) < 7:
            raise forms.ValidationError('请输入有效的联系电话')
        return phone

    def clean_age(self) -> int:
        age = self.cleaned_data['age']
        if age < 0 or age > 150:
            raise forms.ValidationError('年龄范围应在 0-150 之间')
        return age
