"""Кастомные шаблонные теги и фильтры для market."""

import re
from decimal import Decimal, InvalidOperation
from urllib.parse import quote

from django import template

from market.formatting import format_price_display

register = template.Library()

RSI_CITIZENS_BASE = "https://robertsspaceindustries.com/en/citizens"


@register.filter
def rsi_citizen_url(nickname):
    """Возвращает URL профиля гражданина на RSI (Roberts Space Industries)."""
    if not nickname:
        return ""
    encoded = quote(str(nickname).strip(), safe="")
    return f"{RSI_CITIZENS_BASE}/{encoded}"


@register.filter
def parse_deal_message(content):
    """
    Парсит сообщение о завершённой сделке.
    Новый формат: ✅DEAL\\nbuyer_name\\nqty\\ntotal\\ncurrency\\nremaining
    Старый формат (для совместимости): ✅ Сделка завершена... с regex.
    Возвращает dict или None.
    """
    if not content:
        return None

    # Новый формат (допускаем пробел после эмодзи: "✅ DEAL" и "✅DEAL")
    if "✅DEAL" in content or "✅ DEAL" in content:
        lines = content.strip().split("\n")
        if len(lines) >= 6:
            first = lines[0].replace(" ", "")
            if first == "✅DEAL":
                try:
                    data = {
                        "buyer_name": lines[1],
                        "qty": lines[2],
                        "total": lines[3],
                        "currency": lines[4],
                        "remaining": lines[5],
                    }
                    # Дополнительные опциональные строки:
                    # 6: общая сумма доплаты
                    # 7: ник того, кто должен доплатить
                    if len(lines) >= 7:
                        data["diff_total"] = lines[6]
                    if len(lines) >= 8:
                        data["payer_name"] = lines[7]
                    return data
                except IndexError:
                    pass

    # Старый формат (совместимость)
    patterns = [
        # Многострочный
        re.compile(
            r"✅\s*Сделка завершена!?\n\n"
            r"Покупатель (\S+) приобрёл (\d+) шт\.\n"
            r"Сумма: ([0-9 .,]+) ([A-Za-z]+)\n"
            r"Осталось в объявлении:? (\d+) шт\.?",
            re.DOTALL,
        ),
        # Компактный: "приобрёл 2 шт. на сумму X AUEC. Осталось..."
        re.compile(
            r"Покупатель (\S+) приобрёл (\d+) шт\. (?:на сумму )?([0-9 .,]+) ([A-Za-z]+)\."
            r".*?Осталось в объявлении:? (\d+) шт",
            re.DOTALL,
        ),
    ]
    for pat in patterns:
        m = pat.search(content)
        if m:
            return {
                "buyer_name": m.group(1),
                "qty": m.group(2),
                "total": m.group(3).strip(),
                "currency": m.group(4),
                "remaining": m.group(5),
            }

    return None


@register.filter
def parse_purchase_message(content):
    """
    Парсит сообщение о заявке на покупку.
    Новый формат: 🛒PURCHASE\\nbuyer_name\\nqty\\nunit_price\\ntotal\\ncurrency
    Старый формат (совместимость): regex.
    """
    if not content:
        return None

    # Новый формат (также допускаем пробел: "🛒 PURCHASE")
    if "🛒PURCHASE" in content or "🛒 PURCHASE" in content:
        lines = content.strip().split("\n")
        if len(lines) >= 6:
            first = lines[0].replace(" ", "")
            if first == "🛒PURCHASE":
                try:
                    return {
                        "buyer_name": lines[1],
                        "qty": lines[2],
                        "unit_price": lines[3],
                        "total": lines[4],
                        "currency": lines[5],
                    }
                except IndexError:
                    pass

    # Старый формат "Заявка на покупку"
    old_match = re.match(
        r"🛒 Заявка на покупку\n\n"
        r"Количество: (\d+) шт\.\n"
        r"Цена за 1 шт\.: ([0-9 .,]+) ([A-Za-z]+)\n"
        r"Итого к оплате: ([0-9 .,]+) ([A-Za-z]+)",
        content,
    )
    if old_match:
        return {
            "buyer_name": "",
            "qty": old_match.group(1),
            "unit_price": old_match.group(2),
            "total": old_match.group(4),
            "currency": old_match.group(5),
        }

    # Очень старый формат: "Покупаю 2 шт. по..."
    very_old = re.match(
        r"🛒 Покупаю (\d+) шт\. по ([0-9 .,]+) ([A-Za-z]+)\. С вас: ([0-9 .,]+) ([A-Za-z]+) \((\d+) шт\.\)",
        content,
    )
    if very_old:
        return {
            "buyer_name": "",
            "qty": very_old.group(1),
            "unit_price": very_old.group(2),
            "total": very_old.group(4),
            "currency": very_old.group(5),
        }

    return None


@register.filter
def parse_barter_completion_message(content):
    """
    Парсит сообщение о завершённом обмене.
    Формат: "🔄 Обмен завершён\n\nСделка по «{title}» с {buyer} успешно завершена."
    """
    if not content or "Обмен завершён" not in content or "Сделка по" not in content:
        return None
    m = re.search(r"Сделка по «([^»]+)» с (\S+) успешно завершена", content)
    if m:
        return {"listing_title": m.group(1), "buyer_name": m.group(2)}
    return None


@register.filter
def parse_barter_request_message(content):
    """
    Парсит сообщение-заявку на обмен.
    Пример текста: "Хочу обмен! Готов обсудить обмен на ваш «{title}»..."
    """
    if not content or "Хочу обмен" not in content:
        return None
    m = re.search(r"обмен на ваш «([^»]+)»", content)
    if m:
        return {"listing_title": m.group(1)}
    return {"listing_title": ""}


@register.filter
def normalize_compact_text(value):
    """
    Нормализует текст для сравнения в шаблонах:
    - lower()
    - убирает все пробельные символы (пробелы, табы, переносы строк, NBSP и т.п.)
    """
    if value is None:
        return ""
    s = str(value).lower()
    return re.sub(r"\s+", "", s, flags=re.UNICODE)


@register.filter
def parse_sell_offer_message(content):
    """
    Парсит сообщение о предложении своего товара продавцу.
    Формат (новый):
        📤SELL_OFFER\nseller_username\nlisting_pk\nlisting_title\nprice\ncurrency\nqty
    Старый формат (без qty) тоже поддерживается — тогда qty=1.
    """
    if not content:
        return None

    if "📤SELL_OFFER" in content:
        lines = content.strip().split("\n")
        if len(lines) >= 6 and lines[0] == "📤SELL_OFFER":
            try:
                data = {
                    "seller_name": lines[1],
                    "listing_pk": lines[2],
                    "listing_title": lines[3],
                    "price": lines[4],
                    "currency": lines[5],
                }
                # Если есть строка с количеством — учитываем её, иначе по умолчанию 1
                if len(lines) >= 7:
                    data["qty"] = lines[6]
                else:
                    data["qty"] = "1"
                return data
            except IndexError:
                pass

    return None


@register.filter
def currency_display(currency):
    """AUEC -> UEC для отображения, остальные без изменений."""
    if not currency:
        return ""
    c = str(currency).strip().upper()
    if c in ("AUEC", "A UEC"):
        return "UEC"
    return currency


@register.inclusion_tag("market/_price_display.html")
def price_display(amount, currency=""):
    """
    Отображение цены: [логотип] сумма UEC.
    AUEC отображается как UEC с логотипом слева.
    """
    curr = str(currency or "").strip().upper()
    if curr in ("AUEC", "A UEC") or not curr:
        curr = "UEC"
    return {"amount": str(amount or "0").strip(), "currency": curr}


@register.simple_tag
def sell_offer_details(offer, base_price, base_currency):
    """
    Возвращает детали по предложению продажи:
    - qty: количество
    - total: итоговая сумма (строка для вывода)
    - diff_text: текст про доплату (кто кому должен и сколько)
    """
    if not offer:
        return {"qty": 0, "total": "0", "diff_text": ""}

    # Количество
    try:
        qty = int(offer.get("qty") or 1)
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1

    # Цена за 1 шт. предложения
    raw_offer_price = str(offer.get("price") or "0").replace(" ", "").replace(",", ".")
    try:
        price = Decimal(raw_offer_price)
    except (InvalidOperation, TypeError):
        price = Decimal("0")

    # Базовая цена из объявления "Покупаю"
    try:
        base = Decimal(str(base_price or "0").replace(" ", "").replace(",", "."))
    except (InvalidOperation, TypeError):
        base = Decimal("0")

    offer_currency = str(offer.get("currency") or "").strip().upper() or "AUEC"
    base_curr = str(base_currency or "").strip().upper() or "AUEC"

    # Итоговая сумма
    total = price * qty
    total_str = format_price_display(total)

    # Если валюты разные — только подсказка про обсуждение в чате
    if not base or offer_currency != base_curr:
        return {
            "qty": qty,
            "total": total_str,
            "diff_text": (
                f"Разные валюты: {offer_currency} / {base_curr}. "
                "Обсудите итоговую сумму и доплату в чате."
            ),
        }

    # Сравниваем цены за 1 шт. в одной валюте
    diff_per_unit = price - base
    if abs(diff_per_unit) < Decimal("0.01"):
        diff_text = (
            f"Цены за 1 шт. совпадают — сделка без доплаты "
            f"({format_price_display(base)} {base_curr} за штуку)."
        )
    elif diff_per_unit > 0:
        diff_total = diff_per_unit * qty
        diff_text = (
            "Ваш товар дороже. "
            f"Разница за 1 шт.: {format_price_display(diff_per_unit)} {base_curr}, "
            f"за {qty} шт.: {format_price_display(diff_total)} {base_curr}. "
            "Обсудите доплату в вашу пользу."
        )
    else:
        diff_total = (-diff_per_unit) * qty
        diff_text = (
            "Товар покупателя дороже. "
            f"Разница за 1 шт.: {format_price_display(-diff_per_unit)} {base_curr}, "
            f"за {qty} шт.: {format_price_display(diff_total)} {base_curr}. "
            "Обсудите доплату в его пользу."
        )

    return {"qty": qty, "total": total_str, "diff_text": diff_text}


@register.simple_tag
def deal_totals(qty_raw, total_raw):
    """
    Детали завершённой сделки для отображения в карточке:
    - qty: количество
    - unit: цена за 1 шт. (если можно посчитать)
    - total: итоговая сумма (как форматированная строка)

    qty_raw и total_raw приходят как строки из parse_deal_message.
    """
    try:
        qty = int(str(qty_raw).strip())
    except (TypeError, ValueError):
        qty = 0

    # Преобразуем строку total в Decimal (убирая пробелы / запятые).
    raw_total = str(total_raw or "0").replace(" ", "").replace(",", ".")
    try:
        total = Decimal(raw_total)
    except (InvalidOperation, TypeError):
        total = Decimal("0")

    total_str = format_price_display(total)

    unit_str = ""
    if qty > 0 and total > 0:
        try:
            unit_price = (total / Decimal(qty)).quantize(Decimal("0.01"))
            unit_str = format_price_display(unit_price)
        except (InvalidOperation, ZeroDivisionError):
            unit_str = ""

    return {
        "qty": qty,
        "unit": unit_str,
        "total": total_str,
    }
