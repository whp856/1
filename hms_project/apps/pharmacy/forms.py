from django import forms
from apps.pharmacy.models import Medicine, StockIn, StockCheck


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'specification', 'manufacturer', 'unit_price',
                   'warning_stock', 'expiry_date', 'category', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '药品名称'}),
            'specification': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '如: 0.25g*24片'}),
            'manufacturer': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '生产厂家'}),
            'unit_price': forms.NumberInput(attrs={'class': 'hms-input', 'step': '0.01', 'min': '0'}),
            'warning_stock': forms.NumberInput(attrs={'class': 'hms-input', 'min': '0'}),
            'expiry_date': forms.DateInput(attrs={'class': 'hms-input', 'type': 'date'}),
            'category': forms.Select(attrs={'class': 'hms-select'}),
        }

    def clean_unit_price(self) -> float:
        price = self.cleaned_data['unit_price']
        if price <= 0:
            raise forms.ValidationError('单价必须大于0')
        return price

    def clean(self):
        cleaned = super().clean()
        name = cleaned.get('name', '')
        if name:
            import re
            pinyin = ''.join(
                re.findall(r'[\u4e00-\u9fff]', name)
            )
            try:
                from pypinyin import lazy_pinyin
                cleaned['pinyin_code'] = ''.join([w[0].upper() for w in lazy_pinyin(name)])
            except ImportError:
                cleaned['pinyin_code'] = name[:10].upper()
        return cleaned


class StockInForm(forms.ModelForm):
    class Meta:
        model = StockIn
        fields = ['medicine', 'quantity', 'unit_price', 'batch_number', 'supplier', 'note']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'hms-select'}),
            'quantity': forms.NumberInput(attrs={'class': 'hms-input', 'min': '1'}),
            'unit_price': forms.NumberInput(attrs={'class': 'hms-input', 'step': '0.01', 'min': '0'}),
            'batch_number': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '批次号'}),
            'supplier': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '供应商'}),
            'note': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '备注'}),
        }


class StockCheckForm(forms.ModelForm):
    class Meta:
        model = StockCheck
        fields = ['medicine', 'actual_quantity', 'note']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'hms-select'}),
            'actual_quantity': forms.NumberInput(attrs={'class': 'hms-input', 'min': '0'}),
            'note': forms.Textarea(attrs={'class': 'hms-textarea', 'rows': 2, 'placeholder': '备注'}),
        }
