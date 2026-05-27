from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.utils import timezone
import uuid

# Create your models here.


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("teacher", "Teacher"),
        ("admin", "Admin"),
    ]

    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    is_authorized = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        Group,
        blank=True,
        help_text="The groups this user belongs to.",
        related_name="home_auth_custom_users",
        related_query_name="home_auth_custom_user",
        verbose_name="groups",
    )
    user_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        help_text="Specific permissions for this user.",
        related_name="home_auth_custom_users",
        related_query_name="home_auth_custom_user",
        verbose_name="user permissions",
    )

    def __str__(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        self.is_student = self.role == "student"
        self.is_teacher = self.role == "teacher"
        self.is_admin = self.role == "admin"
        super().save(*args, **kwargs)


class LoginActivity(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    login_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Login activities"
        ordering = ["-login_time"]

    def __str__(self):
        return f"{self.user.username} logged in at {self.login_time}"


class PasswordResetRequest(models.Model):
    VALIDITY_PERIOD = timezone.timedelta(hours=1)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    @property
    def is_expired(self):
        return timezone.now() >= self.expires_at

    @property
    def is_usable(self):
        return self.used_at is None and not self.is_expired

    def mark_used(self):
        self.used_at = timezone.now()
        self.save(update_fields=["used_at"])

    def __str__(self):
        return f"Password reset for {self.user.username}"
