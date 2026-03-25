"""Сервисы настроек сайта и общего контекста для шаблонов."""

from .services import get_site_settings, get_template_context_for_errors

__all__ = ["get_site_settings", "get_template_context_for_errors"]
