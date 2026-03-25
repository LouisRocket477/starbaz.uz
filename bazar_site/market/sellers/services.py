from __future__ import annotations

from datetime import timedelta
from typing import Optional, Tuple

from django.utils import timezone

from ..enums import SellerStatusOverride
from ..mappings import DEFAULT_SELLER_STATUS_BADGE, SELLER_STATUS_BADGE_MAPPING
from ..models import UserProfile


class SellerStatusService:
    """Вся логика расчёта статуса продавца и CSS‑класса."""

    @staticmethod
    def for_profile(
        profile,
        avg_rating_rounded: int,
        orders_count: int,
    ) -> Tuple[Optional[str], str]:
        # Явный оверрайд статуса админом
        if profile and profile.seller_status_override:
            badge = SELLER_STATUS_BADGE_MAPPING.get(
                profile.seller_status_override,
                DEFAULT_SELLER_STATUS_BADGE,
            )
            # Если админ вручную зафиксировал статус «Проверенный»,
            # и бонус ещё не выдавался — выдаём единоразово +5 очков.
            if (
                profile.seller_status_override == SellerStatusOverride.VERIFIED
                and not profile.verified_bonus_given
            ):
                profile.premium_boost_credits = (profile.premium_boost_credits or 0) + 5
                profile.verified_bonus_given = True
                profile.save(update_fields=["premium_boost_credits", "verified_bonus_given"])
            return badge

        if orders_count < 10 or avg_rating_rounded < 5:
            return DEFAULT_SELLER_STATUS_BADGE

        if 10 <= orders_count < 50:
            # Автоматический статус «Проверенный»: один раз даём +5 очков поднятия.
            if profile and not profile.verified_bonus_given:
                profile.premium_boost_credits = (profile.premium_boost_credits or 0) + 5
                profile.verified_bonus_given = True
                profile.save(update_fields=["premium_boost_credits", "verified_bonus_given"])
            return SELLER_STATUS_BADGE_MAPPING[SellerStatusOverride.VERIFIED]
        if 50 <= orders_count < 100:
            return SELLER_STATUS_BADGE_MAPPING[SellerStatusOverride.SILVER]
        if 100 <= orders_count < 200:
            return SELLER_STATUS_BADGE_MAPPING[SellerStatusOverride.GOLD]

        return SELLER_STATUS_BADGE_MAPPING[SellerStatusOverride.COSMIC]

    @staticmethod
    def for_stats(
        avg_rating_rounded: int,
        orders_count: int,
    ) -> Tuple[Optional[str], str]:
        """Упрощённый вариант, когда профиля нет."""
        return SellerStatusService.for_profile(None, avg_rating_rounded, orders_count)


def is_user_online(profile: Optional[UserProfile]) -> bool:
    """Проверяет, был ли пользователь онлайн в последние 5 минут (по last_seen)."""
    if not profile or not profile.last_seen:
        return False
    return profile.last_seen >= timezone.now() - timedelta(minutes=5)

