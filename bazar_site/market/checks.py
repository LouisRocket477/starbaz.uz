"""
Системные проверки конфигурации (django check framework).
"""

from __future__ import annotations

from django.conf import settings
from django.core.checks import Warning, register

from market.recaptcha_keys import get_admin_recaptcha_public_key, get_admin_recaptcha_secret_key


@register()
def recaptcha_admin_config_check(app_configs, **kwargs):
    """
    В продакшене без секретного ключа reCAPTCHA вход в админку не защищён.
    """
    if settings.DEBUG:
        return []
    secret = get_admin_recaptcha_secret_key()
    public = get_admin_recaptcha_public_key()
    hints = []
    if not secret:
        hints.append(
            Warning(
                "Секретный ключ reCAPTCHA не задан (ни в БД, ни в окружении): вход в /admin/ без Google reCAPTCHA.",
                hint=(
                    "Заполните «Ключи reCAPTCHA (вход в админку)» в админке Django "
                    "или задайте RECAPTCHA_SECRET_KEY / RECAPTCHA_PUBLIC_KEY в окружении."
                ),
                id="market.W001",
            )
        )
    if secret and not public:
        hints.append(
            Warning(
                "Секретный ключ reCAPTCHA задан, но публичный пуст — виджет на странице входа не отобразится.",
                hint="Укажите site key в «Ключи reCAPTCHA» или RECAPTCHA_PUBLIC_KEY в окружении.",
                id="market.W002",
            )
        )
    return hints
