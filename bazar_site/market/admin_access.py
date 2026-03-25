from __future__ import annotations

from django.contrib.auth.models import AbstractBaseUser


def user_can_access_admin(user: AbstractBaseUser | None) -> bool:
    """
    Доступ к Django Admin разрешён только:
    - superuser
    - staff пользователям, у которых в профиле включён флаг `is_admin_whitelist`.
    """
    if user is None:
        return False

    if not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    if not getattr(user, "is_staff", False):
        return False

    try:
        profile = getattr(user, "profile", None)
        if not profile:
            return False
        return bool(
            getattr(profile, "is_admin_whitelist", False)
            or getattr(profile, "is_project_admin", False)
            or getattr(profile, "is_operator", False)
        )
    except Exception:
        return False

