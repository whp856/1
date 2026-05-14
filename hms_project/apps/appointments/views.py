from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from datetime import date, timedelta

from apps.accounts.decorators import admin_required, nurse_required, doctor_required
from apps.appointments.models import Appointment, DoctorSchedule
from apps.appointments.forms import AppointmentForm, DoctorScheduleForm
from apps.accounts.models import User


@login_required
def appointment_list(request: HttpRequest) -> HttpResponse:
    qs = Appointment.objects.select_related('patient', 'doctor', 'department').all()
    if request.user.is_doctor:
        qs = qs.filter(doctor=request.user)
    elif request.user.is_nurse:
        if request.user.department:
            qs = qs.filter(department=request.user.department)

    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    search = request.GET.get('search', '')

    if status_filter:
        qs = qs.filter(status=status_filter)
    if date_filter:
        qs = qs.filter(appointment_date=date_filter)
    if doctor_filter:
        qs = qs.filter(doctor_id=doctor_filter)
    if search:
        qs = qs.filter(Q(patient__name__icontains=search) | Q(patient__phone__icontains=search))

    doctors = User.objects.filter(role='doctor', is_active=True)

    return render(request, 'appointments/appointment_list.html', {
        'appointments': qs,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'search': search,
        'doctors': doctors,
        'status_choices': Appointment.Status.choices,
    })


@login_required
def appointment_create(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            if not appointment.department_id:
                appointment.department = appointment.doctor.department
            if appointment.payment_method:
                appointment.payment_status = True
            appointment.save()

            schedule, _ = DoctorSchedule.objects.get_or_create(
                doctor=appointment.doctor,
                date=appointment.appointment_date,
                defaults={'max_patients': 30},
            )
            schedule.current_patients += 1
            schedule.save(update_fields=['current_patients'])

            messages.success(request, f'挂号成功！挂号单号: {appointment.id}')
            return redirect('appointment_list')
    else:
        form = AppointmentForm()

    doctors = User.objects.filter(role='doctor', is_active=True).select_related('department')
    return render(request, 'appointments/appointment_form.html', {
        'form': form,
        'action': '新建挂号',
        'doctors': doctors,
    })


@login_required
def appointment_detail(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(
        Appointment.objects.select_related('patient', 'doctor', 'department'), pk=pk
    )
    return render(request, 'appointments/appointment_detail.html', {'appointment': appointment})


@login_required
def appointment_cancel(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.status != 'pending':
        messages.error(request, '仅待就诊状态的挂号可以取消')
        return redirect('appointment_list')
    if not appointment.can_cancel():
        messages.error(request, '就诊前30分钟内不可取消挂号')
        return redirect('appointment_list')

    appointment.status = 'cancelled'
    appointment.save(update_fields=['status'])

    schedule = DoctorSchedule.objects.filter(
        doctor=appointment.doctor, date=appointment.appointment_date
    ).first()
    if schedule and schedule.current_patients > 0:
        schedule.current_patients -= 1
        schedule.save(update_fields=['current_patients'])

    messages.success(request, '挂号已取消')
    return redirect('appointment_list')


@login_required
@nurse_required
def appointment_payment(request: HttpRequest, pk: int) -> HttpResponse:
    appointment = get_object_or_404(Appointment, pk=pk)
    if appointment.payment_status:
        messages.warning(request, '该挂号已支付')
        return redirect('appointment_list')
    method = request.POST.get('payment_method', 'cash')
    appointment.payment_method = method
    appointment.payment_status = True
    appointment.save(update_fields=['payment_method', 'payment_status'])
    messages.success(request, f'挂号费 ¥{appointment.fee} 已通过{appointment.get_payment_method_display()}收取')
    return redirect('appointment_list')


@login_required
@doctor_required
def doctor_queue(request: HttpRequest) -> HttpResponse:
    today = date.today()
    pending = Appointment.objects.filter(
        doctor=request.user, appointment_date=today, status='pending'
    ).select_related('patient').order_by('appointment_time')
    return render(request, 'appointments/queue_management.html', {
        'pending_patients': pending,
        'today': today,
    })


@login_required
@admin_required
def schedule_list(request: HttpRequest) -> HttpResponse:
    schedules = DoctorSchedule.objects.select_related('doctor').all()
    date_filter = request.GET.get('date', '')
    doctor_filter = request.GET.get('doctor', '')
    if date_filter:
        schedules = schedules.filter(date=date_filter)
    if doctor_filter:
        schedules = schedules.filter(doctor_id=doctor_filter)
    doctors = User.objects.filter(role='doctor', is_active=True)
    return render(request, 'appointments/schedule_list.html', {
        'schedules': schedules,
        'date_filter': date_filter,
        'doctor_filter': doctor_filter,
        'doctors': doctors,
    })


@login_required
@admin_required
def schedule_create(request: HttpRequest) -> HttpResponse:
    form = DoctorScheduleForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '排班信息创建成功')
        return redirect('schedule_list')
    return render(request, 'appointments/schedule_form.html', {'form': form, 'action': '创建排班'})


@login_required
@admin_required
def schedule_edit(request: HttpRequest, pk: int) -> HttpResponse:
    schedule = get_object_or_404(DoctorSchedule, pk=pk)
    form = DoctorScheduleForm(request.POST or None, instance=schedule)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '排班信息更新成功')
        return redirect('schedule_list')
    return render(request, 'appointments/schedule_form.html', {'form': form, 'action': '编辑排班'})


@login_required
@admin_required
def schedule_toggle(request: HttpRequest, pk: int) -> HttpResponse:
    schedule = get_object_or_404(DoctorSchedule, pk=pk)
    schedule.is_available = not schedule.is_available
    schedule.save(update_fields=['is_available'])
    status_text = '开放挂号' if schedule.is_available else '暂停挂号'
    messages.success(request, f'{schedule.doctor.get_full_name()} {schedule.date} 已{status_text}')
    return redirect('schedule_list')


@login_required
def get_doctor_schedule_api(request: HttpRequest) -> JsonResponse:
    doctor_id = request.GET.get('doctor_id', '')
    date_str = request.GET.get('date', '')
    if not doctor_id or not date_str:
        return JsonResponse({'error': '参数缺失'}, status=400)
    try:
        schedule = DoctorSchedule.objects.get(doctor_id=doctor_id, date=date_str)
        return JsonResponse({
            'max_patients': schedule.max_patients,
            'current_patients': schedule.current_patients,
            'remaining': schedule.remaining,
            'is_available': schedule.is_available,
        })
    except DoctorSchedule.DoesNotExist:
        return JsonResponse({
            'max_patients': 30,
            'current_patients': 0,
            'remaining': 30,
            'is_available': True,
        })
