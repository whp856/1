from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum, Count, F
from django.http import HttpRequest, HttpResponse
from datetime import date, timedelta

from apps.accounts.models import User
from apps.accounts.forms import LoginForm, UserCreateForm, UserEditForm
from apps.accounts.decorators import admin_required
from apps.appointments.models import Appointment
from apps.pharmacy.models import Medicine


def login_view(request: HttpRequest) -> HttpResponse:
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        if not user.is_active:
            messages.error(request, '账号已被禁用，请联系管理员')
            return render(request, 'login.html', {'form': form})
        login(request, user)
        messages.success(request, f'欢迎回来，{user.full_name}')
        return redirect('dashboard')
    return render(request, 'login.html', {'form': form})


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, '您已安全退出系统')
    return redirect('login')


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    today = date.today()
    context = {'today': today}

    if request.user.is_admin:
        context.update(_admin_dashboard_data(today))
    elif request.user.is_doctor:
        context.update(_doctor_dashboard_data(request.user, today))
    elif request.user.is_nurse:
        context.update(_nurse_dashboard_data(request.user, today))
    elif request.user.is_pharmacist:
        context.update(_pharmacist_dashboard_data(request.user, today))

    return render(request, 'dashboard.html', context)


def _admin_dashboard_data(today: date) -> dict:
    today_appointments = Appointment.objects.filter(appointment_date=today)
    return {
        'today_appointment_count': today_appointments.count(),
        'today_completed_count': today_appointments.filter(status='completed').count(),
        'today_pending_count': today_appointments.filter(status='pending').count(),
        'today_income': today_appointments.filter(payment_status=True).aggregate(
            total=Sum('fee')
        )['total'] or 0,
        'total_patients': Appointment.objects.values('patient').distinct().count(),
        'low_stock_medicines': Medicine.objects.filter(
            stock_quantity__lte=F('warning_stock'), is_active=True
        )[:10],
        'expiring_medicines': Medicine.objects.filter(
            expiry_date__lte=today + timedelta(days=30), is_active=True
        )[:10],
        'recent_appointments': Appointment.objects.select_related(
            'patient', 'doctor', 'department'
        ).order_by('-created_at')[:10],
    }


def _doctor_dashboard_data(user: User, today: date) -> dict:
    pending = Appointment.objects.filter(doctor=user, appointment_date=today, status='pending')
    return {
        'today_pending_count': pending.count(),
        'today_completed_count': Appointment.objects.filter(
            doctor=user, appointment_date=today, status='completed'
        ).count(),
        'pending_patients': pending.select_related('patient').order_by('appointment_time'),
        'recent_records': user.medical_records.select_related('patient').order_by('-created_at')[:5],
    }


def _nurse_dashboard_data(user: User, today: date) -> dict:
    dept = user.department
    base_qs = Appointment.objects.filter(appointment_date=today, status='pending')
    if dept:
        base_qs = base_qs.filter(department=dept)
    return {
        'today_pending_count': base_qs.count(),
        'department_patients': base_qs.select_related('patient', 'doctor').order_by('appointment_time'),
        'pending_nursing': user.nursing_records.filter(
            execution_status='pending'
        ).select_related('patient').order_by('-created_at')[:10],
    }


def _pharmacist_dashboard_data(user: User, today: date) -> dict:
    from apps.medical.models import Prescription
    return {
        'pending_dispense': Prescription.objects.filter(
            status='paid'
        ).select_related('patient', 'doctor').order_by('-created_at')[:10],
        'today_dispensed': Prescription.objects.filter(
            status='dispensed', pharmacist=user, dispense_time__date=today
        ).count(),
        'low_stock_medicines': Medicine.objects.filter(
            stock_quantity__lte=F('warning_stock'), is_active=True
        )[:5],
        'expiring_medicines': Medicine.objects.filter(
            expiry_date__lte=today + timedelta(days=30), is_active=True
        )[:5],
    }


@login_required
@admin_required
def user_list(request: HttpRequest) -> HttpResponse:
    users = User.objects.select_related('department').all()
    role_filter = request.GET.get('role', '')
    search = request.GET.get('search', '')
    if role_filter:
        users = users.filter(role=role_filter)
    if search:
        users = users.filter(
            Q(username__icontains=search) | Q(full_name__icontains=search) | Q(phone__icontains=search)
        )
    return render(request, 'accounts/user_list.html', {
        'users': users,
        'role_filter': role_filter,
        'search': search,
        'role_choices': User.Role.choices,
    })


@login_required
@admin_required
def user_create(request: HttpRequest) -> HttpResponse:
    form = UserCreateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '用户创建成功')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': '创建'})


@login_required
@admin_required
def user_edit(request: HttpRequest, pk: int) -> HttpResponse:
    user = get_object_or_404(User, pk=pk)
    form = UserEditForm(request.POST or None, instance=user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '用户信息更新成功')
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'form': form, 'action': '编辑', 'edit_user': user})


@login_required
@admin_required
def user_toggle_active(request: HttpRequest, pk: int) -> HttpResponse:
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, '不能禁用自己的账号')
        return redirect('user_list')
    user.is_active = not user.is_active
    user.save(update_fields=['is_active'])
    status = '启用' if user.is_active else '禁用'
    messages.success(request, f'用户 {user.full_name} 已{status}')
    return redirect('user_list')
