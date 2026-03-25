"""
Публичные страницы: главная, список/деталь объявления, гаранты, карточка продавца.
"""

from collections import defaultdict
from datetime import timedelta
from decimal import Decimal

from django.db.models import (
    Case,
    Count,
    Exists,
    F,
    Max,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    BooleanField,
    IntegerField,
    When,
    Avg,
)
from django.contrib.auth import get_user_model
from django.db.models.functions import TruncDate
from django.shortcuts import get_object_or_404, redirect, render
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone

from ..enums import ListingDealType, ListingStatus
from ..langvars import Lang
from ..models import (
    Banner,
    Category,
    Conversation,
    DealCompletion,
    Listing,
    ListingImage,
    ListingPriceHistory,
    ListingVideo,
    Message,
    NewsItem,
    PurchaseRequest,
    SellerReview,
    UsefulLink,
    UserProfile,
)
from ._helpers import get_site_settings, get_seller_status_for_profile, is_user_online


def guarantor_list(request):
    """Страница со списком гарантов, которых админ отметил в профиле."""
    settings_obj = get_site_settings()
    guarantor_qs = (
        UserProfile.objects.filter(is_guarantor=True)
        .select_related("user")
        .order_by("-guarantor_priority", "user__username")
    )
    for profile in guarantor_qs:
        user = profile.user
        profile.is_online_flag = is_user_online(profile)
        reviews_qs = SellerReview.objects.filter(seller=user)
        avg_rating = reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0
        profile.avg_rating = avg_rating
        profile.avg_rating_rounded = int(round(avg_rating)) if avg_rating else 0
        profile.likes_count = reviews_qs.filter(rating__gte=4).count()
        profile.dislikes_count = reviews_qs.filter(rating__lte=2).count()
        profile.orders_count = Conversation.objects.filter(seller=user).count()
        status, status_class = get_seller_status_for_profile(
            profile, profile.avg_rating_rounded, profile.orders_count
        )
        profile.seller_status = status
        profile.seller_status_class = status_class

    context = {
        "site_settings": settings_obj,
        "guarantors": guarantor_qs,
        "page_title": "Гаранты StarBaz",
        "meta_description": "Список гарантов StarBaz: проверенные посредники для безопасных сделок между игроками.",
        "meta_keywords": "гарант, гаранты, безопасная сделка, посредник, StarBaz, Star Citizen",
    }
    return render(request, "market/guarantors.html", context)


def about(request):
    """Статическая страница «О нас»."""
    settings_obj = get_site_settings()
    return render(
        request,
        "market/about.html",
        {
            "site_settings": settings_obj,
            "page_title": "О площадке StarBaz",
            "meta_description": "StarBaz — площадка для объявлений, сделок и общения игроков. Узнайте, как работает сервис и какие возможности доступны пользователям.",
            "meta_keywords": "StarBaz, о нас, объявления, торговая площадка, Star Citizen",
        },
    )


def rules(request):
    """Статическая страница с правилами проекта."""
    settings_obj = get_site_settings()
    return render(
        request,
        "market/rules.html",
        {
            "site_settings": settings_obj,
            "page_title": "Правила проекта StarBaz",
            "meta_description": "Правила StarBaz: требования к публикациям, общению, сделкам и обращению в поддержку. Пожалуйста, ознакомьтесь перед использованием сайта.",
            "meta_keywords": "StarBaz, правила, политика, поддержка, сделки, объявления",
        },
    )


def useful_links(request):
    """Полезные ссылки по Star Citizen / RSI."""
    settings_obj = get_site_settings()
    links = UsefulLink.objects.filter(is_active=True).order_by("sort_order", "id")
    return render(
        request,
        "market/useful_links.html",
        {
            "site_settings": settings_obj,
            "page_title": "Полезные ссылки",
            "links": links,
            "meta_description": "Подборка полезных сервисов и баз данных для Star Citizen: корабли, торговля, ресурсы, калькуляторы DPS, статусы серверов и другое.",
            "meta_keywords": "Star Citizen, RSI, корабли, торговля, ресурсы, DPS калькулятор, Erkul, SC trade, SCMDB",
        },
    )


def home(request):
    settings_obj = get_site_settings()
    categories = Category.objects.filter(is_active=True, parent__isnull=True)
    total_listings = Listing.objects.filter(status=ListingStatus.ACTIVE).count()
    guarantor_count = UserProfile.objects.filter(is_guarantor=True).count()
    now = timezone.now()
    cutoff = now - timedelta(minutes=5)
    total_deals = Listing.objects.filter(status=ListingStatus.SOLD).count()
    online_count = UserProfile.objects.filter(last_seen__gte=cutoff).count()

    seller_avg_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(avg=Avg("rating"))
        .values("avg")[:1]
    )
    seller_reviews_count_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    seller_listings_count_subquery = (
        Listing.objects.filter(seller=OuterRef("seller"), status=ListingStatus.ACTIVE)
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    profile_last_seen_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("last_seen")[:1]
    profile_is_guarantor_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("is_guarantor")[:1]

    listings_qs = (
        Listing.objects.filter(status=ListingStatus.ACTIVE)
        .select_related("category", "seller", "guarantor")
        .annotate(
            seller_avg_rating=Subquery(seller_avg_subquery),
            seller_reviews_count=Subquery(seller_reviews_count_subquery),
            seller_listings_count=Subquery(seller_listings_count_subquery),
            seller_last_seen=Subquery(profile_last_seen_subquery),
            seller_is_guarantor=Subquery(profile_is_guarantor_subquery),
            seller_is_online=Case(
                When(
                    seller_last_seen__gte=cutoff,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            boost_priority=Case(
                When(boosted_until__gte=now, then=0),
                default=1,
                output_field=IntegerField(),
            ),
        )
    )
    listings = listings_qs.order_by("boost_priority", "-boosted_until", "-created_at")[:20]
    banners = Banner.objects.filter(is_active=True, show_in_hero=True)
    side_banners = Banner.objects.filter(is_active=True, show_under_categories=True)
    news_items = NewsItem.objects.filter(is_active=True)[:4]
    return render(
        request,
        "market/home.html",
        {
            "site_settings": settings_obj,
            "categories": categories,
            "listings": listings,
            "banners": banners,
            "side_banners": side_banners,
            "news_items": news_items,
            "total_listings": total_listings,
            "guarantor_count": guarantor_count,
            "total_deals": total_deals,
            "online_count": online_count,
            "page_title": settings_obj.seo_meta_title or settings_obj.name,
            "meta_description": settings_obj.seo_meta_description,
            "meta_keywords": settings_obj.seo_meta_keywords,
        },
    )


def home_live_search(request):
    """Живой поиск объявлений на главной странице, возвращает HTML‑сетку карточек."""
    if request.method != "GET":
        return JsonResponse({"error": "Method not allowed"}, status=405)

    query = (request.GET.get("q") or "").strip()
    now = timezone.now()
    cutoff = now - timedelta(minutes=5)

    seller_avg_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(avg=Avg("rating"))
        .values("avg")[:1]
    )
    seller_reviews_count_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    seller_listings_count_subquery = (
        Listing.objects.filter(seller=OuterRef("seller"), status=ListingStatus.ACTIVE)
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    profile_last_seen_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("last_seen")[:1]
    profile_is_guarantor_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("is_guarantor")[:1]

    qs = (
        Listing.objects.filter(status=ListingStatus.ACTIVE)
        .select_related("category", "seller", "guarantor")
        .annotate(
            seller_avg_rating=Subquery(seller_avg_subquery),
            seller_reviews_count=Subquery(seller_reviews_count_subquery),
            seller_listings_count=Subquery(seller_listings_count_subquery),
            seller_last_seen=Subquery(profile_last_seen_subquery),
            seller_is_guarantor=Subquery(profile_is_guarantor_subquery),
            seller_is_online=Case(
                When(
                    seller_last_seen__gte=cutoff,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
            boost_priority=Case(
                When(boosted_until__gte=now, then=0),
                default=1,
                output_field=IntegerField(),
            ),
        )
    )
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(description__icontains=query))

    listings = qs.order_by("boost_priority", "-boosted_until", "-created_at")[:20]
    html = render_to_string(
        "market/_home_listings_grid.html",
        {"listings": listings},
        request=request,
    )
    return JsonResponse({"html": html})


def listing_list(request):
    settings_obj = get_site_settings()
    categories = (
        Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("sort_order", "name")
    )
    seller_avg_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(avg=Avg("rating"))
        .values("avg")[:1]
    )
    seller_reviews_count_subquery = (
        SellerReview.objects.filter(seller=OuterRef("seller"))
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    seller_listings_count_subquery = (
        Listing.objects.filter(seller=OuterRef("seller"), status=ListingStatus.ACTIVE)
        .values("seller")
        .annotate(c=Count("id"))
        .values("c")[:1]
    )
    profile_last_seen_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("last_seen")[:1]
    profile_is_guarantor_subquery = UserProfile.objects.filter(
        user=OuterRef("seller")
    ).values("is_guarantor")[:1]

    now = timezone.now()
    cutoff = now - timedelta(minutes=5)
    qs = (
        Listing.objects.filter(status=ListingStatus.ACTIVE)
        .select_related("category", "seller", "guarantor")
        .annotate(
            seller_avg_rating=Subquery(seller_avg_subquery),
            seller_reviews_count=Subquery(seller_reviews_count_subquery),
            seller_listings_count=Subquery(seller_listings_count_subquery),
            seller_last_seen=Subquery(profile_last_seen_subquery),
            seller_is_guarantor=Subquery(profile_is_guarantor_subquery),
            seller_is_online=Case(
                When(
                    seller_last_seen__gte=cutoff,
                    then=Value(True),
                ),
                default=Value(False),
                output_field=BooleanField(),
            ),
        )
    )

    category_id = request.GET.get("category")
    if category_id:
        qs = qs.filter(category_id=category_id)
    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    sort = request.GET.get("sort", "new")
    # boost_priority: 0 — активное поднятие в топ, 1 — обычные объявления
    qs = qs.annotate(
        boost_priority=Case(
            When(boosted_until__gte=now, then=0),
            default=1,
            output_field=IntegerField(),
        )
    )

    if sort == "price_asc":
        listings = qs.order_by("boost_priority", "-boosted_until", "price", "-created_at")
    elif sort == "price_desc":
        listings = qs.order_by("boost_priority", "-boosted_until", "-price", "-created_at")
    elif sort == "rating":
        listings = qs.order_by(
            "boost_priority",
            "-boosted_until",
            "-seller_avg_rating",
            "-created_at",
        )
    elif sort == "title":
        listings = qs.order_by("boost_priority", "-boosted_until", "title", "-created_at")
    else:
        sort = "new"
        listings = qs.order_by("boost_priority", "-boosted_until", "-created_at")

    page_title = Lang.ListingPage.TITLE_ALL
    meta_description = "Актуальные объявления StarBaz: покупки, продажи и обмены. Фильтры по категориям, поиск и сортировка."
    meta_keywords = settings_obj.seo_meta_keywords or ""
    if category_id:
        current_category = Category.objects.filter(pk=category_id).first()
        if current_category:
            page_title = Lang.ListingPage.TITLE_BY_CATEGORY.format(
                category_name=current_category.name
            )
            meta_description = f"Объявления в категории «{current_category.name}» на StarBaz: покупки, продажи и обмены. Найдите нужный товар или услугу."
            meta_keywords = (meta_keywords + f", {current_category.name}").strip(", ")
    if q:
        meta_description = f"Поиск по объявлениям StarBaz: «{q}». Смотрите предложения продавцов и покупателей, сравнивайте условия."
        meta_keywords = (meta_keywords + f", {q}").strip(", ")

    return render(
        request,
        "market/listing_list.html",
        {
            "site_settings": settings_obj,
            "categories": categories,
            "listings": listings,
            "current_category": category_id,
            "search_query": q,
            "current_sort": sort,
            "page_title": page_title,
            "meta_description": meta_description,
            "meta_keywords": meta_keywords,
        },
    )


def listing_detail(request, pk: int):
    settings_obj = get_site_settings()
    listing = get_object_or_404(
        Listing.objects.select_related("category", "seller")
        .prefetch_related("images", "price_history"),
        pk=pk,
    )
    if not request.user.is_authenticated or request.user != listing.seller:
        Listing.objects.filter(pk=listing.pk).update(views=F("views") + 1)
        listing.refresh_from_db()
    seller_profile, _ = UserProfile.objects.get_or_create(user=listing.seller)
    user_profile = None
    is_user_guarantor = False
    if request.user.is_authenticated:
        user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
        is_user_guarantor = bool(user_profile.is_guarantor)
    conversation = None
    messages = None
    user_review = None

    if request.method == "POST" and is_user_guarantor:
        action = request.POST.get("action")
        if action == "set_guarantor":
            if listing.guarantor is None or listing.guarantor == request.user:
                listing.guarantor = request.user
                listing.save(update_fields=["guarantor"])
            return redirect("market:listing_detail", pk=listing.pk)
        elif action == "unset_guarantor":
            if listing.guarantor == request.user:
                listing.guarantor = None
                listing.save(update_fields=["guarantor"])
            return redirect("market:listing_detail", pk=listing.pk)

    can_leave_review = False
    if request.user.is_authenticated and request.user != listing.seller:
        conversation, _ = Conversation.objects.get_or_create(
            listing=listing,
            buyer=request.user,
            seller=listing.seller,
        )
        messages = conversation.messages.select_related("sender")
        user_review = SellerReview.objects.filter(
            listing=listing, seller=listing.seller, buyer=request.user
        ).first()
        can_leave_review = conversation.deal_completions.exists()

        if request.method == "POST":
            action = request.POST.get("action")
            if action == "chat":
                content = request.POST.get("content", "").strip()
                if content:
                    Message.objects.create(
                        conversation=conversation,
                        sender=request.user,
                        content=content,
                    )
                return redirect("market:listing_detail", pk=listing.pk)
            elif action == "request_barter" and listing.barter_allowed and listing.status != ListingStatus.SOLD and listing.in_stock:
                barter_parts = [cat.name for cat in listing.barter_for.all()]
                if listing.barter_custom:
                    for item in (listing.barter_custom or "").split(","):
                        part = item.strip()
                        if part:
                            barter_parts.append(part)
                barter_str = ", ".join(barter_parts) if barter_parts else "варианты"
                content = f"Хочу обмен! Готов обсудить обмен на ваш «{listing.title}». Можете предложить: {barter_str}."
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content,
                )
                return redirect("market:conversation_detail", pk=conversation.pk)
            elif action == "review" and can_leave_review and not user_review:
                try:
                    rating = int(request.POST.get("rating", "0"))
                except ValueError:
                    rating = 0
                text = request.POST.get("text", "").strip()
                if 1 <= rating <= 5 and text:
                    SellerReview.objects.create(
                        listing=listing,
                        seller=listing.seller,
                        buyer=request.user,
                        rating=rating,
                        text=text,
                    )
                return redirect("market:listing_detail", pk=listing.pk)
            elif action == "offer_sell" and listing.deal_type == ListingDealType.BUY and listing.status != ListingStatus.SOLD:
                content = f"Хочу продать! У меня есть то, что вы ищете («{listing.title}»). Давайте обсудим в чате."
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content,
                )
                return redirect("market:conversation_detail", pk=conversation.pk)

    if request.user.is_authenticated and request.user == listing.seller:
        seller_conversations = (
            Conversation.objects.filter(listing=listing)
            .select_related("buyer")
            .annotate(
                unread_count=Count(
                    "messages",
                    filter=Q(messages__is_read=False) & ~Q(messages__sender=listing.seller),
                ),
                last_message_at=Max("messages__created_at"),
            )
            .filter(unread_count__gt=0)
            .order_by("-last_message_at")
        )
        if request.method == "POST":
            action = request.POST.get("action")
            if action == "close":
                listing.status = ListingStatus.SOLD
                listing.save()
                return redirect("market:listing_detail", pk=listing.pk)
            if action == "republish":
                listing.status = ListingStatus.ACTIVE
                listing.in_stock = True
                qty = request.POST.get("quantity", "").strip()
                if qty:
                    try:
                        listing.quantity = max(0, int(qty))
                    except ValueError:
                        pass
                listing.save(update_fields=["status", "in_stock", "quantity", "updated_at"])
                return redirect("market:listing_detail", pk=listing.pk)
            if action == "reply":
                review_id = request.POST.get("review_id")
                reply_text = request.POST.get("reply_text", "").strip()
                if review_id and reply_text:
                    review = get_object_or_404(
                        SellerReview,
                        pk=review_id,
                        seller=request.user,
                    )
                    if not review.reply_text:
                        review.reply_text = reply_text
                        review.reply_created_at = timezone.now()
                        review.save()
                return redirect("market:listing_detail", pk=listing.pk)
    else:
        seller_conversations = Conversation.objects.none()

    completed_deal_subquery = DealCompletion.objects.filter(
        conversation__listing=OuterRef("listing"),
        conversation__buyer=OuterRef("buyer"),
        conversation__seller=OuterRef("seller"),
    )
    reviews_qs = (
        SellerReview.objects.filter(seller=listing.seller)
        .annotate(has_completed_deal=Exists(completed_deal_subquery))
        .filter(has_completed_deal=True)
        .select_related("buyer")
    )
    base_reviews_qs = reviews_qs
    for review in reviews_qs:
        UserProfile.objects.get_or_create(user=review.buyer)

    avg_rating = base_reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0
    avg_rating_rounded = int(round(avg_rating)) if avg_rating else 0
    likes_count = reviews_qs.filter(rating__gte=4).count()
    dislikes_count = reviews_qs.filter(rating__lte=2).count()
    orders_count = Conversation.objects.filter(seller=listing.seller).count()
    seller_status, seller_status_class = get_seller_status_for_profile(
        seller_profile, avg_rating_rounded, orders_count
    )
    seller_is_online = is_user_online(seller_profile)

    from_date = timezone.now().date() - timedelta(days=30)
    first_word = (listing.title or "").strip().split()[0][:30] if (listing.title or "").strip() else ""
    similar_q = Q(category=listing.category, status__in=(ListingStatus.ACTIVE, ListingStatus.SOLD))
    if first_word:
        similar_q &= (Q(title__iexact=listing.title) | Q(title__istartswith=first_word))
    similar_listing_ids = list(
        Listing.objects.filter(similar_q).values_list("pk", flat=True)
    ) or [listing.pk]

    conv_by_day = (
        Conversation.objects.filter(
            listing_id__in=similar_listing_ids,
            created_at__date__gte=from_date,
        )
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(count=Count("id"))
        .order_by("day")
    )
    orders_by_date = {r["day"]: r["count"] for r in conv_by_day}
    sold_by_day = (
        DealCompletion.objects.filter(
            conversation__listing_id__in=similar_listing_ids,
            completed_at__date__gte=from_date,
        )
        .annotate(day=TruncDate("completed_at"))
        .values("day")
        .annotate(total=Sum("quantity_sold"))
        .order_by("day")
    )
    sold_by_date = {r["day"]: r["total"] for r in sold_by_day}

    all_price_records = list(
        ListingPriceHistory.objects.filter(listing_id__in=similar_listing_ids)
        .order_by("recorded_at")
        .values_list("recorded_at", "price")
    )
    listings_with_history = set(
        ListingPriceHistory.objects.filter(listing_id__in=similar_listing_ids)
        .values_list("listing_id", flat=True)
        .distinct()
    )
    for row in Listing.objects.filter(pk__in=similar_listing_ids).exclude(pk__in=listings_with_history).values("created_at", "price", "original_price"):
        created = row["created_at"]
        if created:
            p = row["price"] or row["original_price"]
            if p is not None:
                all_price_records.append((created, p))

    prices_per_date = defaultdict(list)
    for dt, price in all_price_records:
        if price is not None:
            try:
                prices_per_date[dt.date() if hasattr(dt, "date") else dt].append(float(price))
            except (TypeError, ValueError):
                pass
    price_by_date = {d: sum(p) / len(p) for d, p in prices_per_date.items() if p}
    price_min_by_date = {d: min(p) for d, p in prices_per_date.items() if p}
    price_max_by_date = {d: max(p) for d, p in prices_per_date.items() if p}
    if not price_by_date:
        base_val = float(listing.original_price or listing.price)
        price_by_date = {listing.created_at.date(): base_val}
        price_min_by_date = {listing.created_at.date(): base_val}
        price_max_by_date = {listing.created_at.date(): base_val}
        if listing.updated_at.date() != listing.created_at.date():
            up_val = float(listing.price)
            price_by_date[listing.updated_at.date()] = up_val
            price_min_by_date[listing.updated_at.date()] = up_val
            price_max_by_date[listing.updated_at.date()] = up_val
    sorted_dates = sorted(price_by_date.keys(), reverse=True)

    today = timezone.now().date()
    current_prices = list(
        Listing.objects.filter(pk__in=similar_listing_ids).values_list("price", "original_price")
    )
    current_vals = []
    if current_prices:
        for p, orig in current_prices:
            v = p or orig
            if v is not None:
                current_vals.append(float(v))
    if current_vals:
        price_by_date[today] = sum(current_vals) / len(current_vals)
        price_min_by_date[today] = min(current_vals)
        price_max_by_date[today] = max(current_vals)
        sorted_dates = sorted(price_by_date.keys(), reverse=True)

    chart_labels = []
    chart_orders = []
    chart_sold = []
    chart_prices = []
    chart_prices_min = []
    chart_prices_max = []

    def _get_price_for_day(key_by_date: dict, fallback: float) -> float:
        for d in sorted_dates:
            if d <= day:
                return key_by_date.get(d, fallback)
        return list(key_by_date.values())[0] if key_by_date else fallback

    fallback = float(listing.price or listing.original_price or 0)
    for i in range(30, -1, -1):
        day = timezone.now().date() - timedelta(days=i)
        chart_labels.append(day.strftime("%d.%m"))
        chart_orders.append(orders_by_date.get(day, 0))
        chart_sold.append(sold_by_date.get(day, 0))
        chart_prices.append(_get_price_for_day(price_by_date, fallback))
        chart_prices_min.append(_get_price_for_day(price_min_by_date, fallback))
        chart_prices_max.append(_get_price_for_day(price_max_by_date, fallback))

    viewer_sell_listings = []
    if (
        request.user.is_authenticated
        and request.user != listing.seller
        and listing.deal_type == ListingDealType.BUY
        and listing.status != ListingStatus.SOLD
    ):
        viewer_sell_listings = list(
            Listing.objects.filter(
                seller=request.user,
                status=ListingStatus.ACTIVE,
                deal_type__in=(ListingDealType.SELL, ListingDealType.TRADE),
            ).order_by("-created_at")[:20]
        )

    buyer_has_pending_purchase = False
    if conversation and conversation.listing and request.user == conversation.buyer:
        buyer_has_pending_purchase = conversation.purchase_requests.filter(
            buyer=request.user,
            status=PurchaseRequest.Status.PENDING,
        ).exists()

    deal_label = dict(ListingDealType.choices).get(listing.deal_type, listing.deal_type)
    price_str = ""
    try:
        price_str = f"{listing.price_display} {listing.currency}".strip()
    except Exception:
        price_str = f"{listing.price} {listing.currency}".strip()

    # Авто‑SEO (если SEO-поля не заполнены вручную)
    auto_title_parts = [listing.title, f"— {deal_label}"]
    if price_str:
        auto_title_parts.append(f"· {price_str}")
    auto_title_parts.append("· StarBaz")
    auto_title = " ".join([p for p in auto_title_parts if p]).strip()
    if len(auto_title) > 160:
        auto_title = auto_title[:157].rstrip() + "…"

    auto_desc_parts = []
    if deal_label:
        auto_desc_parts.append(f"{deal_label}: {listing.title}.")
    else:
        auto_desc_parts.append(f"{listing.title}.")
    if price_str:
        auto_desc_parts.append(f"Цена: {price_str}.")
    if listing.category:
        auto_desc_parts.append(f"Категория: {listing.category.name}.")
    if listing.in_stock:
        if listing.quantity:
            auto_desc_parts.append(f"В наличии: {listing.quantity} шт.")
        else:
            auto_desc_parts.append("В наличии.")
    else:
        auto_desc_parts.append("Под заказ / нет в наличии.")
    if (listing.star_system or "").strip():
        auto_desc_parts.append(f"Система: {listing.star_system}.")
    if (listing.location or "").strip():
        auto_desc_parts.append(f"Локация: {listing.location}.")
    if (listing.availability or "").strip():
        auto_desc_parts.append(f"Доступность: {listing.availability}.")
    auto_desc_parts.append("Смотрите детали объявления на StarBaz и свяжитесь с продавцом в чате.")
    auto_description = " ".join(auto_desc_parts).strip()
    if len(auto_description) > 320:
        auto_description = auto_description[:317].rstrip() + "…"

    auto_keywords = settings_obj.seo_meta_keywords or ""
    if listing.category and listing.category.name:
        auto_keywords = (auto_keywords + f", {listing.category.name}").strip(", ")
    if listing.title:
        auto_keywords = (auto_keywords + f", {listing.title}").strip(", ")
    auto_keywords = (auto_keywords + ", Star Citizen, RSI").strip(", ")
    if len(auto_keywords) > 320:
        auto_keywords = auto_keywords[:320]

    og_image = None
    try:
        main_img = listing.main_image
        if main_img and getattr(main_img, "image", None):
            og_image = request.build_absolute_uri(main_img.image.url)
    except Exception:
        og_image = None

    return render(
        request,
        "market/listing_detail.html",
        {
            "site_settings": settings_obj,
            "listing": listing,
            "seller_profile": seller_profile,
            "user_profile": user_profile,
            "conversation": conversation,
            "messages": messages,
            "seller_conversations": seller_conversations,
            "reviews": reviews_qs,
            "user_review": user_review,
            "can_leave_review": can_leave_review,
            "show_review_section": request.user.is_authenticated and request.user != listing.seller and (can_leave_review or user_review),
            "avg_rating": avg_rating,
            "avg_rating_rounded": avg_rating_rounded,
            "likes_count": likes_count,
            "dislikes_count": dislikes_count,
            "orders_count": orders_count,
            "seller_status": seller_status,
            "seller_status_class": seller_status_class,
            "seller_is_online": seller_is_online,
            "is_user_guarantor": is_user_guarantor,
            "chart_labels": chart_labels,
            "chart_orders": chart_orders,
            "chart_sold": chart_sold,
            "chart_prices": chart_prices,
            "chart_prices_min": chart_prices_min,
            "chart_prices_max": chart_prices_max,
            "listing_currency": listing.currency,
            "page_title": (listing.seo_title or "").strip() or auto_title,
            "meta_description": (listing.seo_description or "").strip() or auto_description,
            "meta_keywords": (listing.seo_keywords or "").strip() or auto_keywords,
            "og_type": "website",
            "og_title": (listing.seo_title or "").strip() or auto_title,
            "og_description": (listing.seo_description or "").strip() or auto_description,
            "og_image": og_image,
            "viewer_sell_listings": viewer_sell_listings,
            "buyer_has_pending_purchase": buyer_has_pending_purchase,
        },
    )


def seller_detail(request, user_id: int):
    settings_obj = get_site_settings()
    seller = get_object_or_404(get_user_model(), pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=seller)

    if request.method == "POST" and request.user == seller:
        action = request.POST.get("action")
        if action == "reply":
            review_id = request.POST.get("review_id")
            reply_text = request.POST.get("reply_text", "").strip()
            if review_id and reply_text:
                review = get_object_or_404(
                    SellerReview,
                    pk=review_id,
                    seller=request.user,
                )
                if not review.reply_text:
                    review.reply_text = reply_text
                    review.reply_created_at = timezone.now()
                    review.save()
            return redirect("market:seller_detail", user_id=seller.pk)

    completed_deal_subquery = DealCompletion.objects.filter(
        conversation__listing=OuterRef("listing"),
        conversation__buyer=OuterRef("buyer"),
        conversation__seller=OuterRef("seller"),
    )
    base_reviews_qs = (
        SellerReview.objects.filter(seller=seller)
        .annotate(has_completed_deal=Exists(completed_deal_subquery))
        .filter(has_completed_deal=True)
    )
    reviews_qs = base_reviews_qs.select_related("buyer", "listing").order_by("-created_at")
    reviews = list(reviews_qs[:5])
    for review in reviews:
        UserProfile.objects.get_or_create(user=review.buyer)

    has_more_reviews = base_reviews_qs[5:6].exists()
    avg_rating = base_reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0
    avg_rating_rounded = int(round(avg_rating)) if avg_rating else 0
    likes_count = base_reviews_qs.filter(rating__gte=4).count()
    dislikes_count = base_reviews_qs.filter(rating__lte=2).count()
    orders_count = Conversation.objects.filter(seller=seller).count()
    seller_status, seller_status_class = get_seller_status_for_profile(
        profile, avg_rating_rounded, orders_count
    )
    seller_is_online = is_user_online(profile)

    listings_active_qs = (
        Listing.objects.filter(seller=seller, status=ListingStatus.ACTIVE)
        .select_related("category", "category__parent")
        .order_by("category__parent__name", "category__name", "title")
    )
    listings_sold_qs = (
        Listing.objects.filter(seller=seller, status=ListingStatus.SOLD)
        .select_related("category", "category__parent")
        .order_by("category__parent__name", "category__name", "title")
    )

    def _group_by_parent(queryset):
        groups = []
        current_parent = None
        current_items = []
        for item in queryset:
            cat = item.category
            parent_name = cat.parent.name if cat.parent else cat.name
            if parent_name != current_parent:
                if current_items:
                    groups.append(
                        {
                            "parent_name": current_parent,
                            "items": current_items,
                        }
                    )
                current_parent = parent_name
                current_items = []
            current_items.append(item)
        if current_items:
            groups.append(
                {
                    "parent_name": current_parent,
                    "items": current_items,
                }
            )
        return groups

    listings_active_groups = _group_by_parent(listings_active_qs)
    listings_sold_groups = _group_by_parent(listings_sold_qs)

    seller_name = (profile.game_nickname or seller.username).strip() if seller else ""
    listings_active_count = listings_active_qs.count()
    page_title = f"Продавец {seller_name} — StarBaz"
    meta_description = (
        f"Профиль продавца {seller_name} на StarBaz: активных объявлений — {listings_active_count}, "
        f"рейтинг — {avg_rating_rounded}/5, завершённых сделок — {orders_count}. "
        "Отзывы покупателей и список товаров."
    )
    meta_keywords = f"{settings_obj.seo_meta_keywords}, продавец, {seller_name}".strip(", ")

    return render(
        request,
        "market/seller_detail.html",
        {
            "site_settings": settings_obj,
            "seller": seller,
            "profile": profile,
            "reviews": reviews,
            "avg_rating": avg_rating,
            "avg_rating_rounded": avg_rating_rounded,
            "likes_count": likes_count,
            "dislikes_count": dislikes_count,
            "orders_count": orders_count,
            "seller_status": seller_status,
            "seller_status_class": seller_status_class,
            "seller_is_online": seller_is_online,
            "has_more_reviews": reviews_qs.count() > 5,
            "listings_active_groups": listings_active_groups,
            "listings_sold_groups": listings_sold_groups,
            "is_guarantor": profile.is_guarantor,
            "page_title": page_title,
            "meta_description": meta_description[:320],
            "meta_keywords": meta_keywords,
        },
    )


def seller_reviews(request, user_id: int):
    settings_obj = get_site_settings()
    seller = get_object_or_404(get_user_model(), pk=user_id)
    profile, _ = UserProfile.objects.get_or_create(user=seller)

    base_reviews_qs = SellerReview.objects.filter(seller=seller)
    reviews_qs = base_reviews_qs.select_related("buyer", "listing").order_by("-created_at")
    for review in reviews_qs:
        UserProfile.objects.get_or_create(user=review.buyer)

    avg_rating = base_reviews_qs.aggregate(avg=Avg("rating"))["avg"] or 0
    avg_rating_rounded = int(round(avg_rating)) if avg_rating else 0
    likes_count = reviews_qs.filter(rating__gte=4).count()
    dislikes_count = reviews_qs.filter(rating__lte=2).count()
    orders_count = Conversation.objects.filter(seller=seller).count()
    seller_status, seller_status_class = get_seller_status_for_profile(
        profile, avg_rating_rounded, orders_count
    )
    seller_is_online = is_user_online(profile)

    return render(
        request,
        "market/seller_reviews.html",
        {
            "site_settings": settings_obj,
            "seller": seller,
            "profile": profile,
            "reviews": reviews_qs,
            "avg_rating": avg_rating,
            "avg_rating_rounded": avg_rating_rounded,
            "likes_count": likes_count,
            "dislikes_count": dislikes_count,
            "orders_count": orders_count,
            "seller_status": seller_status,
            "seller_status_class": seller_status_class,
            "seller_is_online": seller_is_online,
            "is_guarantor": profile.is_guarantor,
        },
    )
