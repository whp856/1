from django import forms
from django.contrib.auth.forms import AuthenticationForm
from apps.accounts.models import User


class LoginForm(AuthenticationForm):
    username = forms.CharField(
        label='用户名',
        widget=forms.TextInput(attrs={
            'class': 'hms-input',
            'placeholder': '请输入用户名',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={
            'class': 'hms-input',
            'placeholder': '请输入密码',
            'autocomplete': 'current-password',
        }),
    )


class UserCreateForm(forms.ModelForm):
    password = forms.CharField(
        label='密码',
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'hms-input', 'placeholder': '至少6位'}),
    )
    password_confirm = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'class': 'hms-input', 'placeholder': '再次输入密码'}),
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'role', 'department', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '登录用户名'}),
            'full_name': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '真实姓名'}),
            'role': forms.Select(attrs={'class': 'hms-select'}),
            'department': forms.Select(attrs={'class': 'hms-select'}),
            'phone': forms.TextInput(attrs={'class': 'hms-input', 'placeholder': '联系电话'}),
        }

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('password') != cleaned.get('password_confirm'):
            raise forms.ValidationError('两次输入的密码不一致')
        return cleaned

    def save(self, commit: bool = True) -> User:
        user: User = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserEditForm(forms.ModelForm):
    new_password = forms.CharField(
        label='新密码',
        required=False,
        min_length=6,
        widget=forms.PasswordInput(attrs={'class': 'hms-input', 'placeholder': '留空则不修改'}),
    )

    class Meta:
        model = User
        fields = ['username', 'full_name', 'role', 'department', 'phone', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'hms-input'}),
            'full_name': forms.TextInput(attrs={'class': 'hms-input'}),
            'role': forms.Select(attrs={'class': 'hms-select'}),
            'department': forms.Select(attrs={'class': 'hms-select'}),
            'phone': forms.TextInput(attrs={'class': 'hms-input'}),
        }

    def save(self, commit: bool = True) -> User:
        user: User = super().save(commit=False)
        new_pw = self.cleaned_data.get('new_password')
        if new_pw:
            user.set_password(new_pw)
        if commit:
            user.save()
        return user
