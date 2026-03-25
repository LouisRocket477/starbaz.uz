"""
Общие хелперы для вьюх: реэкспорт из services для обратной совместимости.
"""

from ..models import UserProfile
from ..services import (
    SellerStatusService,
    get_site_settings,
    get_template_context_for_errors,
    is_user_online,
)

__all__ = [
    "get_site_settings",
    "get_seller_status",
    "get_seller_status_for_profile",
    "is_user_online",
    "_get_site_settings_context",
]


def get_seller_status_for_profile(
    profile: UserProfile | None, avg_rating_rounded: int, orders_count: int
) -> tuple[str | None, str]:
    """Тонкая обёртка над SellerStatusService для обратной совместимости."""
    return SellerStatusService.for_profile(
        profile=profile,
        avg_rating_rounded=avg_rating_rounded,
        orders_count=orders_count,
    )


def get_seller_status(avg_rating_rounded: int, orders_count: int) -> tuple[str | None, str]:
    """Старый хелпер для обратной совместимости (без профиля)."""
    return SellerStatusService.for_stats(avg_rating_rounded, orders_count)


def _get_site_settings_context() -> dict:
    """Контекст для шаблонов ошибок (алиас для get_template_context_for_errors)."""
    return get_template_context_for_errors()
