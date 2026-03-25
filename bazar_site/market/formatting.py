"""
Форматирование чисел для отображения и для полей ввода.

Без зависимостей от моделей и вьюх — только Decimal, чтобы избежать циклических импортов.
"""

from decimal import Decimal
from typing import Optional


def format_price_display(value: Optional[Decimal]) -> str:
    """
    Цена для отображения в шаблонах: пробел как разделитель тысяч, без .00.
    Пример: 123456.99 -> "123 456.99", 500000 -> "500 000".
    """
    if value is None:
        return ""
    try:
        num = Decimal(value)
    except Exception:
        return str(value)
    s = f"{num:,.2f}".replace(",", " ")
    if s.endswith(".00"):
        s = s[:-3]
    return s


def format_price_for_input(value: Optional[Decimal]) -> Optional[str]:
    """
    Цена для подстановки в поле ввода формы: запятая как разделитель тысяч, без .00.
    Пример: 123456.99 -> "123,456.99", 500000 -> "500,000".
    """
    if value is None:
        return None
    try:
        num = Decimal(value)
    except Exception:
        return str(value)
    s = f"{num:,.2f}"
    if s.endswith(".00"):
        s = s[:-3]
    return s
