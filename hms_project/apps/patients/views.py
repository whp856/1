from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse

from apps.accounts.decorators import admin_required
from apps.patients.models import Patient
from apps.patients.forms import PatientForm


@login_required
def patient_list(request: HttpRequest) -> HttpResponse:
    patients = Patient.objects.all()
    search = request.GET.get('search', '')
    if search:
        patients = patients.filter(
            Q(name__icontains=search) | Q(id_card__icontains=search) | Q(phone__icontains=search)
        )
    return render(request, 'patients/patient_list.html', {
        'patients': patients,
        'search': search,
    })


@login_required
def patient_detail(request: HttpRequest, pk: int) -> HttpResponse:
    patient = get_object_or_404(Patient, pk=pk)
    appointments = patient.appointments.select_related('doctor', 'department').order_by('-appointment_date')[:20]
    records = patient.medical_records.select_related('doctor').order_by('-created_at')[:10]
    return render(request, 'patients/patient_detail.html', {
        'patient': patient,
        'appointments': appointments,
        'records': records,
    })


@login_required
def patient_create(request: HttpRequest) -> HttpResponse:
    form = PatientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        patient = form.save()
        messages.success(request, f'患者 {patient.name} 建档成功')
        return redirect('patient_list')
    return render(request, 'patients/patient_form.html', {'form': form, 'action': '新建档案'})


@login_required
@admin_required
def patient_edit(request: HttpRequest, pk: int) -> HttpResponse:
    patient = get_object_or_404(Patient, pk=pk)
    form = PatientForm(request.POST or None, instance=patient)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '患者信息更新成功')
        return redirect('patient_detail', pk=patient.pk)
    return render(request, 'patients/patient_form.html', {'form': form, 'action': '编辑档案'})


@login_required
def patient_search_api(request: HttpRequest) -> JsonResponse:
    q = request.GET.get('q', '')
    if len(q) < 2:
        return JsonResponse({'patients': []})
    patients = Patient.objects.filter(
        Q(name__icontains=q) | Q(id_card__icontains=q) | Q(phone__icontains=q)
    )[:10]
    data = [{
        'id': p.id,
        'name': p.name,
        'id_card': p.id_card,
        'gender': p.get_gender_display(),
        'age': p.age,
        'phone': p.phone,
    } for p in patients]
    return JsonResponse({'patients': data})
