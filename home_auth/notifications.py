from django.contrib.auth import get_user_model

from .models import Notification


def create_notification(user, title, message, link=""):
    if user is None or not getattr(user, "is_authenticated", False):
        return None

    return Notification.objects.create(
        user=user,
        title=title,
        message=message,
        link=link,
    )


def notify_admins(title, message, link="", exclude_user=None):
    User = get_user_model()
    admins = User.objects.filter(is_staff=True) | User.objects.filter(is_superuser=True)

    for user in admins.distinct():
        if exclude_user is not None and user.pk == getattr(exclude_user, "pk", None):
            continue
        create_notification(user, title, message, link)
