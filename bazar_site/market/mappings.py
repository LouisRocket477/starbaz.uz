from __future__ import annotations

from .enums import SellerStatusOverride
from .langvars import Lang

"""
Все мэппинги/словарики для статусов, типов и т.п.
Новые соответствия лучше добавлять сюда, а не размазывать по вьюхам.
"""


SELLER_STATUS_BADGE_MAPPING: dict[str, tuple[str, str]] = {
    SellerStatusOverride.BASIC: (Lang.SellerStatus.BASIC, "status-badge-basic"),
    SellerStatusOverride.VERIFIED: (
        Lang.SellerStatus.VERIFIED,
        "status-badge-verified",
    ),
    SellerStatusOverride.SILVER: (
        Lang.SellerStatus.SILVER,
        "status-badge-silver",
    ),
    SellerStatusOverride.GOLD: (Lang.SellerStatus.GOLD, "status-badge-gold"),
    SellerStatusOverride.COSMIC: (
        Lang.SellerStatus.COSMIC,
        "status-badge-cosmic",
    ),
}

DEFAULT_SELLER_STATUS_BADGE: tuple[str, str] = (
    Lang.SellerStatus.BASIC,
    "status-badge-basic",
)

