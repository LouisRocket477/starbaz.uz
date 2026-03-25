"""Настройки сайта и контекст для страниц ошибок."""

from ..models import SiteSettings


def get_site_settings() -> SiteSettings:
    """Возвращает единственный объект настроек сайта (создаёт при необходимости)."""
    settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)
    return settings_obj


def get_template_context_for_errors() -> dict:
    """Базовый контекст для шаблонов 400, 403, 404, 500."""
    settings_obj = get_site_settings()
    return {
        "site_settings": settings_obj,
        "page_title": settings_obj.seo_meta_title or settings_obj.name,
    }
