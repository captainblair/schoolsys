from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, send_mail
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import LoginActivity, Notification, PasswordResetRequest
from .notifications import create_notification

# Create your views here.

User = get_user_model()
ROLE_CHOICES = ["student", "teacher", "admin"]
PUBLIC_ROLE_CHOICES = ["student", "teacher"]


def _build_absolute_url(request, view_name, *args):
    return request.build_absolute_uri(reverse(view_name, args=args))


def _apply_role(user, role):
    if hasattr(user, "role"):
        user.role = role
    if hasattr(user, "is_student"):
        user.is_student = role == "student"
    if hasattr(user, "is_teacher"):
        user.is_teacher = role == "teacher"
    if hasattr(user, "is_admin"):
        user.is_admin = role == "admin"
    group, _ = Group.objects.get_or_create(name=role)
    user.groups.remove(*Group.objects.filter(name__in=ROLE_CHOICES))
    user.groups.add(group)
    return user


def _dashboard_for_user(user):
    group_names = set(user.groups.values_list("name", flat=True))

    if getattr(user, "is_admin", False) or user.is_staff or user.is_superuser or "admin" in group_names:
        return "index"
    if getattr(user, "is_teacher", False) or "teacher" in group_names:
        return "teacher-dashboard"
    if getattr(user, "is_student", False) or "student" in group_names:
        return "student-dashboard"
    return None


def _is_admin(user):
    if not user.is_authenticated:
        return False
    group_names = set(user.groups.values_list("name", flat=True))
    return getattr(user, "is_admin", False) or user.is_staff or user.is_superuser or "admin" in group_names


def _role_for_user(user):
    if getattr(user, "is_admin", False) or user.is_staff or user.is_superuser or user.groups.filter(name="admin").exists():
        return "admin"
    if getattr(user, "is_teacher", False) or user.groups.filter(name="teacher").exists():
        return "teacher"
    return "student"


def _require_admin(request):
    if not request.user.is_authenticated:
        return redirect("login")
    if not _is_admin(request.user):
        return HttpResponseForbidden("Only administrators can access this page.")
    return None


def _next_step_for_user(user):
    dashboard = _dashboard_for_user(user)
    if dashboard == "student-dashboard" and not hasattr(user, "student_profile"):
        return "complete_student_profile"
    if dashboard == "teacher-dashboard" and not hasattr(user, "teacher_profile"):
        return "complete_teacher_profile"
    return dashboard


def login_view(request):
    if request.user.is_authenticated and request.method == "POST":
        dashboard = _dashboard_for_user(request.user)
        if dashboard is not None:
            return redirect(dashboard)
        logout(request)
        messages.error(request, "Invalid user role")
        return render(request, "Home/login.html")

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password")
        matched_user = User.objects.filter(email__iexact=email).first()
        user = None

        if matched_user is not None:
            user = authenticate(request, username=matched_user.get_username(), password=password)

        if user is not None:
            next_step = _next_step_for_user(user)
            if next_step is None:
                messages.error(request, "Invalid user role")
                return render(request, "Home/login.html")

            login(request, user)
            LoginActivity.objects.create(user=user)
            messages.success(request, "Logged in successfully")
            return redirect(next_step)

        messages.error(request, "Invalid email or password")

    return render(request, "Home/login.html")


def register_view(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        role = request.POST.get("role", "student").strip().lower()
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if not first_name or not last_name or not email or not password or role not in PUBLIC_ROLE_CHOICES:
            messages.error(request, "Please fill in all required fields")
            return render(request, "Home/register.html")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "Home/register.html")

        username = email
        if User.objects.filter(username__iexact=username).exists() or User.objects.filter(email__iexact=email).exists():
            messages.error(request, "An account with this email already exists")
            return render(request, "Home/register.html")

        try:
            validate_password(password)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return render(request, "Home/register.html")

        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
        )
        _apply_role(user, role)
        update_fields = ["first_name", "last_name"]
        if hasattr(user, "role"):
            update_fields.append("role")
        if hasattr(user, "is_student"):
            update_fields.append("is_student")
        if hasattr(user, "is_teacher"):
            update_fields.append("is_teacher")
        if hasattr(user, "is_admin"):
            update_fields.append("is_admin")
        user.save(update_fields=update_fields)
        create_notification(user, "Account created", "Your account was created successfully.")
        login(request, user, backend="django.contrib.auth.backends.ModelBackend")
        messages.success(request, "Account created successfully. Please complete your profile.")
        return redirect(_next_step_for_user(user) or "index")

    return render(request, "Home/register.html")


@login_required
def user_role_list_view(request):
    denied = _require_admin(request)
    if denied:
        return denied

    users = [
        {
            "account": account,
            "role": _role_for_user(account),
        }
        for account in User.objects.order_by("first_name", "last_name", "email", "username")
    ]
    return render(request, "Home/user-roles.html", {"users": users})


@login_required
def update_user_role_view(request, id):
    denied = _require_admin(request)
    if denied:
        return denied

    if request.method != "POST":
        return HttpResponseForbidden("User roles can only be changed with a POST request.")

    target_user = get_object_or_404(User, id=id)
    role = request.POST.get("role", "").strip().lower()

    if role not in ROLE_CHOICES:
        messages.error(request, "Invalid role selected.")
        return redirect("user_roles")

    if target_user == request.user and role != "admin":
        messages.error(request, "You cannot remove your own admin access.")
        return redirect("user_roles")
    if target_user.is_superuser and role != "admin":
        messages.error(request, "Superuser accounts must be changed from Django admin.")
        return redirect("user_roles")

    _apply_role(target_user, role)
    update_fields = []
    if hasattr(target_user, "role"):
        update_fields.append("role")
    if hasattr(target_user, "is_student"):
        update_fields.append("is_student")
    if hasattr(target_user, "is_teacher"):
        update_fields.append("is_teacher")
    if hasattr(target_user, "is_admin"):
        update_fields.append("is_admin")
    if role != "admin" and target_user.is_staff:
        target_user.is_staff = False
        update_fields.append("is_staff")
    if update_fields:
        target_user.save(update_fields=update_fields)

    create_notification(
        target_user,
        "Role updated",
        f"Your account role is now {role.title()}.",
        reverse(_dashboard_for_user(target_user) or "index"),
    )
    messages.success(request, f"{target_user} is now {role.title()}. Profile approval is handled from Pending Approvals.")
    return redirect("user_roles")


def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        user = User.objects.filter(email__iexact=email).first()

        if user is not None:
            reset_request = PasswordResetRequest.objects.create(
                user=user,
                expires_at=timezone.now() + PasswordResetRequest.VALIDITY_PERIOD,
            )
            reset_url = _build_absolute_url(request, "reset_password", reset_request.token)

            if not getattr(settings, "EMAIL_HOST", ""):
                messages.error(request, "Email is not configured. Please set EMAIL_HOST, EMAIL_HOST_USER, and EMAIL_HOST_PASSWORD.")
                return render(request, "Home/forgot-password.html")
            if settings.EMAIL_HOST_USER == "your_email@gmail.com" or settings.EMAIL_HOST_PASSWORD == "your_gmail_app_password":
                messages.error(request, "Email credentials are still placeholders. Update HOME/.env with your real email and app password.")
                return render(request, "Home/forgot-password.html")

            try:
                send_mail(
                    "Reset your Preskool password",
                    (
                        f"Hello {user.first_name or user.email},\n\n"
                        f"Use this link to reset your password:\n{reset_url}\n\n"
                        "This link expires in 1 hour.\n\n"
                        "If you did not request this, you can ignore this email."
                    ),
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
            except BadHeaderError:
                messages.error(request, "Invalid email header detected.")
                return render(request, "Home/forgot-password.html")
            except Exception as error:
                messages.error(request, f"Could not send reset email: {error}")
                return render(request, "Home/forgot-password.html")

        messages.success(request, "If an account exists for that email, a reset link has been created.")

    return render(request, "Home/forgot-password.html")


def reset_password_view(request, token):
    reset_request = PasswordResetRequest.objects.filter(token=token).select_related("user").first()

    if reset_request is None or not reset_request.is_usable:
        return render(request, "Home/reset-password.html", {"valid_link": False}, status=400)

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return render(request, "Home/reset-password.html", {"valid_link": True})

        try:
            validate_password(password, reset_request.user)
        except ValidationError as error:
            for message in error.messages:
                messages.error(request, message)
            return render(request, "Home/reset-password.html", {"valid_link": True})

        reset_request.user.set_password(password)
        reset_request.user.save(update_fields=["password"])
        reset_request.mark_used()
        messages.success(request, "Password reset successfully. You can now log in.")
        return redirect("login")

    return render(request, "Home/reset-password.html", {"valid_link": True})


def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully")
    return redirect("login")


@login_required
def notification_list_view(request):
    notifications = Notification.objects.filter(user=request.user)
    return render(request, "Home/notifications.html", {"notifications": notifications})


@login_required
def mark_notification_read_view(request, id):
    notification = get_object_or_404(Notification, id=id, user=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])

    if notification.link:
        return redirect(notification.link)
    return redirect("notifications")


@login_required
def mark_all_notifications_read_view(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect("notifications")


def error_404_view(request, exception=None):
    return render(request, "Home/error-404.html", status=404)
