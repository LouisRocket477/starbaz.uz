"""
Слой сервисов верхнего уровня для `market`.

- orders  — цены и заказы (ListingPriceService)
- sellers — статусы продавцов и онлайн (SellerStatusService, is_user_online)
- site    — настройки сайта и контекст для ошибок
- formatting — форматирование цен (formatting.py)
"""

from .formatting import format_price_display, format_price_for_input
from .orders import ListingPriceService, PriceValidationResult
from .sellers import SellerStatusService, is_user_online
from .site import get_site_settings, get_template_context_for_errors

__all__ = [
    "ListingPriceService",
    "PriceValidationResult",
    "SellerStatusService",
    "format_price_display",
    "format_price_for_input",
    "get_site_settings",
    "get_template_context_for_errors",
    "is_user_online",
]

