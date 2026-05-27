from .models import Notification


def notifications(request):
    if not request.user.is_authenticated:
        return {
            "unread_notifications_count": 0,
            "recent_notifications": [],
            "current_user_is_admin": False,
            "current_user_is_teacher": False,
            "current_user_is_student": False,
        }

    queryset = Notification.objects.filter(user=request.user)
    groups = set(request.user.groups.values_list("name", flat=True))
    return {
        "unread_notifications_count": queryset.filter(is_read=False).count(),
        "recent_notifications": queryset[:5],
        "current_user_is_admin": request.user.is_staff
        or request.user.is_superuser
        or getattr(request.user, "is_admin", False)
        or "admin" in groups,
        "current_user_is_teacher": getattr(request.user, "is_teacher", False) or "teacher" in groups,
        "current_user_is_student": getattr(request.user, "is_student", False) or "student" in groups,
    }
