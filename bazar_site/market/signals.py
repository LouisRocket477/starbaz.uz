"""Сигналы приложения market."""

from django.db.models.signals import post_migrate, post_save
from django.dispatch import receiver

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from .models import Listing, ListingPriceHistory, UserProfile


GROUP_PROJECT_ADMIN = "Project Admin"
GROUP_OPERATOR = "Operator"


def _ensure_group(name: str) -> Group:
    group, _ = Group.objects.get_or_create(name=name)
    return group


def _get_perm(app_label: str, model: str, action: str) -> Permission | None:
    try:
        ct = ContentType.objects.get(app_label=app_label, model=model)
        return Permission.objects.get(content_type=ct, codename=f"{action}_{model}")
    except Exception:
        return None


@receiver(post_migrate)
def ensure_admin_groups(sender, **kwargs):
    """
    Создаём группы и настраиваем права:
    - Operator: поддержка + выдача премиума/статусов в UserProfile
    - Project Admin: расширенные права на все модели market + просмотр пользователей
    """
    # Ограничиваемся нашим приложением.
    try:
        app_label = getattr(sender, "label", "") or ""
    except Exception:
        app_label = ""
    if app_label != "market":
        return

    op = _ensure_group(GROUP_OPERATOR)
    pa = _ensure_group(GROUP_PROJECT_ADMIN)

    # Operator permissions
    perms = []
    perms += [
        _get_perm("market", "supportrequest", "view"),
        _get_perm("market", "supportrequest", "change"),
        _get_perm("market", "supportmessage", "view"),
        _get_perm("market", "supportmessage", "add"),
        _get_perm("market", "supportmessage", "change"),
        _get_perm("market", "userprofile", "view"),
        _get_perm("market", "userprofile", "change"),
    ]

    # user view (auth.User or custom)
    user_model = get_user_model()
    perms += [
        _get_perm(user_model._meta.app_label, user_model._meta.model_name, "view"),
        _get_perm(user_model._meta.app_label, user_model._meta.model_name, "change"),
    ]

    op.permissions.set([p for p in perms if p is not None])

    # Project admin: все permissions по app_label=market
    pa.permissions.set(Permission.objects.filter(content_type__app_label="market"))


@receiver(post_save, sender=UserProfile)
def sync_profile_roles(sender, instance: UserProfile, **kwargs):
    """
    Синхронизируем флаги в профиле с:
    - is_staff
    - группами Operator / Project Admin
    """
    user = getattr(instance, "user", None)
    if user is None:
        return

    needs_staff = bool(
        getattr(user, "is_superuser", False)
        or instance.is_admin_whitelist
        or instance.is_operator
        or instance.is_project_admin
    )
    if needs_staff and not user.is_staff:
        user.is_staff = True
        user.save(update_fields=["is_staff"])

    try:
        op = Group.objects.filter(name=GROUP_OPERATOR).first()
        pa = Group.objects.filter(name=GROUP_PROJECT_ADMIN).first()
        if op:
            if instance.is_operator:
                user.groups.add(op)
            else:
                user.groups.remove(op)
        if pa:
            if instance.is_project_admin:
                user.groups.add(pa)
            else:
                user.groups.remove(pa)
    except Exception:
        return


@receiver(post_save, sender=Listing)
def record_listing_price_history(sender, instance, created, **kwargs):
    """Записываем историю цены при создании или изменении объявления."""
    update_fields = kwargs.get("update_fields")
    # Пропускаем, если сохраняли только guarantor и т.п.
    if not created and update_fields is not None:
        if "price" not in update_fields and "original_price" not in update_fields:
            return
    price = instance.price
    if price is None:
        return
    last = instance.price_history.order_by("-recorded_at").first()
    if last and last.price == price:
        return
    ListingPriceHistory.objects.create(listing=instance, price=price)
