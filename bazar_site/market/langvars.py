from __future__ import annotations

"""
Единое место для текстовых констант (русский язык).

Все новые русские строки в Python‑коде должны ссылаться сюда,
а не дублироваться по модулям.
"""


class Lang:
    class DealType:
        SELL = "Продаю"
        BUY = "Покупаю"
        TRADE = "Обмен"

    class ListingStatus:
        ACTIVE = "Активно"
        RESERVED = "В резерве"
        SOLD = "Продано"
        HIDDEN = "Скрыто"

    class SellerStatus:
        AUTO = "Авто (по заказам и рейтингу)"
        BASIC = "Обычный"
        VERIFIED = "Проверенный продавец"
        SILVER = "Серебряный продавец"
        GOLD = "Золотой продавец"
        COSMIC = "Космический продавец"

    class ListingPage:
        TITLE_ALL = "Все объявления"
        TITLE_BY_CATEGORY = "Объявления — {category_name}"

    class ListingValidation:
        ORIGINAL_REQUIRED = "Укажите рыночную цену товара."
        ORIGINAL_MUST_BE_NUMBER = "Рыночная цена должна быть числом в AUEC."
        ORIGINAL_NON_NEGATIVE = "Рыночная цена не может быть отрицательной."
        ORIGINAL_MAX_LIMIT = (
            "Максимальная рыночная цена — 999 999 999 999 999.99 AUEC."
        )

        DISCOUNT_MUST_BE_NUMBER = "Цена со скидкой должна быть числом в AUEC."
        DISCOUNT_NON_NEGATIVE = "Цена со скидкой не может быть отрицательной."
        DISCOUNT_MAX_LIMIT = (
            "Максимальная цена со скидкой — 999 999 999 999 999.99 AUEC."
        )
        DISCOUNT_NOT_HIGHER_THAN_ORIGINAL = (
            "Цена со скидкой должна быть меньше или равна рыночной."
        )

    class RateLimit:
        TOO_MANY_REQUESTS = "Слишком много запросов. Попробуйте повторить позже."

    class VisitSessionText:
        SECONDS = "{seconds} c"
        MINUTES_SECONDS = "{minutes} мин {seconds} c"
        HOURS_MINUTES = "{hours} ч {minutes} мин"

    class SiteSettingsDefaults:
        NAME = "StarBaz"
        PRIMARY_COLOR = "#1f2937"
        SECONDARY_COLOR = "#22c55e"
        LOGO_TEXT = "StarBaz"
        FOOTER_TEXT = "StarBaz — игровая торговая площадка"
        HERO_TITLE = "StarBaz — торговая площадка по вашей игре"
        HERO_SUBTITLE = (
            "Выставляйте предметы, находите выгодные предложения и мгновенно "
            "выходите на связь с продавцами через встроенный чат."
        )
        HOW_IT_WORKS_TITLE = "Как это работает"
        HOW_IT_WORKS_ITEM1 = "Вход через Discord — не нужны отдельные логины."
        HOW_IT_WORKS_ITEM2 = (
            "Гибкие категории под вашу игру: броня, шлемы, нагрудная броня и другое."
        )
        HOW_IT_WORKS_ITEM3 = "Личные диалоги по каждому объявлению."
        HOW_IT_WORKS_ITEM4 = "Можно настроить внешний вид StarBaz под свой стиль."
        FOOTER_LEFT = "© StarBaz 2026"
        FOOTER_RIGHT = "StarBaz by Louis Rocket"

    class AdminText:
        DELETE_GUEST_ACCOUNTS_DESCRIPTION = (
            "Очистить гостевые аккаунты (username начинается с 'guest', "
            "без объявлений и диалогов, старше 7 дней)"
        )
        DELETE_GUEST_ACCOUNTS_MESSAGE = "Удалено гостевых аккаунтов: {count}"

    class FooterLinkText:
        COLUMN_1 = "Колонка 1"
        COLUMN_2 = "Колонка 2"
        COLUMN_3 = "Колонка 3"

    class SocialNetworkText:
        FACEBOOK = "Facebook"
        INSTAGRAM = "Instagram"
        YOUTUBE = "YouTube"
        TWITCH = "Twitch"
        DISCORD = "Discord"
        TELEGRAM = "Telegram"
        TWITTER_X = "Twitter / X"
        VK = "VK"

    class NewsSourceText:
        TELEGRAM = "Telegram"
        INSTAGRAM = "Instagram"
        TWITCH = "Twitch"
        VK = "VK"
        YOUTUBE = "YouTube"
        OTHER = "Другое"

