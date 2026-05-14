from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db import transaction
from django.utils import timezone
from datetime import date

from apps.accounts.decorators import doctor_required, nurse_required, pharmacist_required
from apps.appointments.models import Appointment
from apps.medical.models import MedicalRecord, NursingRecord, Prescription, PrescriptionItem
from apps.medical.forms import MedicalRecordForm, PrescriptionForm, PrescriptionItemForm, NursingRecordForm
from apps.pharmacy.models import Medicine


@login_required
@doctor_required
def doctor_workbench(request: HttpRequest) -> HttpResponse:
    today = date.today()
    pending = Appointment.objects.filter(
        doctor=request.user, appointment_date=today, status='pending'
    ).select_related('patient').order_by('appointment_time')

    appointment_id = request.GET.get('appointment_id')
    current_appointment = None
    medical_form = None
    prescription_form = None
    history_records = None

    if appointment_id:
        current_appointment = get_object_or_404(
            Appointment.objects.select_related('patient'),
            pk=appointment_id, doctor=request.user,
        )
        if hasattr(current_appointment, 'medical_record'):
            medical_form = MedicalRecordForm(instance=current_appointment.medical_record)
        else:
            medical_form = MedicalRecordForm()
        prescription_form = PrescriptionForm()
        history_records = MedicalRecord.objects.filter(
            patient=current_appointment.patient
        ).exclude(appointment=current_appointment).order_by('-created_at')[:10]

    return render(request, 'medical/doctor_workbench.html', {
        'pending_patients': pending,
        'current_appointment': current_appointment,
        'medical_form': medical_form,
        'prescription_form': prescription_form,
        'history_records': history_records,
        'today': today,
    })


@login_required
@doctor_required
def medical_record_save(request: HttpRequest, appointment_id: int) -> HttpResponse:
    appointment = get_object_or_404(
        Appointment, pk=appointment_id, doctor=request.user, status='pending'
    )
    record, created = MedicalRecord.objects.get_or_create(
        appointment=appointment,
        defaults={
            'patient': appointment.patient,
            'doctor': request.user,
        },
    )
    form = MedicalRecordForm(request.POST or None, instance=record)
    if request.method == 'POST' and form.is_valid():
        form.save()
        appointment.status = 'completed'
        appointment.save(update_fields=['status'])
        messages.success(request, '病历保存成功，本次就诊已完成')
        return redirect('doctor_workbench')
    return redirect(f'{request.path}?appointment_id={appointment_id}')


@login_required
@doctor_required
def prescription_create(request: HttpRequest, appointment_id: int) -> HttpResponse:
    appointment = get_object_or_404(Appointment, pk=appointment_id, doctor=request.user)

    if not hasattr(appointment, 'medical_record'):
        messages.error(request, '请先完成病历填写后再开具处方')
        return redirect(f'/medical/workbench/?appointment_id={appointment_id}')

    if hasattr(appointment, 'prescription'):
        prescription = appointment.prescription
    else:
        prescription = Prescription.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            doctor=request.user,
        )

    medicines = Medicine.objects.filter(is_active=True)
    search = request.GET.get('medicine_search', '')
    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) | Q(pinyin_code__icontains=search)
        )

    return render(request, 'medical/prescription_form.html', {
        'prescription': prescription,
        'appointment': appointment,
        'medicines': medicines[:50],
        'search': search,
        'item_form': PrescriptionItemForm(),
    })


@login_required
@doctor_required
def prescription_item_add(request: HttpRequest, prescription_id: int) -> JsonResponse:
    prescription = get_object_or_404(Prescription, pk=prescription_id, doctor=request.user)
    if prescription.status != 'pending':
        return JsonResponse({'error': '处方状态不允许修改'}, status=400)

    if request.method == 'POST':
        medicine_id = request.POST.get('medicine')
        quantity = int(request.POST.get('quantity', 1))
        dosage = request.POST.get('dosage', '')
        medicine = get_object_or_404(Medicine, pk=medicine_id, is_active=True)

        if quantity > medicine.stock_quantity:
            return JsonResponse({
                'error': f'{medicine.name} 库存不足，当前库存: {medicine.stock_quantity}',
            }, status=400)

        item = PrescriptionItem.objects.create(
            prescription=prescription,
            medicine=medicine,
            quantity=quantity,
            dosage=dosage,
            unit_price=medicine.unit_price,
        )
        prescription.calculate_total()
        return JsonResponse({
            'id': item.id,
            'medicine_name': medicine.name,
            'specification': medicine.specification,
            'quantity': item.quantity,
            'dosage': item.dosage,
            'unit_price': str(item.unit_price),
            'subtotal': str(item.subtotal),
            'total': str(prescription.total_amount),
        })
    return JsonResponse({'error': '无效请求'}, status=400)


@login_required
@doctor_required
def prescription_item_delete(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(PrescriptionItem, pk=item_id, prescription__doctor=request.user)
    if item.prescription.status != 'pending':
        return JsonResponse({'error': '处方状态不允许修改'}, status=400)
    prescription = item.prescription
    item.delete()
    prescription.calculate_total()
    return JsonResponse({'success': True, 'total': str(prescription.total_amount)})


@login_required
@doctor_required
def prescription_submit(request: HttpRequest, prescription_id: int) -> HttpResponse:
    prescription = get_object_or_404(Prescription, pk=prescription_id, doctor=request.user)
    if not prescription.items.exists():
        messages.error(request, '处方不能为空，请添加药品')
        return redirect('prescription_create', appointment_id=prescription.appointment_id)

    for item in prescription.items.all():
        if item.quantity > item.medicine.stock_quantity:
            messages.error(
                request,
                f'{item.medicine.name} 库存不足 (库存:{item.medicine.stock_quantity}, 需要:{item.quantity})',
            )
            return redirect('prescription_create', appointment_id=prescription.appointment_id)

    messages.success(request, f'处方已提交至药房，总金额: ¥{prescription.total_amount}')
    return redirect('doctor_workbench')


@login_required
def prescription_detail(request: HttpRequest, pk: int) -> HttpResponse:
    prescription = get_object_or_404(
        Prescription.objects.select_related('patient', 'doctor', 'pharmacist'), pk=pk
    )
    items = prescription.items.select_related('medicine').all()
    return render(request, 'medical/prescription_detail.html', {
        'prescription': prescription,
        'items': items,
    })


@login_required
@nurse_required
def nurse_workbench(request: HttpRequest) -> HttpResponse:
    today = date.today()
    qs = Appointment.objects.filter(appointment_date=today).select_related('patient', 'doctor')
    if request.user.department:
        qs = qs.filter(department=request.user.department)

    appointment_id = request.GET.get('appointment_id')
    current_appointment = None
    nursing_form = None
    existing_records = None

    if appointment_id:
        current_appointment = get_object_or_404(qs, pk=appointment_id)
        nursing_form = NursingRecordForm()
        existing_records = NursingRecord.objects.filter(
            appointment=current_appointment
        ).order_by('-created_at')

    return render(request, 'medical/nurse_workbench.html', {
        'department_patients': qs.order_by('appointment_time'),
        'current_appointment': current_appointment,
        'nursing_form': nursing_form,
        'existing_records': existing_records,
        'today': today,
    })


@login_required
@nurse_required
def nursing_record_save(request: HttpRequest, appointment_id: int) -> HttpResponse:
    appointment = get_object_or_404(Appointment, pk=appointment_id)

    if request.user.department and appointment.department != request.user.department:
        messages.error(request, '无法操作非本科室患者')
        return redirect('nurse_workbench')

    form = NursingRecordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        record = form.save(commit=False)
        record.appointment = appointment
        record.patient = appointment.patient
        record.nurse = request.user
        record.save()
        messages.success(request, '护理记录已保存')
        return redirect(f'/medical/nurse/workbench/?appointment_id={appointment_id}')
    return redirect('nurse_workbench')


@login_required
@nurse_required
def nursing_record_execute(request: HttpRequest, record_id: int) -> HttpResponse:
    record = get_object_or_404(NursingRecord, pk=record_id, nurse=request.user)
    record.execution_status = 'executed'
    record.executed_at = timezone.now()
    record.save(update_fields=['execution_status', 'executed_at'])
    messages.success(request, '医嘱已标记为已执行')
    return redirect(f'/medical/nurse/workbench/?appointment_id={record.appointment_id}')


@login_required
def medicine_search_api(request: HttpRequest) -> JsonResponse:
    q = request.GET.get('q', '')
    medicines = Medicine.objects.filter(is_active=True, stock_quantity__gt=0)
    if q:
        medicines = medicines.filter(
            Q(name__icontains=q) | Q(pinyin_code__icontains=q)
        )
    data = [{
        'id': m.id,
        'name': m.name,
        'specification': m.specification,
        'unit_price': str(m.unit_price),
        'stock_quantity': m.stock_quantity,
        'manufacturer': m.manufacturer,
    } for m in medicines[:20]]
    return JsonResponse({'medicines': data})
