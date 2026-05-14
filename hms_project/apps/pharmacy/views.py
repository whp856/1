from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.db import transaction
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils import timezone
from datetime import date, timedelta

from apps.accounts.decorators import admin_required, pharmacist_required
from apps.pharmacy.models import Medicine, StockIn, StockOut, StockCheck
from apps.pharmacy.forms import MedicineForm, StockInForm, StockCheckForm
from apps.medical.models import Prescription


@login_required
def medicine_list(request: HttpRequest) -> HttpResponse:
    medicines = Medicine.objects.all()
    search = request.GET.get('search', '')
    category = request.GET.get('category', '')
    stock_alert = request.GET.get('stock_alert', '')

    if search:
        medicines = medicines.filter(
            Q(name__icontains=search) | Q(pinyin_code__icontains=search)
        )
    if category:
        medicines = medicines.filter(category=category)
    if stock_alert == 'low':
        medicines = medicines.filter(stock_quantity__lte=F('warning_stock'))
    elif stock_alert == 'expiring':
        medicines = medicines.filter(expiry_date__lte=date.today() + timedelta(days=30))

    return render(request, 'pharmacy/medicine_list.html', {
        'medicines': medicines,
        'search': search,
        'category': category,
        'stock_alert': stock_alert,
        'categories': Medicine.Category.choices,
    })


@login_required
@pharmacist_required
def medicine_create(request: HttpRequest) -> HttpResponse:
    form = MedicineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        medicine = form.save(commit=False)
        name = medicine.name
        try:
            from pypinyin import lazy_pinyin
            medicine.pinyin_code = ''.join([w[0].upper() for w in lazy_pinyin(name)])
        except ImportError:
            medicine.pinyin_code = name[:10].upper()
        medicine.save()
        messages.success(request, f'药品「{medicine.name}」添加成功')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'action': '添加药品'})


@login_required
@pharmacist_required
def medicine_edit(request: HttpRequest, pk: int) -> HttpResponse:
    medicine = get_object_or_404(Medicine, pk=pk)
    form = MedicineForm(request.POST or None, instance=medicine)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '药品信息更新成功')
        return redirect('medicine_list')
    return render(request, 'pharmacy/medicine_form.html', {'form': form, 'action': '编辑药品'})


@login_required
@pharmacist_required
def stock_in(request: HttpRequest) -> HttpResponse:
    form = StockInForm(request.POST or None, initial={'operator': request.user})
    if request.method == 'POST':
        form = StockInForm(request.POST or None)
        if form.is_valid():
            stock_in = form.save(commit=False)
            stock_in.operator = request.user
            stock_in.save()
            messages.success(request, f'{stock_in.medicine.name} 入库 x{stock_in.quantity} 成功')
            return redirect('stock_in_list')
    return render(request, 'pharmacy/stock_in.html', {'form': form})


@login_required
def stock_in_list(request: HttpRequest) -> HttpResponse:
    records = StockIn.objects.select_related('medicine', 'operator').all()
    search = request.GET.get('search', '')
    if search:
        records = records.filter(medicine__name__icontains=search)
    return render(request, 'pharmacy/stock_in_list.html', {
        'records': records,
        'search': search,
    })


@login_required
def stock_out_list(request: HttpRequest) -> HttpResponse:
    records = StockOut.objects.select_related('medicine', 'operator', 'prescription').all()
    search = request.GET.get('search', '')
    if search:
        records = records.filter(medicine__name__icontains=search)
    return render(request, 'pharmacy/stock_out_list.html', {
        'records': records,
        'search': search,
    })


@login_required
@pharmacist_required
def stock_check(request: HttpRequest) -> HttpResponse:
    if request.method == 'POST':
        form = StockCheckForm(request.POST)
        if form.is_valid():
            check = form.save(commit=False)
            medicine = check.medicine
            check.system_quantity = medicine.stock_quantity
            check.operator = request.user
            check.save()
            if check.difference != 0:
                messages.warning(
                    request,
                    f'{medicine.name} 盘点差异: {check.difference} (系统:{check.system_quantity}, 实际:{check.actual_quantity})',
                )
            else:
                messages.success(request, f'{medicine.name} 盘点结果一致')
            return redirect('stock_check_list')
    else:
        form = StockCheckForm()
    return render(request, 'pharmacy/stock_check.html', {'form': form})


@login_required
def stock_check_list(request: HttpRequest) -> HttpResponse:
    checks = StockCheck.objects.select_related('medicine', 'operator').all()
    return render(request, 'pharmacy/stock_check_list.html', {'checks': checks})


@login_required
@pharmacist_required
def dispense_workbench(request: HttpRequest) -> HttpResponse:
    paid_prescriptions = Prescription.objects.filter(
        status='paid'
    ).select_related('patient', 'doctor').order_by('payment_time')

    prescription_id = request.GET.get('prescription_id')
    current_prescription = None
    items = None

    if prescription_id:
        current_prescription = get_object_or_404(
            Prescription.objects.select_related('patient', 'doctor'),
            pk=prescription_id, status='paid',
        )
        items = current_prescription.items.select_related('medicine').all()

    return render(request, 'pharmacy/dispense.html', {
        'paid_prescriptions': paid_prescriptions,
        'current_prescription': current_prescription,
        'items': items,
    })


@login_required
@pharmacist_required
def dispense_confirm(request: HttpRequest, prescription_id: int) -> HttpResponse:
    prescription = get_object_or_404(Prescription, pk=prescription_id, status='paid')

    with transaction.atomic():
        for item in prescription.items.select_related('medicine').all():
            medicine = item.medicine
            if medicine.stock_quantity < item.quantity:
                messages.error(
                    request,
                    f'{medicine.name} 库存不足 (库存:{medicine.stock_quantity}, 需要:{item.quantity})',
                )
                return redirect(f'/pharmacy/dispense/?prescription_id={prescription_id}')

            medicine.stock_quantity -= item.quantity
            medicine.save(update_fields=['stock_quantity'])

            StockOut.objects.create(
                medicine=medicine,
                quantity=item.quantity,
                prescription=prescription,
                operator=request.user,
            )

        prescription.status = 'dispensed'
        prescription.dispense_time = timezone.now()
        prescription.pharmacist = request.user
        prescription.save()

    messages.success(request, f'处方 #{prescription.id} 发药完成')
    return redirect('dispense_workbench')


@login_required
@pharmacist_required
def prescription_payment(request: HttpRequest, prescription_id: int) -> HttpResponse:
    prescription = get_object_or_404(Prescription, pk=prescription_id)

    if prescription.status != 'pending':
        messages.error(request, f'处方状态为 {prescription.get_status_display()}，无法收款')
        return redirect('dispense_workbench')

    if not prescription.items.exists():
        messages.error(request, '处方为空，无法收款')
        return redirect('dispense_workbench')

    prescription.status = 'paid'
    prescription.payment_time = timezone.now()
    prescription.save(update_fields=['status', 'payment_time'])

    messages.success(request, f'处方 #{prescription.id} 收款成功，金额: ¥{prescription.total_amount}')
    return redirect('dispense_workbench')


@login_required
@pharmacist_required
def prescription_reject(request: HttpRequest, prescription_id: int) -> HttpResponse:
    prescription = get_object_or_404(Prescription, pk=prescription_id)

    if prescription.status not in ('pending', 'paid'):
        messages.error(request, f'处方状态为 {prescription.get_status_display()}，无法驳回')
        return redirect('dispense_workbench')

    note = request.POST.get('reject_note', '处方存在问题，请修改后重新提交')
    prescription.status = 'cancelled'
    prescription.note = f'[驳回原因] {note}'
    prescription.save(update_fields=['status', 'note'])

    messages.warning(request, f'处方 #{prescription.id} 已驳回')
    return redirect('dispense_workbench')
