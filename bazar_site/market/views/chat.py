"""
Личный чат по объявлению и прямые диалоги с продавцом.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.db import transaction
from django.db.models import Q, Count, Max, F
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from datetime import timedelta

from ..enums import ListingDealType, ListingStatus
from ..middleware import ChatFloodControl
from ..models import (
    Conversation,
    DealCompletion,
    Listing,
    Message,
    PurchaseRequest,
    SellerReview,
    UserProfile,
)
from ..templatetags.market_extras import parse_sell_offer_message
from ._helpers import get_site_settings


def _typing_cache_key(conversation_id: int, user_id: int) -> str:
    return f"typing:{conversation_id}:{user_id}"


def _message_to_payload(msg: Message, request_user_id: int):
    profile, _ = UserProfile.objects.get_or_create(user=msg.sender)
    avatar_url = profile.avatar.url if profile.avatar else None
    return {
        "id": msg.id,
        "sender": msg.sender.username,
        "is_me": msg.sender_id == request_user_id,
        "created_at": msg.created_at.strftime("%d.%m.%Y %H:%M"),
        "content": msg.content,
        "image_url": msg.image.url if msg.image else None,
        "avatar_url": avatar_url,
    }


@login_required
def conversation_list(request):
    settings_obj = get_site_settings()
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    conversations = Conversation.objects.filter(
        Q(buyer=request.user) | Q(seller=request.user)
    ).select_related("listing", "buyer", "seller", "buyer__profile", "seller__profile").annotate(
        unread_count=Count(
            "messages",
            filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user),
        ),
        last_message_at=Max("messages__created_at"),
        last_activity=Coalesce(Max("messages__created_at"), F("created_at")),
    ).order_by("-last_activity", "-unread_count", "-created_at")

    support_tickets = []
    can_view_support = bool(user_profile.is_project_admin or user_profile.is_operator or request.user.is_superuser)
    open_support_count = 0
    user_trade_tickets = []
    if can_view_support:
        try:
            from ..support.models import SupportRequest

            support_tickets = list(
                SupportRequest.objects.select_related("author")
                .filter(is_resolved=False)
                .order_by("-created_at")[:25]
            )
            open_support_count = SupportRequest.objects.filter(is_resolved=False).count()
        except Exception:
            support_tickets = []
            open_support_count = 0

    dispute_window_seconds = 60 * 60
    now = timezone.now()
    window_start = now - timedelta(seconds=dispute_window_seconds)

    last_trade_pr = (
        PurchaseRequest.objects.select_related(
            "conversation",
            "conversation__listing",
            "conversation__buyer",
            "conversation__seller",
        )
        .filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
            status=PurchaseRequest.Status.COMPLETED,
            created_at__gte=window_start,
        )
        .order_by("-created_at")
        .first()
    )

    last_trade_ui = None
    if last_trade_pr:
        convo = last_trade_pr.conversation
        other_user = convo.seller if request.user == convo.buyer else convo.buyer
        deadline = last_trade_pr.created_at + timedelta(seconds=dispute_window_seconds)
        remaining = int((deadline - now).total_seconds())
        if remaining < 0:
            remaining = 0

        last_trade_ui = {
            "pr": last_trade_pr,
            "conversation": convo,
            "listing": getattr(convo, "listing", None),
            "other_user": other_user,
            "deadline_iso": deadline.isoformat(),
            "remaining_seconds": remaining,
            "is_open": remaining > 0,
        }

        # Если по этой сделке уже есть тикет — не показываем “Последняя сделка”,
        # а переносим в блок “Обращения”.
        try:
            from ..support.models import SupportRequest

            user_trade_tickets = list(
                SupportRequest.objects.filter(
                    author=request.user,
                    related_purchase_request=last_trade_pr,
                )
                .order_by("-created_at")[:10]
            )
        except Exception:
            user_trade_tickets = []

        if user_trade_tickets:
            last_trade_ui = None

    show_right_panel = bool(can_view_support or last_trade_ui or user_trade_tickets)
    return render(
        request,
        "market/conversation_list.html",
        {
            "site_settings": settings_obj,
            "conversations": conversations,
            "support_tickets": support_tickets,
            "open_support_count": open_support_count,
            "can_view_support": can_view_support,
            "show_right_panel": show_right_panel,
            "dispute_window_seconds": dispute_window_seconds,
            "last_trade_ui": last_trade_ui,
            "user_trade_tickets": user_trade_tickets,
        },
    )


@login_required
def conversation_typing_ping(request, pk: int):
    """
    Пинг от клиента: "я печатаю" в этом диалоге.
    Храним коротко (несколько секунд) в кэше.
    """
    # Разрешаем GET/POST, чтобы работало без CSRF на фронте.
    if request.method not in {"GET", "POST"}:
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    conversation = get_object_or_404(
        Conversation.objects.select_related("buyer", "seller"),
        pk=pk,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return JsonResponse({"error": "forbidden"}, status=403)

    cache.set(_typing_cache_key(conversation.id, request.user.id), True, timeout=6)
    return JsonResponse({"ok": True})


@login_required
def conversation_typing_status(request, pk: int):
    """
    Статус для клиента: печатает ли другой участник (в последние несколько секунд).
    """
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    conversation = get_object_or_404(
        Conversation.objects.select_related("buyer", "seller"),
        pk=pk,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return JsonResponse({"error": "forbidden"}, status=403)

    other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
    is_typing = bool(cache.get(_typing_cache_key(conversation.id, other_user.id)))
    return JsonResponse({"typing": is_typing, "user": other_user.username})


@login_required
def conversation_poll(request, pk: int):
    """
    Агрессивная синхронизация чата без WebSocket:
    клиент запрашивает новые сообщения после after_id.
    """
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    conversation = get_object_or_404(
        Conversation.objects.select_related("buyer", "seller"),
        pk=pk,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return JsonResponse({"error": "forbidden"}, status=403)

    try:
        after_id = int(request.GET.get("after", "0") or 0)
    except (TypeError, ValueError):
        after_id = 0

    qs = conversation.messages.select_related("sender").order_by("id")
    if after_id > 0:
        qs = qs.filter(id__gt=after_id)
    new_messages = list(qs[:50])

    # Если пользователь в открытом диалоге — новые входящие считаем прочитанными.
    if new_messages:
        Message.objects.filter(
            conversation=conversation,
            id__in=[m.id for m in new_messages],
            is_read=False,
        ).exclude(sender=request.user).update(is_read=True)

    payload = [_message_to_payload(m, request.user.id) for m in new_messages]
    last_id = payload[-1]["id"] if payload else after_id
    return JsonResponse({"messages": payload, "last_id": last_id})


@login_required
def nav_status(request):
    """
    Возвращает счётчики для шапки без перезагрузки:
    - непрочитанные личные сообщения
    - открытые тикеты (для админов/операторов)
    """
    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    unread = Message.objects.filter(
        Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
        is_read=False,
    ).exclude(sender=request.user).count()

    unread_last_id = (
        Message.objects.filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
            is_read=False,
        )
        .exclude(sender=request.user)
        .order_by("-id")
        .values_list("id", flat=True)
        .first()
    ) or 0

    open_tickets = 0
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if getattr(profile, "is_project_admin", False) or getattr(profile, "is_operator", False) or request.user.is_superuser:
        try:
            from ..support.models import SupportRequest

            open_tickets = SupportRequest.objects.filter(is_resolved=False).count()
        except Exception:
            open_tickets = 0

    return JsonResponse(
        {
            "unread_chat_count": unread,
            "unread_last_id": int(unread_last_id or 0),
            "open_support_tickets": open_tickets,
        }
    )


@login_required
def conversation_detail(request, pk: int):
    settings_obj = get_site_settings()
    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return redirect("market:conversation_list")

    other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
    other_profile, _ = UserProfile.objects.get_or_create(user=other_user)
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    had_unread = False
    unread_qs = conversation.messages.filter(is_read=False).exclude(sender=request.user)
    if unread_qs.exists():
        had_unread = True
        unread_qs.update(is_read=True)

    messages = conversation.messages.select_related("sender")
    last_message_id = (
        messages.order_by("-id").values_list("id", flat=True).first() or 0
    )
    pending_purchase_requests = []
    if request.user == conversation.seller and conversation.listing:
        pending_purchase_requests = list(
            conversation.purchase_requests.filter(
                status=PurchaseRequest.Status.PENDING
            ).select_related("buyer").order_by("-created_at")
        )

    buyer_listings = []
    if request.user == conversation.buyer:
        buyer_listings = list(
            Listing.objects.filter(
                seller=request.user,
                status=ListingStatus.ACTIVE,
            )
            .exclude(deal_type=ListingDealType.BUY)
            .filter(Q(quantity__isnull=True) | Q(quantity__gt=0), in_stock=True)
            .order_by("-updated_at")[:20]
        )

    pending_sell_offer_messages = []
    if (
        request.user == conversation.seller
        and conversation.listing
        and conversation.listing.deal_type == ListingDealType.BUY
        and conversation.listing.status != ListingStatus.SOLD
    ):
        qs = conversation.messages.filter(content__contains="📤SELL_OFFER")
        # Если уже были завершённые сделки, показываем только предложения,
        # которые пришли ПОСЛЕ последней завершённой сделки,
        # чтобы принятые/отработанные предложения не висели.
        last_completion = conversation.deal_completions.order_by("-completed_at").first()
        if last_completion:
            qs = qs.filter(created_at__gt=last_completion.completed_at)
        pending_sell_offer_messages = list(qs.order_by("-created_at")[:20])

    buyer_has_pending_purchase = (
        request.user == conversation.buyer
        and conversation.listing
        and conversation.purchase_requests.filter(
            buyer=request.user, status=PurchaseRequest.Status.PENDING
        ).exists()
    )

    has_barter_request = False
    if (
        request.user == conversation.seller
        and conversation.listing
        and conversation.listing.barter_allowed
        and conversation.listing.status != ListingStatus.SOLD
    ):
        barter_messages = conversation.messages.filter(
            sender=conversation.buyer,
            content__icontains="Хочу обмен",
        )
        last_completion = conversation.deal_completions.order_by("-completed_at").first()
        if last_completion:
            has_barter_request = barter_messages.filter(
                created_at__gt=last_completion.completed_at
            ).exists()
        else:
            has_barter_request = barter_messages.exists()
    can_complete_barter = has_barter_request

    deal_review_data = None
    if conversation.listing and conversation.deal_completions.exists():
        # Покупатель может оставлять по одному отзыву на каждое завершение сделки
        total_deals = conversation.deal_completions.count()
        review_qs = SellerReview.objects.filter(
            listing=conversation.listing,
            seller=conversation.seller,
            buyer=conversation.buyer,
        )
        review_count = review_qs.count()
        existing_review = review_qs.order_by("-created_at").first()
        can_buyer_leave_review = (
            request.user == conversation.buyer and review_count < total_deals
        )
        deal_review_data = {
            "existing_review": existing_review,
            "can_buyer_leave_review": can_buyer_leave_review,
            "can_seller_reply": (
                request.user == conversation.seller
                and existing_review
                and not existing_review.reply_text
            ),
        }

    page_title = None
    if conversation.listing:
        page_title = f"Чат: {conversation.listing.title[:50]}" if conversation.listing.title else "Чат по объявлению"
    else:
        page_title = f"Личный чат с {other_user.username}"

    return render(
        request,
        "market/conversation_detail.html",
        {
            "site_settings": settings_obj,
            "conversation": conversation,
            "messages": messages,
            "last_message_id": last_message_id,
            "had_unread": had_unread,
            "other_user": other_user,
            "other_profile": other_profile,
            "user_profile": user_profile,
            "pending_purchase_requests": pending_purchase_requests,
            "pending_sell_offer_messages": pending_sell_offer_messages,
            "can_complete_barter": can_complete_barter,
            "deal_review_data": deal_review_data,
            "buyer_listings": buyer_listings,
            "buyer_has_pending_purchase": buyer_has_pending_purchase,
            "page_title": page_title,
        },
    )


@login_required
def conversation_send_message(request, pk: int):
    if request.method != "POST":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    conversation = get_object_or_404(
        Conversation.objects.select_related("buyer", "seller"),
        pk=pk,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return JsonResponse({"error": "forbidden"}, status=403)

    content = request.POST.get("content", "").strip()
    image_file = request.FILES.get("image")
    if not content and not image_file:
        return JsonResponse({"error": "empty"}, status=400)

    if ChatFloodControl.is_blocked(request.user.id, "private"):
        return ChatFloodControl.cooldown_json()

    msg = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        image=image_file,
    )

    profile, _ = UserProfile.objects.get_or_create(user=msg.sender)
    avatar_url = profile.avatar.url if profile.avatar else None

    data = {
        "id": msg.id,
        "sender": msg.sender.username,
        "is_me": msg.sender_id == request.user.id,
        "created_at": msg.created_at.strftime("%d.%m.%Y %H:%M"),
        "content": msg.content,
        "image_url": msg.image.url if msg.image else None,
        "avatar_url": avatar_url,
    }
    return JsonResponse({"message": data}, status=201)


@login_required
def conversation_request_purchase(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.buyer:
        return redirect("market:conversation_detail", pk=pk)

    listing = conversation.listing
    if not listing or not listing.in_stock:
        return redirect("market:conversation_detail", pk=pk)
    if listing.quantity is None:
        if not listing.price or listing.deal_type == ListingDealType.BUY:
            return redirect("market:conversation_detail", pk=pk)
        available = 1
    else:
        available = listing.quantity or 0

    try:
        qty = int(request.POST.get("quantity", "0"))
    except (TypeError, ValueError):
        qty = 0

    if qty < 1 or qty > available:
        return redirect("market:conversation_detail", pk=pk)

    with transaction.atomic():
        Conversation.objects.select_for_update().get(pk=conversation.pk)
        if conversation.purchase_requests.filter(
            buyer=request.user,
            status=PurchaseRequest.Status.PENDING,
        ).exists():
            return redirect("market:conversation_detail", pk=pk)

        PurchaseRequest.objects.create(
            conversation=conversation,
            buyer=request.user,
            quantity=qty,
            status=PurchaseRequest.Status.PENDING,
        )

    try:
        total = listing.price * qty
        total_display = listing._format_decimal(total)
        unit_display = listing._format_decimal(listing.price)
        currency = listing.currency or "AUEC"
    except Exception:
        total_display = str(listing.price or 0)
        unit_display = str(listing.price or 0)
        currency = listing.currency or "AUEC"

    buyer_name = request.user.username
    content = f"🛒PURCHASE\n{buyer_name}\n{qty}\n{unit_display}\n{total_display}\n{currency}"
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_offer_sell(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.buyer:
        return redirect("market:conversation_detail", pk=pk)

    listing_id = request.POST.get("listing_id")
    if not listing_id:
        return redirect("market:conversation_detail", pk=pk)

    try:
        listing = Listing.objects.get(
            pk=int(listing_id),
            seller=request.user,
            status=ListingStatus.ACTIVE,
        )
    except (ValueError, Listing.DoesNotExist):
        return redirect("market:conversation_detail", pk=pk)

    if listing.deal_type == ListingDealType.BUY:
        return redirect("market:conversation_detail", pk=pk)

    # Определяем, сколько единиц товара реально можно предложить
    if listing.quantity is None:
        seller_available = 1
    else:
        seller_available = listing.quantity or 0
    if not seller_available:
        return redirect("market:conversation_detail", pk=pk)

    try:
        qty_raw = request.POST.get("quantity", "1")
        qty = int(qty_raw)
    except (TypeError, ValueError):
        qty = 1
    if qty < 1:
        qty = 1
    if seller_available and qty > seller_available:
        qty = seller_available

    # Удаляем старые предложения по этому же лоту от этого же пользователя,
    # чтобы в карточке "Предложения о продаже" не было дублей.
    existing_qs = conversation.messages.filter(
        sender=request.user,
        content__contains="📤SELL_OFFER",
    )
    for msg in existing_qs:
        offer = parse_sell_offer_message(msg.content)
        try:
            offer_listing_pk = int(offer.get("listing_pk")) if offer else None
        except (TypeError, ValueError):
            offer_listing_pk = None
        if offer_listing_pk == listing.pk:
            msg.delete()

    try:
        price_display = listing._format_decimal(listing.price)
        currency = listing.currency or "AUEC"
    except Exception:
        price_display = str(listing.price or 0)
        currency = listing.currency or "AUEC"

    seller_name = request.user.username
    # Добавляем количество как отдельную строку, чтобы продавец видел, сколько вы предлагаете продать
    content = (
        f"📤SELL_OFFER\n"
        f"{seller_name}\n"
        f"{listing.pk}\n"
        f"{listing.title}\n"
        f"{price_display}\n"
        f"{currency}\n"
        f"{qty}"
    )
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_cancel_purchase(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.seller:
        return redirect("market:conversation_detail", pk=pk)

    req_id = request.POST.get("purchase_request_id")
    if not req_id:
        return redirect("market:conversation_detail", pk=pk)

    try:
        purchase_request = conversation.purchase_requests.get(
            pk=int(req_id),
            status=PurchaseRequest.Status.PENDING,
        )
    except (ValueError, PurchaseRequest.DoesNotExist):
        return redirect("market:conversation_detail", pk=pk)

    purchase_request.status = PurchaseRequest.Status.CANCELLED
    purchase_request.save(update_fields=["status"])

    content = (
        "❌ Заказ отменён\n\n"
        f"Продавец отменил заказ на {purchase_request.quantity} шт.\n"
        "Причина: товара нет в наличии"
    )
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_accept_sell_offer(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.seller:
        return redirect("market:conversation_detail", pk=pk)

    listing = conversation.listing
    # Работает только для объявлений "Покупаю"
    if not listing or listing.deal_type != ListingDealType.BUY:
        return redirect("market:conversation_detail", pk=pk)

    # Сколько ещё единиц товара хочет купить инициатор
    if listing.quantity is None:
        available = 1
    else:
        available = listing.quantity or 0
    if available <= 0 or listing.status == ListingStatus.SOLD:
        return redirect("market:conversation_detail", pk=pk)

    message_id = request.POST.get("message_id")
    if not message_id:
        return redirect("market:conversation_detail", pk=pk)

    try:
        msg = conversation.messages.get(pk=int(message_id))
    except (ValueError, Message.DoesNotExist):
        return redirect("market:conversation_detail", pk=pk)

    offer = parse_sell_offer_message(msg.content)
    if not offer:
        return redirect("market:conversation_detail", pk=pk)

    # Находим объявление продавца (того, кто предлагает свой товар)
    offered_listing = None
    try:
        offered_listing_pk = int(offer.get("listing_pk"))
        offered_listing = Listing.objects.select_for_update().get(
            pk=offered_listing_pk,
            seller=conversation.buyer,
        )
    except (TypeError, ValueError, Listing.DoesNotExist):
        offered_listing = None

    # Сколько единиц реально можем провести в сделке:
    # 1) не больше, чем ещё хочет купить инициатор;
    # 2) не больше, чем есть у продавца;
    # 3) не больше, чем было указано в предложении.
    try:
        qty_requested = int(offer.get("qty") or 1)
    except (TypeError, ValueError):
        qty_requested = 1
    if qty_requested < 1:
        qty_requested = 1
    seller_available = 1
    if offered_listing and offered_listing.quantity is not None:
        seller_available = offered_listing.quantity or 0
    qty = min(available, seller_available, qty_requested)
    if qty <= 0:
        return redirect("market:conversation_detail", pk=pk)

    DealCompletion.objects.create(
        conversation=conversation,
        quantity_sold=qty,
        completed_by=request.user,
    )

    # Уменьшаем желаемое количество в объявлении "Покупаю"
    if listing.quantity is None:
        # Если количество не задано, считаем, что это разовая покупка
        listing.quantity = 0
        listing.in_stock = False
        listing.status = ListingStatus.SOLD
    else:
        listing.quantity = max(0, available - qty)
        if listing.quantity == 0:
            listing.in_stock = False
            listing.status = ListingStatus.SOLD
    listing.save(update_fields=["quantity", "in_stock", "status", "updated_at"])

    # И уменьшаем количество товара у продавца (его собственное объявление)
    if offered_listing:
        if offered_listing.quantity is None:
            # Если количество не указано — считаем единичной позицией
            offered_listing.quantity = 0
            offered_listing.in_stock = False
            offered_listing.status = ListingStatus.SOLD
        else:
            offered_listing.quantity = max(0, seller_available - qty)
            if offered_listing.quantity == 0:
                offered_listing.in_stock = False
                offered_listing.status = ListingStatus.SOLD
        offered_listing.save(update_fields=["quantity", "in_stock", "status", "updated_at"])

    buyer_name = conversation.buyer.username

    from decimal import Decimal, InvalidOperation

    # Считаем итоговую сумму сделки и возможную доплату относительно цены объявления "Покупаю".
    try:
        # Цена за 1 шт. в предложении продавца
        if offered_listing and offered_listing.price is not None:
            offer_price = Decimal(offered_listing.price)
            currency = offered_listing.currency or "AUEC"
        else:
            raw_price = str(offer.get("price") or "0").replace(" ", "").replace(",", ".")
            try:
                offer_price = Decimal(raw_price)
            except (InvalidOperation, TypeError):
                offer_price = Decimal("0")
            currency = offer.get("currency", "AUEC")

        total_val = offer_price * Decimal(qty)
        # Форматируем через helper объявления, если можем
        total_display = offered_listing._format_decimal(total_val) if offered_listing else str(total_val)
    except Exception:
        total_display = offer.get("price", "0")
        currency = offer.get("currency", "AUEC")

    # Считаем разницу с ценой, указанной в объявлении "Покупаю"
    diff_total_display = ""
    payer_name = ""
    try:
        if listing.price is not None and offered_listing and offered_listing.price is not None:
            base_price = Decimal(listing.price)
            offer_price_dec = Decimal(offered_listing.price)
            if listing.currency == offered_listing.currency:
                diff_per_unit = offer_price_dec - base_price
                if diff_per_unit != 0:
                    diff_total_val = abs(diff_per_unit) * Decimal(qty)
                    diff_total_display = offered_listing._format_decimal(diff_total_val)
                    # Кто должен доплатить:
                    # если товар продавца дороже (diff_per_unit > 0) — инициатор "Покупаю" (seller объявления)
                    # если дешевле — продавец, предложивший свой товар (conversation.buyer)
                    if diff_per_unit > 0:
                        payer_name = conversation.seller.username
                    else:
                        payer_name = conversation.buyer.username
    except Exception:
        diff_total_display = ""
        payer_name = ""

    remaining = listing.quantity or 0
    if diff_total_display and payer_name:
        content = (
            f"✅DEAL\n{buyer_name}\n{qty}\n{total_display}\n{currency}\n{remaining}\n"
            f"{diff_total_display}\n{payer_name}"
        )
    else:
        content = f"✅DEAL\n{buyer_name}\n{qty}\n{total_display}\n{currency}\n{remaining}"
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_complete_barter(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.seller:
        return redirect("market:conversation_detail", pk=pk)

    listing = conversation.listing
    if not listing or not listing.barter_allowed or listing.status == ListingStatus.SOLD:
        return redirect("market:conversation_detail", pk=pk)

    DealCompletion.objects.create(
        conversation=conversation,
        quantity_sold=1,
        completed_by=request.user,
    )

    qty = listing.quantity
    if qty is None:
        listing.quantity = 0
        listing.in_stock = False
        listing.status = ListingStatus.SOLD
        listing.save(update_fields=["quantity", "in_stock", "status", "updated_at"])
    else:
        listing.quantity = max(0, qty - 1)
        if listing.quantity <= 0:
            listing.in_stock = False
            listing.status = ListingStatus.SOLD
            listing.quantity = 0
        listing.save(update_fields=["quantity", "in_stock", "status", "updated_at"])

    buyer_name = conversation.buyer.username
    listing_title = (listing.title or "")[:50]
    content = f"🔄 Обмен завершён\n\nСделка по «{listing_title}» с {buyer_name} успешно завершена."
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_complete_deal(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.seller:
        return redirect("market:conversation_detail", pk=pk)

    listing = conversation.listing
    if not listing:
        return redirect("market:conversation_detail", pk=pk)
    if listing.quantity is None:
        available = 1
    else:
        available = listing.quantity or 0

    req_id = request.POST.get("purchase_request_id")
    qty = 0
    purchase_request = None
    if req_id:
        try:
            purchase_request = conversation.purchase_requests.get(
                pk=int(req_id),
                status=PurchaseRequest.Status.PENDING,
            )
            qty = int(request.POST.get("quantity", purchase_request.quantity))
        except (ValueError, PurchaseRequest.DoesNotExist):
            pass

    if not qty:
        try:
            qty = int(request.POST.get("quantity", "0"))
        except (TypeError, ValueError):
            qty = 0

    if qty < 1 or qty > available:
        return redirect("market:conversation_detail", pk=pk)

    if purchase_request:
        purchase_request.status = PurchaseRequest.Status.COMPLETED
        purchase_request.save(update_fields=["status"])

    DealCompletion.objects.create(
        conversation=conversation,
        quantity_sold=qty,
        completed_by=request.user,
    )

    listing.quantity = available - qty
    if listing.quantity == 0:
        listing.in_stock = False
        listing.status = ListingStatus.SOLD
    listing.save(update_fields=["quantity", "in_stock", "status", "updated_at"])

    buyer_name = conversation.buyer.username
    try:
        total = listing.price * qty
        total_display = listing._format_decimal(total)
        currency = listing.currency or "AUEC"
    except Exception:
        total_display = str(listing.price or 0)
        currency = listing.currency or "AUEC"
    remaining = listing.quantity or 0
    content = f"✅DEAL\n{buyer_name}\n{qty}\n{total_display}\n{currency}\n{remaining}"
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_submit_review(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.buyer:
        return redirect("market:conversation_detail", pk=pk)

    if not conversation.listing or not conversation.deal_completions.exists():
        return redirect("market:conversation_detail", pk=pk)

    # Покупатель может оставить по одному отзыву за каждую завершённую сделку
    total_deals = conversation.deal_completions.count()
    existing_count = SellerReview.objects.filter(
        listing=conversation.listing,
        seller=conversation.seller,
        buyer=conversation.buyer,
    ).count()
    if existing_count >= total_deals:
        return redirect("market:conversation_detail", pk=pk)

    rating_raw = request.POST.get("rating", "").strip()
    text = (request.POST.get("text") or "").strip()

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        rating = 0

    # Оценка обязательна, текст — по желанию (если есть, хотя бы 5 символов)
    if rating not in (1, 2, 3, 4, 5) or (text and len(text) < 5):
        return redirect("market:conversation_detail", pk=pk)

    SellerReview.objects.create(
        listing=conversation.listing,
        seller=conversation.seller,
        buyer=request.user,
        rating=rating,
        text=text,
    )

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_submit_review_reply(request, pk: int):
    if request.method != "POST":
        return redirect("market:conversation_detail", pk=pk)

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=pk,
    )
    if request.user != conversation.seller:
        return redirect("market:conversation_detail", pk=pk)

    review = (
        SellerReview.objects.filter(
            listing=conversation.listing,
            seller=conversation.seller,
            buyer=conversation.buyer,
        )
        .order_by("-created_at")
        .first()
    )
    if not review:
        return redirect("market:conversation_detail", pk=pk)

    if review.reply_text:
        return redirect("market:conversation_detail", pk=pk)

    reply_text = request.POST.get("reply_text", "").strip()
    if not reply_text or len(reply_text) < 5:
        return redirect("market:conversation_detail", pk=pk)

    review.reply_text = reply_text
    review.reply_created_at = timezone.now()
    review.save(update_fields=["reply_text", "reply_created_at"])

    return redirect("market:conversation_detail", pk=pk)


@login_required
def conversation_with_seller(request, user_id: int):
    other_user = get_object_or_404(get_user_model(), pk=user_id)
    if other_user == request.user:
        return redirect("market:conversation_list")

    seller = other_user
    buyer = request.user
    conversation = Conversation.objects.filter(
        listing__isnull=True,
        buyer=buyer,
        seller=seller,
    ).first()
    if not conversation:
        conversation = Conversation.objects.create(
            listing=None,
            buyer=buyer,
            seller=seller,
        )
    return redirect("market:conversation_detail", pk=conversation.pk)
