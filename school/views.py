from django.contrib import messages
from django.contrib.auth import logout
from django.db.models import Sum
from django.shortcuts import redirect, render

from student.models import Book, Department, Event, Exam, Expense, Fee, FeeCollection, Holiday, Student, Teacher, TimeTableEntry


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
        context = {
            "student_count": Student.objects.count(),
            "approved_student_count": Student.objects.filter(approval_status="approved").count(),
            "pending_student_count": Student.objects.filter(approval_status="pending").count(),
            "teacher_count": Teacher.objects.count(),
            "approved_teacher_count": Teacher.objects.filter(approval_status="approved").count(),
            "pending_teacher_count": Teacher.objects.filter(approval_status="pending").count(),
            "department_count": Department.objects.count(),
            "revenue_total": FeeCollection.objects.aggregate(total=Sum("amount_paid"))["total"] or 0,
            "expense_total": Expense.objects.aggregate(total=Sum("amount"))["total"] or 0,
            "fee_count": Fee.objects.count(),
            "holiday_count": Holiday.objects.count(),
            "exam_count": Exam.objects.count(),
            "event_count": Event.objects.count(),
            "timetable_count": TimeTableEntry.objects.count(),
            "book_count": Book.objects.count(),
            "recent_students": Student.objects.select_related("parent").order_by("-id")[:5],
            "recent_payments": FeeCollection.objects.select_related("student", "fee").order_by("-payment_date")[:5],
            "upcoming_exams": Exam.objects.order_by("exam_date", "start_time")[:5],
            "upcoming_events": Event.objects.order_by("start_date")[:5],
        }
        return render(request, "Home/index.html", context)
    if _is_teacher(request.user):
        return redirect("teacher-dashboard")
    if _is_student(request.user):
        return redirect("student-dashboard")

    logout(request)
    messages.error(request, "Invalid user role")
    return redirect("login")
