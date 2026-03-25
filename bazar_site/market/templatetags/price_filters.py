from decimal import Decimal

from django import template
from django.utils import timezone

register = template.Library()


def _time_ago_ru(dt) -> str:
    """Форматирует datetime как «X дней/месяцев/часов назад» на русском."""
    if dt is None:
        return ""
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 60:
        return "только что"
    elif seconds < 3600:
        m = int(seconds / 60)
        return f"{m} мин. назад" if m == 1 else f"{m} мин. назад"
    elif seconds < 86400:
        h = int(seconds / 3600)
        if h == 1:
            return "1 час назад"
        elif 2 <= h <= 4:
            return f"{h} часа назад"
        else:
            return f"{h} часов назад"
    elif seconds < 2592000:  # ~30 days
        d = int(seconds / 86400)
        if d == 1:
            return "1 день назад"
        elif 2 <= d <= 4:
            return f"{d} дня назад"
        else:
            return f"{d} дней назад"
    elif seconds < 31536000:  # ~365 days
        mo = int(seconds / 2592000)
        if mo == 1:
            return "1 месяц назад"
        elif 2 <= mo <= 4:
            return f"{mo} месяца назад"
        else:
            return f"{mo} месяцев назад"
    else:
        y = int(seconds / 31536000)
        if y == 1:
            return "1 год назад"
        elif 2 <= y <= 4:
            return f"{y} года назад"
        else:
            return f"{y} лет назад"


def _member_since_ru(dt) -> str:
    """Форматирует datetime как «X месяцев/лет» — участник с ..."""
    if dt is None:
        return ""
    now = timezone.now()
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt)
    diff = now - dt
    seconds = diff.total_seconds()
    if seconds < 2592000:  # ~30 days
        d = int(seconds / 86400)
        if d == 0:
            return "менее дня"
        elif d == 1:
            return "1 день"
        elif 2 <= d <= 4:
            return f"{d} дня"
        else:
            return f"{d} дней"
    elif seconds < 31536000:
        mo = int(seconds / 2592000)
        if mo == 1:
            return "1 месяц"
        elif 2 <= mo <= 4:
            return f"{mo} месяца"
        else:
            return f"{mo} месяцев"
    else:
        y = int(seconds / 31536000)
        if y == 1:
            return "1 год"
        elif 2 <= y <= 4:
            return f"{y} года"
        else:
            return f"{y} лет"


@register.filter
def time_ago_ru(value):
    """Время назад: «22 дня назад», «1 месяц назад»."""
    if value is None:
        return ""
    return _time_ago_ru(value)


@register.filter
def member_since(value):
    """Участник в течение: «11 месяцев», «2 года»."""
    if value is None:
        return ""
    return _member_since_ru(value)


def _ru_plural(n: int, one: str, few: str, many: str) -> str:
    """Русская плюрализация: 1 — one, 2-4 — few, 0,5-20 — many."""
    n = abs(int(n)) % 100
    if 11 <= n <= 19:
        return many
    if n % 10 == 1:
        return one
    if 2 <= n % 10 <= 4:
        return few
    return many


@register.filter
def ru_plural_reviews(value):
    """Отзыв/отзыва/отзывов."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "отзывов"
    return _ru_plural(n, "отзыв", "отзыва", "отзывов")


@register.filter
def ru_plural_deals(value):
    """Сделка/сделки/сделок."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "сделок"
    return _ru_plural(n, "сделка", "сделки", "сделок")


@register.filter
def ru_plural_views(value):
    """Просмотр/просмотра/просмотров."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "просмотров"
    return _ru_plural(n, "просмотр", "просмотра", "просмотров")


@register.filter
def ru_plural_listings(value):
    """Объявление/объявления/объявлений."""
    try:
        n = int(value)
    except (TypeError, ValueError):
        return "объявлений"
    return _ru_plural(n, "объявление", "объявления", "объявлений")


@register.filter
def split_by_comma(value):
    """Разбивает строку по запятым, убирает пробелы."""
    if not value:
        return []
    return [s.strip() for s in str(value).split(",") if s.strip()]


@register.filter
def compact_k(value):
    """
    Форматирование числа в игровой валюте:
    - тысячи  -> k   (1 000 -> 1k)
    - миллионы -> M  (1 000 000 -> 1M)
    - миллиарды -> Bn (1 000 000 000 -> 1Bn)
    """
    if value is None:
        return ""

    try:
        num = Decimal(value)
    except Exception:
        return value

    negative = num < 0
    num = abs(num)

    thousand = Decimal(1000)
    million = thousand * thousand  # 1 000 000
    billion = million * thousand   # 1 000 000 000

    suffix = ""
    divisor = Decimal(1)

    if num >= billion:
        divisor = billion
        suffix = "Bn"
    elif num >= million:
        divisor = million
        suffix = "M"
    elif num >= thousand:
        divisor = thousand
        suffix = "k"

    if divisor == 1:
        s = f"{num.normalize():f}".rstrip("0").rstrip(".")
        return f"-{s}" if negative else s

    value_short = num / divisor
    num_str = f"{value_short:.2f}".rstrip("0").rstrip(".")

    if negative:
        return f"-{num_str}{suffix}"
    return f"{num_str}{suffix}"

