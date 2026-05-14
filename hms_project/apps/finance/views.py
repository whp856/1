from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count, Q, F
from django.http import HttpRequest, HttpResponse
from datetime import date, timedelta

from apps.accounts.decorators import admin_required
from apps.appointments.models import Appointment
from apps.medical.models import Prescription, PrescriptionItem
from apps.pharmacy.models import Medicine


@login_required
@admin_required
def income_report(request: HttpRequest) -> HttpResponse:
    period = request.GET.get('period', 'today')
    today = date.today()

    if period == 'today':
        start = today
        end = today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        end = today
    elif period == 'month':
        start = today.replace(day=1)
        end = today
    elif period == 'custom':
        start = request.GET.get('start_date', str(today))
        end = request.GET.get('end_date', str(today))
    else:
        start = today
        end = today

    registration_income = Appointment.objects.filter(
        payment_status=True,
        created_at__date__gte=start,
        created_at__date__lte=end,
    ).aggregate(total=Sum('fee'))['total'] or 0

    prescription_income = Prescription.objects.filter(
        status__in=['paid', 'dispensed'],
        payment_time__date__gte=start,
        payment_time__date__lte=end,
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    total_income = float(registration_income) + float(prescription_income)
    appointment_count = Appointment.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).count()

    dept_stats = Appointment.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).values('department__name').annotate(
        count=Count('id'), income=Sum('fee')
    ).order_by('-count')

    doctor_stats = Appointment.objects.filter(
        created_at__date__gte=start, created_at__date__lte=end
    ).values('doctor__full_name', 'doctor__department__name').annotate(
        count=Count('id'), income=Sum('fee')
    ).order_by('-count')

    return render(request, 'finance/income_report.html', {
        'period': period,
        'start': start,
        'end': end,
        'registration_income': registration_income,
        'prescription_income': prescription_income,
        'total_income': total_income,
        'appointment_count': appointment_count,
        'dept_stats': dept_stats,
        'doctor_stats': doctor_stats,
    })


@login_required
@admin_required
def dispense_report(request: HttpRequest) -> HttpResponse:
    period = request.GET.get('period', 'today')
    today = date.today()

    if period == 'today':
        start = today
        end = today
    elif period == 'week':
        start = today - timedelta(days=today.weekday())
        end = today
    elif period == 'month':
        start = today.replace(day=1)
        end = today
    else:
        start = today
        end = today

    pharmacist_stats = Prescription.objects.filter(
        status='dispensed',
        dispense_time__date__gte=start,
        dispense_time__date__lte=end,
    ).values('pharmacist__full_name').annotate(
        count=Count('id'), total_amount=Sum('total_amount')
    ).order_by('-count')

    medicine_stats = PrescriptionItem.objects.filter(
        prescription__status='dispensed',
        prescription__dispense_time__date__gte=start,
        prescription__dispense_time__date__lte=end,
    ).values('medicine__name', 'medicine__specification').annotate(
        total_quantity=Sum('quantity'), total_amount=Sum('subtotal')
    ).order_by('-total_amount')

    return render(request, 'finance/dispense_report.html', {
        'period': period,
        'start': start,
        'end': end,
        'pharmacist_stats': pharmacist_stats,
        'medicine_stats': medicine_stats,
    })


@login_required
@admin_required
def data_dashboard(request: HttpRequest) -> HttpResponse:
    today = date.today()
    week_start = today - timedelta(days=today.weekday())

    today_appointments = Appointment.objects.filter(appointment_date=today)
    today_income = today_appointments.filter(payment_status=True).aggregate(
        total=Sum('fee')
    )['total'] or 0
    today_prescription_income = Prescription.objects.filter(
        status__in=['paid', 'dispensed'], payment_time__date=today
    ).aggregate(total=Sum('total_amount'))['total'] or 0

    week_appointments = Appointment.objects.filter(
        appointment_date__gte=week_start, appointment_date__lte=today
    ).count()

    total_patients = Appointment.objects.values('patient').distinct().count()

    dept_rank = Appointment.objects.filter(appointment_date=today).values(
        'department__name'
    ).annotate(count=Count('id')).order_by('-count')[:5]

    doctor_rank = Appointment.objects.filter(appointment_date=today).values(
        'doctor__full_name'
    ).annotate(count=Count('id')).order_by('-count')[:5]

    low_stock = Medicine.objects.filter(
        stock_quantity__lte=F('warning_stock'), is_active=True
    ).count()
    expiring = Medicine.objects.filter(
        expiry_date__lte=today + timedelta(days=30), is_active=True
    ).count()

    return render(request, 'finance/dashboard.html', {
        'today': today,
        'today_appointment_count': today_appointments.count(),
        'today_completed': today_appointments.filter(status='completed').count(),
        'today_pending': today_appointments.filter(status='pending').count(),
        'today_income': float(today_income) + float(today_prescription_income),
        'today_registration_income': today_income,
        'today_prescription_income': today_prescription_income,
        'week_appointments': week_appointments,
        'total_patients': total_patients,
        'dept_rank': dept_rank,
        'doctor_rank': doctor_rank,
        'low_stock_count': low_stock,
        'expiring_count': expiring,
    })
