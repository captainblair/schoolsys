from django.contrib import messages
from django.contrib.auth import logout
from django.shortcuts import redirect, render


# Create your views here.

def _group_names(user):
    if not user.is_authenticated:
        return set()
    return set(user.groups.values_list("name", flat=True))


def _is_admin(user):
    groups = _group_names(user)
    return (
        user.is_authenticated
        and (user.is_staff or user.is_superuser or getattr(user, "is_admin", False) or "admin" in groups)
    )


def _is_teacher(user):
    return user.is_authenticated and (getattr(user, "is_teacher", False) or "teacher" in _group_names(user))


def _is_student(user):
    return user.is_authenticated and (getattr(user, "is_student", False) or "student" in _group_names(user))


def index(request):
    if not request.user.is_authenticated:
        return redirect("login")

    if _is_admin(request.user):
        return render(request, "Home/index.html")
    if _is_teacher(request.user):
        return redirect("teacher-dashboard")
    if _is_student(request.user):
        return redirect("student-dashboard")

    logout(request)
    messages.error(request, "Invalid user role")
    return redirect("login")
