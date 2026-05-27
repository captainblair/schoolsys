from django.core.exceptions import ObjectDoesNotExist

from .models import Notification


def _profile_for_user(user):
    try:
        student = getattr(user, "student_profile", None)
    except ObjectDoesNotExist:
        student = None
    if student is not None:
        return student
    try:
        return getattr(user, "teacher_profile", None)
    except ObjectDoesNotExist:
        return None


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
    profile = _profile_for_user(request.user)
    profile_image = ""
    if profile is not None:
        image = getattr(profile, "student_image", None) or getattr(profile, "teacher_image", None)
        if image:
            profile_image = image.url
    display_name = request.user.get_full_name() or request.user.email or request.user.username
    return {
        "unread_notifications_count": queryset.filter(is_read=False).count(),
        "recent_notifications": queryset[:5],
        "current_user_is_admin": request.user.is_staff
        or request.user.is_superuser
        or getattr(request.user, "is_admin", False)
        or "admin" in groups,
        "current_user_is_teacher": getattr(request.user, "is_teacher", False) or "teacher" in groups,
        "current_user_is_student": getattr(request.user, "is_student", False) or "student" in groups,
        "current_user_profile_image": profile_image,
        "current_user_display_name": display_name,
    }
