from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse

from apps.accounts.decorators import admin_required
from apps.departments.models import Department
from apps.departments.forms import DepartmentForm


@login_required
def department_list(request: HttpRequest) -> HttpResponse:
    departments = Department.objects.all()
    return render(request, 'departments/department_list.html', {'departments': departments})


@login_required
@admin_required
def department_create(request: HttpRequest) -> HttpResponse:
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '科室创建成功')
        return redirect('department_list')
    return render(request, 'departments/department_form.html', {'form': form, 'action': '创建'})


@login_required
@admin_required
def department_edit(request: HttpRequest, pk: int) -> HttpResponse:
    dept = get_object_or_404(Department, pk=pk)
    form = DepartmentForm(request.POST or None, instance=dept)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '科室信息更新成功')
        return redirect('department_list')
    return render(request, 'departments/department_form.html', {'form': form, 'action': '编辑'})


@login_required
@admin_required
def department_delete(request: HttpRequest, pk: int) -> HttpResponse:
    dept = get_object_or_404(Department, pk=pk)
    if dept.users.exists():
        messages.error(request, f'科室「{dept.name}」下仍有用户，无法删除')
        return redirect('department_list')
    dept.delete()
    messages.success(request, f'科室「{dept.name}」已删除')
    return redirect('department_list')
