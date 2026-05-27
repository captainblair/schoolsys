from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.mail import BadHeaderError, send_mail
from django.conf import settings
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .models import LoginActivity, PasswordResetRequest

# Create your views here.

User = get_user_model()
ROLE_CHOICES = ["student", "teacher", "admin"]


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
            dashboard = _dashboard_for_user(user)
            if dashboard is None:
                messages.error(request, "Invalid user role")
                return render(request, "Home/login.html")

            login(request, user)
            LoginActivity.objects.create(user=user)
            messages.success(request, "Logged in successfully")
            return redirect(dashboard)

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

        if not first_name or not last_name or not email or not password or role not in ROLE_CHOICES:
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
        messages.success(request, "Account created successfully. You can now log in.")
        return redirect("login")

    return render(request, "Home/register.html")


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


def error_404_view(request, exception=None):
    return render(request, "Home/error-404.html", status=404)
