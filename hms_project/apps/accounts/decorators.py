from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from typing import Callable


def role_required(*roles: str) -> Callable:
    def decorator(view_func: Callable) -> Callable:
        @wraps(view_func)
        def wrapper(request: HttpRequest, *args, **kwargs) -> HttpResponse:
            if not request.user.is_authenticated:
                return redirect('login')
            if request.user.role not in roles:
                messages.error(request, '您没有权限执行此操作')
                return redirect('dashboard')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


def admin_required(view_func: Callable) -> Callable:
    return role_required('admin')(view_func)


def doctor_required(view_func: Callable) -> Callable:
    return role_required('doctor', 'admin')(view_func)


def nurse_required(view_func: Callable) -> Callable:
    return role_required('nurse', 'admin')(view_func)


def pharmacist_required(view_func: Callable) -> Callable:
    return role_required('pharmacist', 'admin')(view_func)
