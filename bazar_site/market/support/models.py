from django.conf import settings
from django.db import models

from ..validators import image_upload_validator


class SupportRequest(models.Model):
    class Type(models.TextChoices):
        PRODUCT = "product", "Найти / запросить товар"
        BUG = "bug", "Сообщить о баге"
        IDEA = "idea", "Предложение по улучшению"
        SELLER = "seller", "Вопрос по продавцу / сделке"
        PREMIUM = "premium", "Премиум / оплата"
        OTHER = "other", "Другое"

    class DisputeKind(models.TextChoices):
        NOT_RECEIVED = "not_received", "Не выдали / не вернули"
        RULES_VIOLATION = "rules_violation", "Сделка не по правилам"
        SCAM = "scam", "Обман / мошенничество"
        OTHER = "other", "Другое"

    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests",
        verbose_name="Пользователь",
    )
    contact = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Контакт для ответа",
        help_text="E‑mail, Discord, Telegram или любая удобная ссылка.",
    )
    request_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.OTHER,
        verbose_name="Тип обращения",
    )
    subject = models.CharField(
        max_length=160,
        blank=True,
        verbose_name="Кратко о чём",
    )
    message = models.TextField(verbose_name="Сообщение")
    is_resolved = models.BooleanField(
        default=False,
        verbose_name="Обращение обработано",
        help_text="Если тикет закрыт, переписка в нём недоступна.",
    )
    admin_reply = models.TextField(
        blank=True,
        verbose_name="Ответ администрации (кратко)",
        help_text="Краткий итоговый ответ, который увидит пользователь в своём кабинете поддержки.",
    )
    admin_replied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время последнего ответа администрации",
    )
    admin_replied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_replies_made",
        verbose_name="Администратор, ответивший",
    )
    resolved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Время закрытия тикета",
    )
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_closed_tickets",
        verbose_name="Кто закрыл тикет",
    )

    # Привязка к спору/сделке (опционально)
    related_conversation = models.ForeignKey(
        "market.Conversation",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests",
        verbose_name="Связанный диалог",
    )
    related_listing = models.ForeignKey(
        "market.Listing",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests",
        verbose_name="Связанное объявление",
    )
    related_purchase_request = models.ForeignKey(
        "market.PurchaseRequest",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests",
        verbose_name="Связанный запрос на покупку",
    )
    against_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_requests_against",
        verbose_name="На кого жалоба",
    )
    dispute_kind = models.CharField(
        max_length=24,
        choices=DisputeKind.choices,
        blank=True,
        verbose_name="Тип спора",
    )
    dispute_details = models.TextField(
        blank=True,
        verbose_name="Детали спора",
    )

    class Meta:
        verbose_name = "Обращение в поддержку"
        verbose_name_plural = "Обращения в поддержку"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        prefix = dict(self.Type.choices).get(self.request_type, self.request_type)
        return f"[{prefix}] {self.subject or self.message[:40]}"

    @property
    def is_closed(self) -> bool:
        return bool(self.is_resolved)


class SupportMessage(models.Model):
    """Сообщение в рамках тикета (переписка пользователя и администрации)."""

    request = models.ForeignKey(
        SupportRequest,
        related_name="messages",
        on_delete=models.CASCADE,
        verbose_name="Тикет",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="support_messages",
        verbose_name="Автор сообщения",
    )
    text = models.TextField(verbose_name="Текст сообщения", blank=True)
    screenshot = models.ImageField(
        upload_to="support_screenshots/",
        blank=True,
        null=True,
        verbose_name="Скриншот",
        validators=[image_upload_validator],
    )

    class Meta:
        verbose_name = "Сообщение тикета"
        verbose_name_plural = "Сообщения тикетов"
        ordering = ["created_at", "pk"]

    def __str__(self) -> str:
        return f"Сообщение по тикету #{self.request_id}"


class SupportFAQ(models.Model):
    """Вопрос–ответ по сайту, который видят все пользователи на странице поддержки."""

    question = models.CharField(max_length=255, verbose_name="Вопрос")
    answer = models.TextField(verbose_name="Ответ")
    sort_order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    is_active = models.BooleanField(default=True, verbose_name="Показывать")

    class Meta:
        verbose_name = "FAQ: вопрос"
        verbose_name_plural = "FAQ: вопросы"
        ordering = ["sort_order", "id"]

    def __str__(self) -> str:
        return self.question

