"""
Ключи Google reCAPTCHA для входа в /admin/.

Приоритет: запись в БД (раздел админки «Ключи reCAPTCHA»), иначе переменные
из settings (окружение / .env).
"""

from __future__ import annotations

from django.conf import settings


def get_admin_recaptcha_public_key() -> str:
    try:
        from .models import RecaptchaAdminKeys

        row = RecaptchaAdminKeys.objects.only("public_key").first()
        if row is not None and (row.public_key or "").strip():
            return (row.public_key or "").strip()
    except Exception:
        pass
    return (getattr(settings, "RECAPTCHA_PUBLIC_KEY", None) or "").strip()


def get_admin_recaptcha_secret_key() -> str:
    try:
        from .models import RecaptchaAdminKeys

        row = RecaptchaAdminKeys.objects.only("secret_key").first()
        if row is not None and (row.secret_key or "").strip():
            return (row.secret_key or "").strip()
    except Exception:
        pass
    return (getattr(settings, "RECAPTCHA_SECRET_KEY", None) or "").strip()
