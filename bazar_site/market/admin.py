"""
Настройки Django‑админки для приложения `market`.

Структура:
- Категории и объявления (+ инлайны медиа)
- Диалоги и сообщения
- Настройки сайта и футер
- Баннеры и новости
- Профили пользователей и кастомная админка User
- Статистика посещений (VisitSession)
"""

from datetime import timedelta

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from django.db.models import F

from .langvars import Lang
from django.db import models
from .models import (
    Banner,
    Category,
    Conversation,
    DealCompletion,
    FooterLink,
    FooterSocialLink,
    Listing,
    ListingImage,
    ListingVideo,
    Message,
    MusicTrack,
    NewsItem,
    PurchaseRequest,
    RecaptchaAdminKeys,
    SellerReview,
    SiteSettings,
    UsefulLink,
    UserProfile,
    VisitSession,
)
from .support.models import SupportRequest, SupportFAQ, SupportMessage

User = get_user_model()


# === Категории и объявления ===


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "parent", "is_active", "sort_order")
    list_editable = ("is_active", "sort_order")
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}


class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1


class ListingVideoInline(admin.TabularInline):
    model = ListingVideo
    extra = 1


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "seller", "deal_type", "guarantor", "price", "currency", "status", "created_at")
    list_filter = ("status", "deal_type", "category", "guarantor")
    search_fields = ("title", "description")
    inlines = [ListingImageInline, ListingVideoInline]


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("listing", "buyer", "seller", "created_at")
    search_fields = ("listing__title", "buyer__username", "seller__username")


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("conversation", "buyer", "quantity", "status", "created_at")
    list_filter = ("status",)

@admin.register(DealCompletion)
class DealCompletionAdmin(admin.ModelAdmin):
    list_display = ("conversation", "quantity_sold", "completed_by", "completed_at")
    list_filter = ("completed_at",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "sender", "created_at", "is_read")
    list_filter = ("is_read",)
    search_fields = ("content", "sender__username")


#
# === Настройки сайта и футер ===
# 
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.TextField: {
            "widget": forms.Textarea(
                attrs={
                    "rows": 6,
                    "class": "vLargeTextField rich-textarea",
                    "style": "font-family: monospace;",
                }
            )
        }
    }
    fieldsets = (
        ("Брендинг", {"fields": ("name", "logo_text", "primary_color", "secondary_color", "footer_text", "footer_left", "footer_right")}),
        (
            "Главный экран",
            {
                "fields": (
                    "hero_title",
                    "hero_subtitle",
                    "show_home_banner",
                    "show_news_block",
                )
            },
        ),
        (
            "SEO (по умолчанию для сайта)",
            {
                "fields": (
                    "seo_meta_title",
                    "seo_meta_description",
                    "seo_meta_keywords",
                )
            },
        ),
        (
            "Фон сайта",
            {
                "fields": (
                    "background_media",
                    "background_is_video",
                    "footer_col1_title",
                    "footer_col2_title",
                    "footer_col3_title",
                )
            },
        ),
        (
            "Футер: ссылки и дисклеймер",
            {
                "fields": (
                    "footer_about_title",
                    "footer_about_url",
                    "footer_privacy_title",
                    "footer_privacy_url",
                    "footer_discord_title",
                    "footer_discord_url",
                    "footer_extra1_title",
                    "footer_extra1_url",
                    "footer_extra2_title",
                    "footer_extra2_url",
                    "footer_extra3_title",
                    "footer_extra3_url",
                    "footer_disclaimer",
                )
            },
        ),
        (
            "Страницы и юр.информация",
            {
                "fields": (
                    "about_page_body",
                    "signup_legal_text",
                    "useful_links_intro",
                )
            },
        ),
    )


@admin.register(UsefulLink)
class UsefulLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "sort_order", "is_active", "url")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("title", "description", "url")
    ordering = ("sort_order", "id")

    class Media:
        js = ("market/admin/useful_link_icon_picker.js",)


@admin.register(RecaptchaAdminKeys)
class RecaptchaAdminKeysAdmin(admin.ModelAdmin):
    """Одна запись: ключи reCAPTCHA для страницы входа в /admin/."""

    list_display = ("id", "site_key_short", "secret_configured")
    fields = ("public_key", "secret_key")

    @admin.display(description="Ключ сайта (фрагмент)")
    def site_key_short(self, obj: RecaptchaAdminKeys) -> str:
        s = (obj.public_key or "").strip()
        if not s:
            return "—"
        if len(s) > 28:
            return f"{s[:14]}…{s[-10:]}"
        return s

    @admin.display(description="Secret задан", boolean=True)
    def secret_configured(self, obj: RecaptchaAdminKeys) -> bool:
        return bool((obj.secret_key or "").strip())

    def has_add_permission(self, request) -> bool:
        return not RecaptchaAdminKeys.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(MusicTrack)
class MusicTrackAdmin(admin.ModelAdmin):
    list_display = ("name", "sort_order", "is_active", "created_at")
    list_editable = ("sort_order", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("sort_order", "id")


@admin.register(FooterLink)
class FooterLinkAdmin(admin.ModelAdmin):
    list_display = ("title", "url", "column", "sort_order", "is_active")
    list_editable = ("column", "sort_order", "is_active")
    list_filter = ("column", "is_active")
    search_fields = ("title", "url")


@admin.register(FooterSocialLink)
class FooterSocialLinkAdmin(admin.ModelAdmin):
    list_display = ("network", "url", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    list_filter = ("network", "is_active")


#
# === Баннеры, новости, отзывы ===
#
@admin.register(SellerReview)
class SellerReviewAdmin(admin.ModelAdmin):
    list_display = ("listing", "seller", "buyer", "rating", "created_at")
    list_filter = ("rating",)
    search_fields = ("listing__title", "seller__username", "buyer__username", "text")


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "link_url", "is_active", "show_in_hero", "show_under_categories", "sort_order", "created_at")
    list_editable = ("is_active", "show_in_hero", "show_under_categories", "sort_order")
    list_filter = ("is_active", "show_in_hero", "show_under_categories")
    search_fields = ("title", "link_url")


@admin.register(NewsItem)
class NewsItemAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "is_pinned", "is_active", "created_at")
    list_filter = ("source", "is_active", "is_pinned")
    list_editable = ("is_pinned", "is_active")
    search_fields = ("title", "text", "link_url")


#
# === Пользователи, профили и гостевые аккаунты ===
#
class UserProfileAdminForm(forms.ModelForm):
    PREMIUM_PRESET_CHOICES = [
        ("", "— не менять премиум —"),
        ("month", "Премиум на 1 месяц от сегодня"),
        ("3m", "Премиум на 3 месяца от сегодня"),
        ("year", "Премиум на 12 месяцев от сегодня"),
        ("lifetime", "Премиум бессрочно"),
        ("clear", "Снять премиум‑статус"),
    ]

    user_email = forms.EmailField(
        label="E-mail пользователя",
        required=False,
        help_text="Почта привязана к аккаунту пользователя (не к профилю). Здесь можно изменить её прямо из профиля.",
    )

    new_password1 = forms.CharField(
        label="Новый пароль",
        required=False,
        widget=forms.PasswordInput(render_value=False),
        help_text="Оставьте пустым, если не нужно менять пароль.",
    )
    new_password2 = forms.CharField(
        label="Повтор нового пароля",
        required=False,
        widget=forms.PasswordInput(render_value=False),
    )

    premium_preset = forms.ChoiceField(
        label="Быстрый выбор премиум‑пакета",
        required=False,
        choices=PREMIUM_PRESET_CHOICES,
        help_text="Выберите вариант, чтобы автоматически выставить период премиума от сегодняшней даты, "
        "или снимите прем по необходимости. Если оставить пустым — премиум не меняется.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if getattr(self.instance, "user", None) is not None:
            self.fields["user_email"].initial = (self.instance.user.email or "").strip()

    def clean_user_email(self):
        email = (self.cleaned_data.get("user_email") or "").strip()
        if not email:
            return ""
        user = getattr(self.instance, "user", None)
        if user is None:
            return email
        # Проверяем, что e-mail не занят другим пользователем.
        user_model = get_user_model()
        if user_model.objects.filter(email__iexact=email).exclude(pk=user.pk).exists():
            raise forms.ValidationError("Этот e-mail уже используется другим пользователем.")
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get("new_password1") or ""
        p2 = cleaned.get("new_password2") or ""
        if p1 or p2:
            if p1 != p2:
                raise forms.ValidationError("Пароли не совпадают.")
            user = getattr(self.instance, "user", None)
            # Прогоняем через валидаторы Django (минимальная длина и т.п.)
            try:
                validate_password(p1, user=user)
            except forms.ValidationError as e:
                raise forms.ValidationError(e.messages)
        return cleaned

    class Meta:
        model = UserProfile
        fields = "__all__"


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    form = UserProfileAdminForm
    list_display = ("user", "user_id_display", "user_email_display", "game_nickname", "is_guarantor", "is_streamer", "is_premium", "premium_until", "is_project_admin", "is_operator", "is_admin_whitelist", "is_banned", "guarantor_title", "seller_status_override")
    list_filter = ("is_guarantor", "is_streamer", "is_premium", "is_project_admin", "is_operator", "is_admin_whitelist", "is_banned", "seller_status_override")
    actions = ["set_premium_1_month", "set_premium_3_months", "set_premium_12_months", "clear_premium"]
    search_fields = ("user__id", "user__username", "game_nickname")
    readonly_fields = ("user_id_display",)

    def save_model(self, request, obj, form, change):
        # Обновляем e-mail на связанном User, если меняли в форме профиля.
        try:
            new_email = (form.cleaned_data.get("user_email") or "").strip()
            if getattr(obj, "user", None) is not None:
                current_email = (obj.user.email or "").strip()
                if new_email != current_email:
                    obj.user.email = new_email
                    obj.user.save(update_fields=["email"])
        except Exception:
            # Если e-mail не удалось сохранить (например, из-за ограничений БД),
            # не ломаем сохранение профиля — ошибка будет видна по результату.
            pass

        # Смена пароля пользователя (если указали новый пароль).
        try:
            new_password = (form.cleaned_data.get("new_password1") or "").strip()
            if new_password and getattr(obj, "user", None) is not None:
                obj.user.set_password(new_password)
                obj.user.save(update_fields=["password"])
        except Exception:
            pass

        # Если включили белый список админов — делаем пользователя staff,
        # иначе он физически не сможет войти в Django Admin.
        try:
            if getattr(obj, "user", None) is not None and (obj.is_admin_whitelist or obj.is_project_admin or obj.is_operator):
                if not obj.user.is_staff:
                    obj.user.is_staff = True
                    obj.user.save(update_fields=["is_staff"])
        except Exception:
            pass

        preset = form.cleaned_data.get("premium_preset")
        if preset:
            now = timezone.now()
            if preset == "month":
                obj.is_premium = True
                obj.premium_until = now + timedelta(days=30)
                obj.premium_boost_credits = (obj.premium_boost_credits or 0) + 5
            elif preset == "3m":
                obj.is_premium = True
                obj.premium_until = now + timedelta(days=90)
                obj.premium_boost_credits = (obj.premium_boost_credits or 0) + 20
            elif preset == "year":
                obj.is_premium = True
                obj.premium_until = now + timedelta(days=365)
                obj.premium_boost_credits = (obj.premium_boost_credits or 0) + 250
            elif preset == "lifetime":
                obj.is_premium = True
                obj.premium_until = None
            elif preset == "clear":
                obj.is_premium = False
                obj.premium_until = None
        super().save_model(request, obj, form, change)

    @admin.action(description="Выдать премиум на 1 месяц с сегодняшнего дня")
    def set_premium_1_month(self, request, queryset):
        from django.utils import timezone

        now = timezone.now()
        until = now + timedelta(days=30)
        updated = queryset.update(
            is_premium=True,
            premium_until=until,
            premium_boost_credits=F("premium_boost_credits") + 5,
        )
        self.message_user(request, f"Премиум на 1 месяц выдан {updated} пользователям.")

    @admin.action(description="Выдать премиум на 3 месяца с сегодняшнего дня")
    def set_premium_3_months(self, request, queryset):
        from django.utils import timezone

        now = timezone.now()
        until = now + timedelta(days=90)
        updated = queryset.update(
            is_premium=True,
            premium_until=until,
            premium_boost_credits=F("premium_boost_credits") + 20,
        )
        self.message_user(request, f"Премиум на 3 месяца выдан {updated} пользователям.")

    @admin.action(description="Выдать премиум на 12 месяцев с сегодняшнего дня")
    def set_premium_12_months(self, request, queryset):
        from django.utils import timezone

        now = timezone.now()
        until = now + timedelta(days=365)
        updated = queryset.update(
            is_premium=True,
            premium_until=until,
            premium_boost_credits=F("premium_boost_credits") + 250,
        )
        self.message_user(request, f"Премиум на 12 месяцев выдан {updated} пользователям.")

    @admin.action(description="Снять премиум‑статус")
    def clear_premium(self, request, queryset):
        updated = queryset.update(is_premium=False, premium_until=None)
        self.message_user(request, f"Премиум снят у {updated} пользователей.")

    @admin.display(description="ID пользователя")
    def user_id_display(self, obj: UserProfile) -> int | None:
        if obj.user_id:
            return obj.user_id
        return None

    @admin.display(description="E-mail")
    def user_email_display(self, obj: UserProfile) -> str:
        try:
            return (obj.user.email or "").strip()
        except Exception:
            return ""


# Переопределяем стандартную админку пользователя, чтобы добавить действия очистки.
try:
    admin.site.unregister(User)
except admin.sites.NotRegistered:
    pass


@admin.register(User)
class BazarUserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "is_staff", "is_superuser", "date_joined", "last_login")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("id", "username", "email")
    actions = ["delete_guest_accounts"]

    @admin.action(description=Lang.AdminText.DELETE_GUEST_ACCOUNTS_DESCRIPTION)
    def delete_guest_accounts(self, request, queryset):
        cutoff = timezone.now() - timedelta(days=7)
        guests = (
            User.objects.filter(
                username__istartswith="guest",
                is_staff=False,
                is_superuser=False,
                date_joined__lt=cutoff,
            )
            .filter(
                listings__isnull=True,
                purchases_conversations__isnull=True,
                sales_conversations__isnull=True,
                messages__isnull=True,
            )
            .distinct()
        )
        deleted_count, _ = guests.delete()
        self.message_user(
            request,
            Lang.AdminText.DELETE_GUEST_ACCOUNTS_MESSAGE.format(count=deleted_count),
        )


@admin.register(VisitSession)
class VisitSessionAdmin(admin.ModelAdmin):
    list_display = (
        "session_key",
        "user",
        "ip_address",
        "pageviews",
        "first_seen",
        "last_seen",
        "duration_display",
        "last_path",
    )
    list_filter = ("first_seen", "user")
    search_fields = ("session_key", "ip_address", "user__username", "first_path", "last_path")
    date_hierarchy = "first_seen"
    readonly_fields = (
        "session_key",
        "user",
        "ip_address",
        "user_agent",
        "first_path",
        "last_path",
        "first_referrer",
        "last_referrer",
        "pageviews",
        "first_seen",
        "last_seen",
        "duration_display",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Разрешаем только просмотр (readonly)
        return request.method in ("GET", "HEAD", "OPTIONS")

    @admin.display(description="Время на сайте")
    def duration_display(self, obj: VisitSession) -> str:
        return obj.duration_human()


@admin.register(SupportRequest)
class SupportRequestAdmin(admin.ModelAdmin):
    class SupportMessageInline(admin.TabularInline):
        model = SupportMessage
        extra = 0
        readonly_fields = ("created_at", "author", "text", "screenshot")

    list_display = ("created_at", "request_type", "author", "contact", "subject", "is_resolved", "related_conversation", "against_user", "admin_replied_by", "resolved_by")
    list_filter = ("request_type", "is_resolved", "created_at")
    search_fields = ("subject", "message", "contact", "author__username", "author__email")
    readonly_fields = ("created_at", "author", "admin_replied_at", "admin_replied_by", "resolved_at", "resolved_by", "related_conversation", "related_listing", "related_purchase_request", "against_user", "dispute_kind", "dispute_details")
    inlines = [SupportMessageInline]

    def _can_handle_support(self, request) -> bool:
        if request.user.is_superuser:
            return True
        try:
            profile = request.user.profile  # type: ignore[attr-defined]
        except Exception:
            return False
        return bool(profile.is_project_admin or profile.is_operator)

    def _is_project_admin(self, request) -> bool:
        if request.user.is_superuser:
            return True
        try:
            profile = request.user.profile  # type: ignore[attr-defined]
        except Exception:
            return False
        return bool(profile.is_project_admin)

    def has_view_permission(self, request, obj=None):
        return self._can_handle_support(request)

    def has_change_permission(self, request, obj=None):
        # Оператор может отвечать пользователям и менять статус тикета.
        return self._can_handle_support(request)

    def has_add_permission(self, request):
        # Обращения создаются только с сайта, не вручную
        return False

    def has_delete_permission(self, request, obj=None):
        return self._is_project_admin(request)

    def save_model(self, request, obj, form, change):
        # При сохранении ответа фиксируем, кто и когда ответил.
        if "admin_reply" in form.changed_data and obj.admin_reply:
            from django.utils import timezone

            obj.admin_replied_at = timezone.now()
            obj.admin_replied_by = request.user
            # Добавляем сообщение в историю тикета
            SupportMessage.objects.create(
                request=obj,
                author=request.user,
                text=obj.admin_reply,
            )

        # При закрытии фиксируем кто/когда закрыл.
        if "is_resolved" in form.changed_data:
            from django.utils import timezone

            if obj.is_resolved:
                if not obj.resolved_at:
                    obj.resolved_at = timezone.now()
                if not obj.resolved_by:
                    obj.resolved_by = request.user
            else:
                obj.resolved_at = None
                obj.resolved_by = None
        super().save_model(request, obj, form, change)


@admin.register(SupportFAQ)
class SupportFAQAdmin(admin.ModelAdmin):
    list_display = ("question", "sort_order", "is_active")
    list_editable = ("sort_order", "is_active")
    search_fields = ("question", "answer")

    def _is_project_admin(self, request) -> bool:
        if request.user.is_superuser:
            return True
        try:
            profile = request.user.profile  # type: ignore[attr-defined]
        except Exception:
            return False
        return bool(profile.is_project_admin)

    def has_view_permission(self, request, obj=None):
        return self._is_project_admin(request)

    def has_change_permission(self, request, obj=None):
        return self._is_project_admin(request)

    def has_add_permission(self, request):
        return self._is_project_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self._is_project_admin(request)
