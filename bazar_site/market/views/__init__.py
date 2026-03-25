"""
Вьюхи приложения `market`.

Пакет разбит на модули:
- _helpers — общие хелперы (get_site_settings, is_user_online, статусы продавца)
- account — логин и регистрация
- public — главная, список/деталь объявлений, гаранты, карточка продавца
- listings — мои объявления, создание/редактирование/удаление
- chat — личные чаты и диалоги с продавцом
- profile — профиль пользователя, heartbeat
- errors — обработчики 400, 403, 404, 500
- global_chat — API глобального чата
"""

from ._helpers import (
    _get_site_settings_context,
    get_seller_status,
    get_seller_status_for_profile,
    get_site_settings,
    is_user_online,
)
from .account import account_login_view, account_signup_view
from .chat import (
    conversation_accept_sell_offer,
    conversation_cancel_purchase,
    conversation_complete_barter,
    conversation_complete_deal,
    conversation_detail,
    conversation_list,
    conversation_offer_sell,
    conversation_request_purchase,
    conversation_send_message,
    conversation_submit_review,
    conversation_submit_review_reply,
    conversation_with_seller,
)
from .errors import error_400, error_403, error_404, error_500
from .global_chat import global_chat_api
from .listings import listing_create, listing_delete, listing_edit, my_listings, listing_toggle_status, listing_boost
from .profile import heartbeat, profile_view
from .public import (
    about,
    rules,
    useful_links,
    guarantor_list,
    home,
    home_live_search,
    listing_detail,
    listing_list,
    seller_detail,
    seller_reviews,
)
from ..support.views import support_hub, support_new, support_my, support_faq, support_thanks, support_dispute, premium_options

__all__ = [
    "_get_site_settings_context",
    "account_login_view",
    "account_signup_view",
    "conversation_accept_sell_offer",
    "conversation_cancel_purchase",
    "conversation_complete_barter",
    "conversation_complete_deal",
    "conversation_detail",
    "conversation_list",
    "conversation_offer_sell",
    "conversation_request_purchase",
    "conversation_send_message",
    "conversation_submit_review",
    "conversation_submit_review_reply",
    "conversation_with_seller",
    "error_400",
    "error_403",
    "error_404",
    "error_500",
    "get_seller_status",
    "get_seller_status_for_profile",
    "get_site_settings",
    "global_chat_api",
    "guarantor_list",
    "heartbeat",
    "home",
    "about",
    "rules",
    "useful_links",
    "home_live_search",
    "is_user_online",
    "listing_create",
    "listing_delete",
    "listing_detail",
    "listing_edit",
    "listing_toggle_status",
    "listing_boost",
    "listing_list",
    "my_listings",
    "profile_view",
    "support_hub",
    "support_new",
    "support_my",
    "support_faq",
    "support_dispute",
    "premium_options",
    "support_thanks",
    "seller_detail",
    "seller_reviews",
]
