"""
Форма входа в Django Admin с ограничением по белому списку.
"""

from __future__ import annotations

from django.contrib.admin.forms import AdminAuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class RecaptchaAdminAuthenticationForm(AdminAuthenticationForm):
    def clean(self):
        return super().clean()

    def confirm_login_allowed(self, user):
        """
        Ограничиваем вход в /admin/login/ белым списком.
        """
        super().confirm_login_allowed(user)

        from market.admin_access import user_can_access_admin

        if not user_can_access_admin(user):
            raise ValidationError(
                _(
                    "Доступ к админке разрешён только пользователям из белого списка."
                ),
                code="admin_whitelist_failed",
            )
