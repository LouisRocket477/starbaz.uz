from __future__ import annotations

from django.db.models import TextChoices

from .langvars import Lang


class ListingDealType(TextChoices):
    SELL = "sell", Lang.DealType.SELL
    BUY = "buy", Lang.DealType.BUY
    TRADE = "trade", Lang.DealType.TRADE


class ListingStatus(TextChoices):
    ACTIVE = "active", Lang.ListingStatus.ACTIVE
    RESERVED = "reserved", Lang.ListingStatus.RESERVED
    SOLD = "sold", Lang.ListingStatus.SOLD
    HIDDEN = "hidden", Lang.ListingStatus.HIDDEN


class SellerStatusOverride(TextChoices):
    AUTO = "", Lang.SellerStatus.AUTO
    BASIC = "basic", Lang.SellerStatus.BASIC
    VERIFIED = "verified", Lang.SellerStatus.VERIFIED
    SILVER = "silver", Lang.SellerStatus.SILVER
    GOLD = "gold", Lang.SellerStatus.GOLD
    COSMIC = "cosmic", Lang.SellerStatus.COSMIC

