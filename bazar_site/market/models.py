"""
Основные модели домена StarBaz.

Структура:
- UserProfile      — расширение пользователя и статусы продавца
- Category        — дерево категорий товаров
- Listing + media — объявления и связанные изображения/видео
- Conversation    — личные диалоги и сообщения
- GlobalChatMessage — сообщения общего чата
- VisitSession    — статистика посещений
- SiteSettings    — глобальные настройки и футер
- RecaptchaAdminKeys — ключи Google reCAPTCHA для входа в Django Admin
- FooterLink / FooterSocialLink — ссылки в подвале
- SellerReview    — отзывы о продавцах
- Banner / NewsItem — баннеры и новости
"""

from django.conf import settings
from django.db import models
from decimal import Decimal

from .enums import ListingDealType, ListingStatus, SellerStatusOverride
from .formatting import format_price_display
from .langvars import Lang
from .validators import image_upload_validator
from .support.models import SupportRequest


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        related_name="profile",
        on_delete=models.CASCADE,
    )
    avatar = models.ImageField(
        upload_to="avatars/",
        blank=True,
        null=True,
        verbose_name="Аватар",
        validators=[image_upload_validator],
    )
    game_nickname = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Ник в игре",
    )
    telegram = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Telegram",
        help_text="Например, @nickname или ссылка",
    )
    discord = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Discord",
        help_text="Например, nickname#0000 или ссылка",
    )
    steam = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Steam",
        help_text="Ссылка на профиль Steam",
    )
    youtube = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="YouTube",
        help_text="Ссылка на YouTube‑канал",
    )
    twitch = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Twitch",
        help_text="Ссылка на Twitch‑канал",
    )
    instagram = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Instagram",
        help_text="Ссылка на профиль Instagram",
    )
    vk = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="VK",
        help_text="Ссылка на профиль или сообщество ВКонтакте",
    )
    extra_link = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Дополнительная ссылка",
        help_text="Любая дополнительная ссылка (на продукт, сайт, портфолио и т.п.).",
    )
    is_guarantor = models.BooleanField(
        default=False,
        verbose_name="Показывать в разделе гарантов",
    )
    guarantor_title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Заголовок/роль (для гаранта)",
        help_text="Например: Основной гарант, Админ сервера и т.д.",
    )
    guarantor_description = models.TextField(
        blank=True,
        verbose_name="Описание (для гаранта)",
        help_text="Краткая информация о гаранте, опыте и правилах работы.",
    )
    guarantor_priority = models.PositiveIntegerField(
        default=0,
        verbose_name="Приоритет отображения (чем выше, тем раньше)",
    )
    last_seen = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Последний раз онлайн",
    )
    seller_status_override = models.CharField(
        max_length=20,
        blank=True,
        choices=SellerStatusOverride.choices,
        verbose_name="Фиксированный статус продавца",
        help_text="Если выбран, статус продавца на сайте будет именно таким, независимо от количества заказов.",
    )
    is_banned = models.BooleanField(
        default=False,
        verbose_name="Заблокирован",
        help_text="Если включено, пользователь не сможет пользоваться сайтом.",
    )
    ban_reason = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Причина бана",
        help_text="Кратко укажите причину блокировки (видно только в админке).",
    )
    operator = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Организация",
        help_text="Название организации или корпорации (например, Industrial Model / Omicron Heavy Industries Group).",
    )
    working_hours = models.CharField(
        max_length=300,
        blank=True,
        verbose_name="Время работы",
        help_text="Например: Я онлайн в основном по UTC +13 часов.",
    )
    preferred_language = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Предпочитаемый язык",
        help_text="Например: английский, русский.",
    )
    org_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Ссылка на организацию RSI",
        help_text="Например: https://robertsspaceindustries.com/orgs/INM",
    )
    org_logo_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Логотип организации RSI",
        help_text="Прямая ссылка на логотип (PNG) вашей организации на RSI.",
    )
    is_streamer = models.BooleanField(
        default=False,
        verbose_name="Стример",
        help_text="Отметьте, если пользователь является стримером — на карточке продавца появится анимированная плашка.",
    )
    is_project_admin = models.BooleanField(
        default=False,
        verbose_name="Администратор проекта",
        help_text="Отметьте, если пользователь является администратором площадки (получает обращения из формы поддержки и может помогать пользователям).",
    )
    is_admin_whitelist = models.BooleanField(
        default=False,
        verbose_name="Белый список админов",
        help_text="Если включено — пользователь сможет входить в Django Admin (по прямой ссылке /admin/).",
    )
    is_operator = models.BooleanField(
        default=False,
        verbose_name="Оператор (поддержка/премиум)",
        help_text="Оператор может отвечать на обращения, а также выдавать премиум и статусы пользователям.",
    )
    is_premium = models.BooleanField(
        default=False,
        verbose_name="Премиум‑статус активен",
        help_text="Если включено — у пользователя активен премиум‑статус.",
    )
    premium_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Премиум действует до",
        help_text="Дата и время окончания премиум‑статуса. Можно оставить пустым для бессрочного.",
    )
    premium_boost_credits = models.PositiveIntegerField(
        default=0,
        verbose_name="Очки поднятия объявлений",
        help_text="Сколько раз пользователь может поднять свои объявления в топ. Доступно только при активном премиум‑статусе.",
    )
    verified_bonus_given = models.BooleanField(
        default=False,
        verbose_name="Бонус за статус «Проверенный» выдан",
        help_text="Служебное поле: помогает один раз выдать бонусные очки при достижении статуса «Проверенный».",
    )

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self) -> str:
        return f"Профиль {self.user.username}"

    def save(self, *args, **kwargs):
        """Сохраняем профиль и мягко уменьшаем аватар до разумного размера."""
        super().save(*args, **kwargs)
        if not self.avatar:
            return
        try:
            from PIL import Image  # type: ignore
        except Exception:
            return
        try:
            img = Image.open(self.avatar.path)
        except Exception:
            return

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        max_size = 512
        width, height = img.size
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            img.save(self.avatar.path, optimize=True, quality=85)


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, unique=True)
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="children",
        on_delete=models.CASCADE,
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name

    @property
    def active_listings_count(self) -> int:
        return self.listings.filter(status=ListingStatus.ACTIVE).count()


class Listing(models.Model):
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="listings",
        on_delete=models.CASCADE,
    )
    deal_type = models.CharField(
        max_length=8,
        choices=ListingDealType.choices,
        default=ListingDealType.SELL,
        verbose_name="Тип объявления",
        help_text="Выберите, вы продаёте товар или хотите его купить.",
    )
    category = models.ForeignKey(
        Category,
        related_name="listings",
        on_delete=models.PROTECT,
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    original_price = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Первая цена при публикации",
    )
    price = models.DecimalField(max_digits=18, decimal_places=2)
    currency = models.CharField(max_length=8, default="AUEC")
    barter_allowed = models.BooleanField(default=False)
    barter_for = models.ManyToManyField(
        Category,
        related_name="barter_listings",
        blank=True,
        help_text="На какие типы предметов вы готовы обменять этот товар.",
    )
    barter_custom = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Свои варианты обмена",
        help_text="Напишите свои варианты через запятую, если нет подходящих категорий.",
    )
    status = models.CharField(
        max_length=16,
        choices=ListingStatus.choices,
        default=ListingStatus.ACTIVE,
    )
    seo_title = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="SEO: Заголовок",
        help_text="Если пусто — будет использоваться обычное название объявления.",
    )
    seo_description = models.CharField(
        max_length=320,
        blank=True,
        verbose_name="SEO: Описание",
        help_text="Краткое описание для поисковиков, можно оставить пустым.",
    )
    seo_keywords = models.CharField(
        max_length=320,
        blank=True,
        verbose_name="SEO: Ключевые слова",
        help_text="Через запятую: игра, броня, шлем, услуги и т.д.",
    )
    guarantor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="guaranteed_listings",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        verbose_name="Гарант по сделке",
        help_text="Пользователь‑гарант, который сопровождает эту сделку.",
    )
    source = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Источник",
        help_text="Например: Разграблено, Куплено, Крафт и т.д.",
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Местоположение",
        help_text="Местонахождение товара (например, станция, система).",
    )
    star_system = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Звёздная система",
        help_text="Звёздная система, где находится товар.",
    )
    views = models.PositiveIntegerField(
        default=0,
        verbose_name="Просмотры",
    )
    availability = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Наличие",
        help_text="Например: Готово к самовывозу, Под заказ и т.д.",
    )
    in_stock = models.BooleanField(
        default=True,
        verbose_name="Товар в наличии",
        help_text="Отметьте, если товар доступен для продажи.",
    )
    quantity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Количество",
        help_text="Сколько штук в наличии (оставьте пустым, если не важно).",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    boosted_until = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Поднято в топ до",
        help_text="Если указано будущее время — объявление показывается выше остальных и подсвечивается.",
    )

    class Meta:
        verbose_name = "Объявление"
        verbose_name_plural = "Объявления"
        ordering = ["-created_at"]
        indexes = [
            # Важные индексы для масштабирования и быстрых выборок
            models.Index(fields=["seller"], name="listing_seller_idx"),
            models.Index(fields=["created_at"], name="listing_created_idx"),
            models.Index(fields=["price"], name="listing_price_idx"),
            models.Index(fields=["status"], name="listing_status_idx"),
        ]

    def __str__(self) -> str:
        return self.title

    @property
    def main_image(self):
        main = self.images.filter(is_main=True).first()
        return main or self.images.first()

    # Порог для показа полной суммы (1 трлн)
    PRICE_FULL_THRESHOLD = Decimal("1000000000000")

    @property
    def price_compact(self) -> str:
        """Цена с суффиксом k/M/Bn для отображения."""
        return self._price_compact_for(self.price)

    @property
    def price_display(self) -> str:
        """Цена: полная сумма до 1 трлн, иначе компактная (k/M/Bn)."""
        if self.price is None:
            return ""
        try:
            num = Decimal(self.price)
        except Exception:
            return str(self.price)
        if num < 0 or num >= self.PRICE_FULL_THRESHOLD:
            return self._price_compact_for(self.price)
        return self._format_decimal(self.price)

    def _price_compact_for(self, value: Decimal | None) -> str:
        if value is None:
            return ""

        try:
            num = Decimal(value)
        except Exception:
            return str(value)

        negative = num < 0
        num = abs(num)

        thousand = Decimal(1000)
        million = thousand * thousand      # 1 000 000
        billion = million * thousand       # 1 000 000 000
        trillion = billion * thousand      # 1 000 000 000 000

        suffix = ""
        divisor = Decimal(1)

        if num >= trillion:
            divisor, suffix = trillion, "Tn"
        elif num >= billion:
            divisor, suffix = billion, "Bn"
        elif num >= million:
            divisor, suffix = million, "M"
        elif num >= thousand:
            divisor, suffix = thousand, "k"

        if divisor == 1:
            s = f"{num.normalize():f}".rstrip("0").rstrip(".")
            return f"-{s}" if negative else s

        value_short = num / divisor
        num_str = f"{value_short:.2f}".rstrip("0").rstrip(".")
        return f"-{num_str}{suffix}" if negative else f"{num_str}{suffix}"

    def _format_decimal(self, value: Decimal | None) -> str:
        """Форматирование цены для отображения (пробелы как разделитель тысяч)."""
        return format_price_display(value)

    @property
    def price_full(self) -> str:
        """Полная цена с разделением тысяч пробелами, например 500 000.00."""
        return self._format_decimal(self.price)

    @property
    def original_price_full(self) -> str:
        """Первая цена при публикации (если отличается от текущей)."""
        return self._format_decimal(self.original_price or self.price)

    @property
    def discount_percent(self) -> int | None:
        """Процент скидки относительно первой цены, если текущая ниже."""
        if not self.original_price:
            return None
        try:
            orig = Decimal(self.original_price)
            current = Decimal(self.price)
        except Exception:
            return None
        if orig <= 0 or current >= orig:
            return None
        percent = (orig - current) / orig * Decimal(100)
        return int(percent.quantize(Decimal("1")))

    @property
    def original_price_compact(self) -> str:
        """Компактная форма первой цены (k/M/Bn)."""
        return self._price_compact_for(self.original_price or self.price)


class ListingPriceHistory(models.Model):
    """История изменений цены объявления для графика на карточке товара."""

    listing = models.ForeignKey(
        Listing,
        related_name="price_history",
        on_delete=models.CASCADE,
    )
    price = models.DecimalField(max_digits=18, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "История цены"
        verbose_name_plural = "История цен"
        ordering = ["recorded_at"]

    def __str__(self) -> str:
        return f"{self.listing_id} @ {self.price}"


class ListingImage(models.Model):
    listing = models.ForeignKey(
        Listing,
        related_name="images",
        on_delete=models.CASCADE,
    )
    image = models.ImageField(
        upload_to="listing_images/",
        validators=[image_upload_validator],
    )
    sort_order = models.PositiveIntegerField(default=0)
    is_main = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Изображение объявления"
        verbose_name_plural = "Изображения объявлений"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Изображение для {self.listing_id}"

    def delete(self, *args, **kwargs):
        """Удаляем файл с диска при удалении записи."""
        image = self.image
        super().delete(*args, **kwargs)
        if image:
            try:
                image.storage.delete(image.name)
            except Exception:
                pass

    def save(self, *args, **kwargs):
        """Сохраняем и обрезаем изображение до квадрата и помечаем главное фото."""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        try:
            from PIL import Image
        except Exception:
            return

        if not self.image:
            return

        image_path = self.image.path
        img = Image.open(image_path)

        # Преобразуем в RGB для совместимости форматов
        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        width, height = img.size
        side = min(width, height)
        left = (width - side) // 2
        top = (height - side) // 2
        right = left + side
        bottom = top + side

        img = img.crop((left, top, right, bottom))

        # Дополнительно уменьшим до разумного размера
        max_size = 800
        if side > max_size:
            img = img.resize((max_size, max_size), Image.LANCZOS)

        img.save(image_path)

        # Логика главной картинки:
        # если эта картинка отмечена как главная — снимаем флаг с остальных
        if self.is_main:
            ListingImage.objects.filter(listing=self.listing).exclude(
                pk=self.pk
            ).update(is_main=False)
        # если это первая картинка у объявления и главная ещё не выбрана
        elif is_new and not ListingImage.objects.filter(
            listing=self.listing, is_main=True
        ).exclude(pk=self.pk).exists():
            self.is_main = True
            super().save(update_fields=["is_main"])


class ListingVideo(models.Model):
    listing = models.ForeignKey(
        Listing,
        related_name="videos",
        on_delete=models.CASCADE,
    )
    file = models.FileField(
        upload_to="listing_videos/",
        verbose_name="Видео",
    )
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Видео объявления"
        verbose_name_plural = "Видео объявлений"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return f"Видео для {self.listing_id}"

    def delete(self, *args, **kwargs):
        """Удаляем файл с диска при удалении записи."""
        file = self.file
        super().delete(*args, **kwargs)
        if file:
            try:
                file.storage.delete(file.name)
            except Exception:
                pass

    def delete(self, *args, **kwargs):
        """Удаляем файл с диска при удалении записи."""
        file = self.file
        super().delete(*args, **kwargs)
        if file:
            try:
                file.storage.delete(file.name)
            except Exception:
                pass


class Conversation(models.Model):
    listing = models.ForeignKey(
        Listing,
        related_name="conversations",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="purchases_conversations",
        on_delete=models.CASCADE,
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sales_conversations",
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Диалог"
        verbose_name_plural = "Диалоги"
        unique_together = ("listing", "buyer", "seller")

    def __str__(self) -> str:
        return f"Диалог по {self.listing_id}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="messages",
        on_delete=models.CASCADE,
    )
    content = models.TextField(blank=True)
    image = models.ImageField(
        upload_to="chat_images/",
        null=True,
        blank=True,
        verbose_name="Картинка",
        validators=[image_upload_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ["created_at"]

    def __str__(self) -> str:
        return f"{self.sender}: {self.content[:30]}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.image:
            try:
                from PIL import Image
            except Exception:
                return
            try:
                img = Image.open(self.image.path)
            except Exception:
                return

            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")

            max_size = 900
            width, height = img.size
            if width > max_size or height > max_size:
                img.thumbnail((max_size, max_size), Image.LANCZOS)
                img.save(self.image.path, optimize=True, quality=85)


class PurchaseRequest(models.Model):
    """Запрос покупателя на покупку — ожидает подтверждения продавца."""

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает"
        COMPLETED = "completed", "Завершено"
        CANCELLED = "cancelled", "Отменено"

    conversation = models.ForeignKey(
        Conversation,
        related_name="purchase_requests",
        on_delete=models.CASCADE,
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="purchase_requests",
        on_delete=models.CASCADE,
    )
    quantity = models.PositiveIntegerField(verbose_name="Количество")
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Запрос на покупку"
        verbose_name_plural = "Запросы на покупку"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.buyer} × {self.quantity} ({self.status})"


class DealCompletion(models.Model):
    """Завершённая сделка по объявлению с количеством — для автообновления остатков."""

    conversation = models.ForeignKey(
        Conversation,
        related_name="deal_completions",
        on_delete=models.CASCADE,
    )
    quantity_sold = models.PositiveIntegerField(verbose_name="Продано шт.")
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="deal_completions_made",
        on_delete=models.CASCADE,
    )
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Завершённая сделка"
        verbose_name_plural = "Завершённые сделки"
        ordering = ["-completed_at"]

    def __str__(self) -> str:
        return f"{self.conversation_id}: {self.quantity_sold} шт."


class GlobalChatMessage(models.Model):
    """Сообщение в общем чате на главной странице."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="global_messages",
        on_delete=models.CASCADE,
    )
    content = models.TextField(max_length=500)
    reply_to = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        related_name="replies",
        on_delete=models.SET_NULL,
        verbose_name="Ответ на сообщение",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Сообщение общего чата"
        verbose_name_plural = "Сообщения общего чата"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.user}: {self.content[:30]}"


class VisitSession(models.Model):
    """Сессия посещения сайта (для простой статистики трафика)."""

    session_key = models.CharField(max_length=40, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="visit_sessions",
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    first_path = models.CharField(max_length=512, blank=True)
    last_path = models.CharField(max_length=512, blank=True)
    first_referrer = models.CharField(max_length=512, blank=True)
    last_referrer = models.CharField(max_length=512, blank=True)
    pageviews = models.PositiveIntegerField(default=0)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Сессия посещения"
        verbose_name_plural = "Сессии посещений"
        ordering = ["-last_seen"]

    def __str__(self) -> str:
        return f"Сессия {self.session_key} ({self.user or self.ip_address})"

    @property
    def duration_seconds(self) -> int:
        if not self.first_seen or not self.last_seen:
            return 0
        delta = self.last_seen - self.first_seen
        return int(delta.total_seconds())

    def duration_human(self) -> str:
        seconds = self.duration_seconds
        if seconds < 60:
            return Lang.VisitSessionText.SECONDS.format(seconds=seconds)
        minutes, sec = divmod(seconds, 60)
        if minutes < 60:
            return Lang.VisitSessionText.MINUTES_SECONDS.format(
                minutes=minutes, seconds=sec
            )
        hours, minutes = divmod(minutes, 60)
        return Lang.VisitSessionText.HOURS_MINUTES.format(
            hours=hours, minutes=minutes
        )


class SiteSettings(models.Model):
    name = models.CharField(max_length=100, default=Lang.SiteSettingsDefaults.NAME)
    primary_color = models.CharField(
        max_length=20, default=Lang.SiteSettingsDefaults.PRIMARY_COLOR
    )
    secondary_color = models.CharField(
        max_length=20, default=Lang.SiteSettingsDefaults.SECONDARY_COLOR
    )
    logo_text = models.CharField(
        max_length=50, default=Lang.SiteSettingsDefaults.LOGO_TEXT
    )
    footer_text = models.CharField(
        max_length=255,
        default=Lang.SiteSettingsDefaults.FOOTER_TEXT,
    )
    hero_title = models.CharField(
        max_length=150,
        default=Lang.SiteSettingsDefaults.HERO_TITLE,
    )
    hero_subtitle = models.CharField(
        max_length=300,
        default=Lang.SiteSettingsDefaults.HERO_SUBTITLE,
    )
    how_it_works_title = models.CharField(
        max_length=100,
        default=Lang.SiteSettingsDefaults.HOW_IT_WORKS_TITLE,
    )
    how_it_works_item1 = models.CharField(
        max_length=200,
        default=Lang.SiteSettingsDefaults.HOW_IT_WORKS_ITEM1,
    )
    how_it_works_item2 = models.CharField(
        max_length=200,
        default=Lang.SiteSettingsDefaults.HOW_IT_WORKS_ITEM2,
    )
    how_it_works_item3 = models.CharField(
        max_length=200,
        default=Lang.SiteSettingsDefaults.HOW_IT_WORKS_ITEM3,
    )
    how_it_works_item4 = models.CharField(
        max_length=200,
        default=Lang.SiteSettingsDefaults.HOW_IT_WORKS_ITEM4,
    )
    seo_meta_title = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="SEO: Title по умолчанию",
        help_text="Если оставить пустым — будет использоваться название сайта.",
    )
    seo_meta_description = models.CharField(
        max_length=320,
        blank=True,
        verbose_name="SEO: Description по умолчанию",
        help_text="Краткое описание сайта для поисковиков (до ~160–320 символов).",
    )
    seo_meta_keywords = models.CharField(
        max_length=320,
        blank=True,
        verbose_name="SEO: Ключевые слова по умолчанию",
        help_text="Через запятую: торговая площадка, игровые услуги, AUEC и т.д.",
    )
    show_home_banner = models.BooleanField(
        default=True,
        verbose_name="Показывать баннер на главной",
        help_text="Если выключено — правый баннер с картинкой скрыт, общий чат остаётся.",
    )
    show_news_block = models.BooleanField(
        default=True,
        verbose_name="Показывать блок новостей",
        help_text="Если выключено — карточки новостей и соцсетей на главной скрыты.",
    )
    background_media = models.FileField(
        upload_to="backgrounds/",
        blank=True,
        null=True,
        verbose_name="Фон сайта (картинка / видео)",
        help_text="Можно загрузить изображение, GIF или видео для фона сайта.",
    )
    background_is_video = models.BooleanField(
        default=False,
        verbose_name="Фон — это видео",
        help_text="Включите, если загружен видеофайл для фона.",
    )
    footer_col1_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Заголовок первой колонки футера",
        help_text="Например: BAZAR, название игры и т.п.",
    )
    footer_col2_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Заголовок второй колонки футера",
    )
    footer_col3_title = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Заголовок третьей колонки футера",
    )
    footer_left = models.CharField(
        max_length=255,
        default=Lang.SiteSettingsDefaults.FOOTER_LEFT,
        verbose_name="Текст слева в подвале",
        help_text="Например: © BAZAR 2026",
    )
    footer_right = models.CharField(
        max_length=255,
        default=Lang.SiteSettingsDefaults.FOOTER_RIGHT,
        verbose_name="Текст справа в подвале",
        help_text='Например: "Bazar by Louis Rocket"',
    )
    footer_about_title = models.CharField(
        max_length=120,
        default="О нас",
        verbose_name="Футер: название ссылки «О нас»",
    )
    footer_about_url = models.URLField(
        blank=True,
        verbose_name="Футер: ссылка «О нас»",
        help_text="URL страницы с описанием проекта.",
    )
    footer_privacy_title = models.CharField(
        max_length=160,
        default="Политика конфиденциальности",
        verbose_name="Футер: название ссылки «Политика конфиденциальности»",
    )
    footer_privacy_url = models.URLField(
        blank=True,
        verbose_name="Футер: ссылка на политику конфиденциальности",
    )
    footer_discord_title = models.CharField(
        max_length=120,
        default="Discord",
        verbose_name="Футер: название ссылки на Discord",
    )
    footer_discord_url = models.URLField(
        blank=True,
        verbose_name="Футер: ссылка на Discord",
    )
    footer_extra1_title = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Футер: дополнительная ссылка 1 — название",
    )
    footer_extra1_url = models.URLField(
        blank=True,
        verbose_name="Футер: дополнительная ссылка 1 — URL",
    )
    footer_extra2_title = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Футер: дополнительная ссылка 2 — название",
    )
    footer_extra2_url = models.URLField(
        blank=True,
        verbose_name="Футер: дополнительная ссылка 2 — URL",
    )
    footer_extra3_title = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="Футер: дополнительная ссылка 3 — название",
    )
    footer_extra3_url = models.URLField(
        blank=True,
        verbose_name="Футер: дополнительная ссылка 3 — URL",
    )
    footer_disclaimer = models.TextField(
        blank=True,
        verbose_name="Текст дисклеймера внизу",
        help_text="Текст про частный проект, отсутствие связи с CIG и отсутствие финансовых/инвестиционных услуг.",
        default=(
            "Данный сайт является частным проектом одного из игроков Star Citizen. "
            "Администрация игры Cloud Imperium Games, её разработчики, издатель и другие "
            "официальные лица, причастные к созданию игры, не имеют никакого отношения "
            "к данному сайту. "
            "Сайт не выставляет реальные рыночные котировки, не является финансовой, "
            "инвестиционной или банковской организацией, не относится к МММ‑подобным "
            "проектам и не осуществляет торговлю криптовалютой или настоящими деньгами."
        ),
    )
    about_page_body = models.TextField(
        blank=True,
        verbose_name="Страница «О нас» — текст",
        help_text="При наличии этого текста страница «О нас» будет выводить его как HTML.",
    )
    signup_legal_text = models.TextField(
        blank=True,
        verbose_name="Регистрация — юридический текст",
        help_text="Текст в попапе при регистрации. Можно использовать HTML‑разметку.",
    )
    useful_links_intro = models.TextField(
        blank=True,
        verbose_name="Полезные ссылки — текст страницы",
        help_text="Вводный текст над списком полезных ссылок. Можно использовать HTML‑разметку.",
    )

    class Meta:
        verbose_name = "Настройки сайта"
        verbose_name_plural = "Настройки сайта"

    def __str__(self) -> str:
        return "Настройки сайта"


class UsefulLink(models.Model):
    title = models.CharField(max_length=140, verbose_name="Название")
    url = models.URLField(max_length=500, verbose_name="Ссылка (URL)")
    description = models.CharField(
        max_length=220,
        blank=True,
        verbose_name="Описание (кратко)",
    )
    icon_class = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="Иконка (Bootstrap Icons)",
        help_text="Например: bi bi-link-45deg или bi bi-rocket-takeoff",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Полезная ссылка"
        verbose_name_plural = "Полезные ссылки"
        ordering = ("sort_order", "id")

    def __str__(self) -> str:
        return self.title


class RecaptchaAdminKeys(models.Model):
    """
    Одна запись в БД: ключи Google reCAPTCHA v2 для страницы входа в /admin/.
    Если поля пустые, используются переменные окружения / .env (см. settings).
    """

    public_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ключ сайта (site key)",
        help_text="Публичный ключ из консоли Google reCAPTCHA (тип v2 «Я не робот»).",
    )
    secret_key = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Секретный ключ (secret key)",
        help_text="Секретный ключ из той же пары. Хранится в базе; доступ только у staff.",
    )

    class Meta:
        verbose_name = "Ключи reCAPTCHA (вход в админку)"
        verbose_name_plural = "Ключи reCAPTCHA (вход в админку)"

    def __str__(self) -> str:
        return "Ключи reCAPTCHA для /admin/"


class MusicTrack(models.Model):
    """Трек для глобального медиаплеера на сайте. Файлы хранятся в media/music/."""

    name = models.CharField(
        max_length=200,
        verbose_name="Название трека",
        help_text="Отображается в плеере.",
    )
    file = models.FileField(
        upload_to="music/",
        verbose_name="Аудиофайл",
        help_text="MP3, OGG или другой поддерживаемый браузером формат.",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
        help_text="Меньше — выше в плейлисте.",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Включён",
        help_text="Выключенные треки не показываются в плеере.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Музыкальный трек"
        verbose_name_plural = "Музыкальные треки"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.name


class FooterLink(models.Model):
    COLUMN_CHOICES = [
        (1, Lang.FooterLinkText.COLUMN_1),
        (2, Lang.FooterLinkText.COLUMN_2),
        (3, Lang.FooterLinkText.COLUMN_3),
    ]

    title = models.CharField(max_length=150, verbose_name="Название ссылки")
    url = models.URLField(verbose_name="URL")
    column = models.PositiveSmallIntegerField(
        choices=COLUMN_CHOICES,
        default=1,
        verbose_name="Колонка",
    )
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Ссылка футера"
        verbose_name_plural = "Ссылки футера"
        ordering = ["column", "sort_order", "title"]

    def __str__(self) -> str:
        return self.title


class FooterSocialLink(models.Model):
    NETWORK_CHOICES = [
        ("facebook", Lang.SocialNetworkText.FACEBOOK),
        ("instagram", Lang.SocialNetworkText.INSTAGRAM),
        ("youtube", Lang.SocialNetworkText.YOUTUBE),
        ("twitch", Lang.SocialNetworkText.TWITCH),
        ("discord", Lang.SocialNetworkText.DISCORD),
        ("telegram", Lang.SocialNetworkText.TELEGRAM),
        ("twitter", Lang.SocialNetworkText.TWITTER_X),
        ("vk", Lang.SocialNetworkText.VK),
    ]

    network = models.CharField(
        max_length=20,
        choices=NETWORK_CHOICES,
        verbose_name="Соцсеть",
    )
    url = models.URLField(verbose_name="URL", blank=True)
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Активна")

    class Meta:
        verbose_name = "Соцсеть в футере"
        verbose_name_plural = "Соцсети в футере"
        ordering = ["sort_order", "network"]

    def __str__(self) -> str:
        return dict(self.NETWORK_CHOICES).get(self.network, self.network)

    @property
    def icon_class(self) -> str:
        mapping = {
            "facebook": "bi-facebook",
            "instagram": "bi-instagram",
            "youtube": "bi-youtube",
            "twitch": "bi-twitch",
            "discord": "bi-discord",
            "telegram": "bi-telegram",
            "twitter": "bi-twitter-x",
            "vk": "bi-twitter",  # нет отдельной иконки VK в bootstrap-icons
        }
        return mapping.get(self.network, "bi-link-45deg")


class SellerReview(models.Model):
    """Отзыв о продавце по конкретному товару."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    listing = models.ForeignKey(
        Listing,
        related_name="reviews",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="received_reviews",
        on_delete=models.CASCADE,
    )
    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="written_reviews",
        on_delete=models.CASCADE,
    )
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    text = models.TextField()
    reply_text = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reply_created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Отзыв о продавце"
        verbose_name_plural = "Отзывы о продавце"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Отзыв {self.buyer} → {self.seller} по {self.listing_id}"


class Banner(models.Model):
    title = models.CharField(
        max_length=150,
        blank=True,
        verbose_name="Заголовок (необязательно)",
    )
    image = models.ImageField(
        upload_to="banners/",
        verbose_name="Картинка баннера",
        validators=[image_upload_validator],
    )
    link_url = models.URLField(
        blank=True,
        verbose_name="Ссылка (необязательно)",
        help_text="При клике откроется эта ссылка. Можно оставить пустым.",
    )
    show_in_hero = models.BooleanField(
        default=True,
        verbose_name="Показывать в большом баннере",
    )
    show_under_categories = models.BooleanField(
        default=False,
        verbose_name="Показывать под категориями",
    )
    sort_order = models.PositiveIntegerField(
        default=0,
        verbose_name="Порядок",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активен",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Баннер"
        verbose_name_plural = "Баннеры"
        ordering = ["sort_order", "-created_at"]

    def __str__(self) -> str:
        return self.title or f"Баннер #{self.pk}"

    def save(self, *args, **kwargs):
        """Авто‑ресайз баннера до ~1200px по большой стороне."""
        super().save(*args, **kwargs)
        if not self.image:
            return
        try:
            from PIL import Image  # type: ignore
        except Exception:
            return
        try:
            img = Image.open(self.image.path)
        except Exception:
            return

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        max_size = 1200
        width, height = img.size
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            img.save(self.image.path, optimize=True, quality=85)


class NewsItem(models.Model):
    SOURCE_CHOICES = [
        ("telegram", Lang.NewsSourceText.TELEGRAM),
        ("instagram", Lang.NewsSourceText.INSTAGRAM),
        ("twitch", Lang.NewsSourceText.TWITCH),
        ("vk", Lang.NewsSourceText.VK),
        ("youtube", Lang.NewsSourceText.YOUTUBE),
        ("other", Lang.NewsSourceText.OTHER),
    ]

    title = models.CharField(max_length=200, verbose_name="Заголовок")
    text = models.TextField(blank=True, verbose_name="Текст")
    source = models.CharField(
        max_length=20,
        choices=SOURCE_CHOICES,
        default="telegram",
        verbose_name="Платформа",
    )
    link_url = models.URLField(verbose_name="Ссылка", help_text="Ссылка на пост или канал")
    preview_image = models.ImageField(
        upload_to="news_previews/",
        blank=True,
        null=True,
        verbose_name="Превью (опционально)",
        help_text="Картинка превью для ссылки, если нужно показать обложку.",
        validators=[image_upload_validator],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_pinned = models.BooleanField(default=False, verbose_name="Закреплено")
    is_active = models.BooleanField(default=True, verbose_name="Показывать")

    class Meta:
        verbose_name = "Новость"
        verbose_name_plural = "Новости"
        ordering = ["-is_pinned", "-created_at"]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs):
        """Авто‑ресайз превью новости до ~800px по большой стороне."""
        super().save(*args, **kwargs)
        if not self.preview_image:
            return
        try:
            from PIL import Image  # type: ignore
        except Exception:
            return
        try:
            img = Image.open(self.preview_image.path)
        except Exception:
            return

        if img.mode not in ("RGB", "RGBA"):
            img = img.convert("RGB")

        max_size = 800
        width, height = img.size
        if width > max_size or height > max_size:
            img.thumbnail((max_size, max_size), Image.LANCZOS)
            img.save(self.preview_image.path, optimize=True, quality=85)

