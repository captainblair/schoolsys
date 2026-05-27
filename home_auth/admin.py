from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import CustomUser, LoginActivity, PasswordResetRequest

# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "is_authorized",
        "is_student",
        "is_teacher",
        "is_admin",
        "date_joined",
    )
    list_filter = (
        "is_authorized",
        "role",
        "is_student",
        "is_teacher",
        "is_admin",
        "is_staff",
        "is_superuser",
        "is_active",
    )
    fieldsets = UserAdmin.fieldsets + (
        ("School roles", {"fields": ("role", "is_authorized", "is_student", "is_teacher", "is_admin")}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("School roles", {"fields": ("email", "role", "is_authorized", "is_student", "is_teacher", "is_admin")}),
    )


@admin.register(LoginActivity)
class LoginActivityAdmin(admin.ModelAdmin):
    list_display = ("user", "login_time")
    search_fields = ("user__username", "user__email")
    list_filter = ("login_time",)


@admin.register(PasswordResetRequest)
class PasswordResetRequestAdmin(admin.ModelAdmin):
    list_display = ("user", "created_at", "expires_at", "used_at")
    search_fields = ("user__username", "user__email", "token")
    list_filter = ("created_at", "expires_at", "used_at")
    readonly_fields = ("token", "created_at")
