"""
CRUD объявлений: мои объявления, создание, редактирование, удаление.
"""

from random import randint
from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.db.models import Case, IntegerField, When, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..enums import ListingDealType, ListingStatus
from ..models import (
    Category,
    Listing,
    ListingImage,
    ListingPriceHistory,
    ListingVideo,
    UserProfile,
)
from ..services import ListingPriceService, format_price_for_input, get_site_settings


@login_required
def my_listings(request):
    settings_obj = get_site_settings()
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)
    now = timezone.now()
    query = (request.GET.get("q") or "").strip()
    listings = (
        Listing.objects.filter(seller=request.user)
        .select_related("category")
        .annotate(
            _status_priority=Case(
                When(status=ListingStatus.ACTIVE, then=0),
                default=1,
                output_field=IntegerField(),
            ),
            _boost_priority=Case(
                When(boosted_until__gte=now, then=0),
                default=1,
                output_field=IntegerField(),
            ),
        )
        .order_by("_status_priority", "_boost_priority", "-boosted_until", "-updated_at")
    )
    if query:
        listings = listings.filter(
            Q(title__icontains=query)
            | Q(category__name__icontains=query)
            | Q(description__icontains=query)
        )
    return render(
        request,
        "market/my_listings.html",
        {
            "site_settings": settings_obj,
            "listings": listings,
            "user_profile": user_profile,
            "now": now,
            "query": query,
        },
    )


@login_required
def listing_boost(request, pk: int):
    """Поднять объявление в топ на 24 часа за 1 очко премиума."""
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    now = timezone.now()
    is_premium_active = profile.is_premium and (
        profile.premium_until is None or profile.premium_until >= now
    )
    if request.method == "POST" and is_premium_active and profile.premium_boost_credits > 0:
        profile.premium_boost_credits -= 1
        profile.save(update_fields=["premium_boost_credits"])
        listing.boosted_until = now + timedelta(hours=24)
        listing.save(update_fields=["boosted_until"])
    return redirect("market:my_listings")


@login_required
def listing_create(request):
    settings_obj = get_site_settings()
    categories = Category.objects.filter(is_active=True, parent__isnull=False).order_by(
        "parent__sort_order",
        "parent__name",
        "sort_order",
        "name",
    )

    errors: list[str] = []
    captcha_question: str | None = None

    if request.method == "POST":
        start_of_day = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        created_today = Listing.objects.filter(
            seller=request.user, created_at__gte=start_of_day
        ).count()
        if created_today >= 20:
            errors.append(
                "Вы создали максимальное количество объявлений на сегодня (20 шт.). Попробуйте завтра."
            )

        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        deal_type = request.POST.get("deal_type", ListingDealType.SELL)
        original_price_raw = request.POST.get("original_price", "").strip()
        price_raw = request.POST.get("price", "").strip()
        category_id = request.POST.get("category")
        barter_allowed = request.POST.get("barter_allowed") == "on"
        barter_for_ids = request.POST.getlist("barter_for")
        barter_custom = request.POST.get("barter_custom", "").strip()
        source = request.POST.get("source", "").strip()
        location = request.POST.get("location", "").strip()
        star_system = request.POST.get("star_system", "").strip()
        availability = request.POST.get("availability", "").strip()
        in_stock = request.POST.get("in_stock") == "on"
        quantity_raw = request.POST.get("quantity", "").strip()
        try:
            quantity = int(quantity_raw) if quantity_raw else None
            if quantity is not None and quantity < 0:
                quantity = None
        except ValueError:
            quantity = None

        correct_value = request.session.get("listing_captcha_value")
        captcha_raw = request.POST.get("captcha_answer", "").strip()
        try:
            captcha_val = int(captcha_raw)
        except (TypeError, ValueError):
            captcha_val = None
        if correct_value is None or captcha_val != correct_value:
            errors.append("Неверный ответ на проверочный пример.")

        a = randint(2, 9)
        b = randint(2, 9)
        request.session["listing_captcha_value"] = a + b
        captcha_question = f"Сколько будет {a} + {b}?"

        price_result = ListingPriceService.validate_for_create(
            original_price_raw=original_price_raw,
            price_raw=price_raw,
        )
        original_price_value = price_result.original_price
        price_value = price_result.price
        errors.extend(price_result.errors)

        if (
            title
            and description
            and category_id
            and original_price_value is not None
            and price_value is not None
            and not errors
        ):
            category = get_object_or_404(Category, pk=category_id, is_active=True)
            if deal_type not in {
                ListingDealType.SELL,
                ListingDealType.BUY,
                ListingDealType.TRADE,
            }:
                deal_type = ListingDealType.SELL
            _in_stock = in_stock if deal_type != ListingDealType.BUY else True

            listing = Listing.objects.create(
                seller=request.user,
                category=category,
                title=title,
                description=description,
                deal_type=deal_type,
                price=price_value,
                original_price=original_price_value,
                barter_allowed=barter_allowed,
                barter_custom=barter_custom,
                source=source,
                location=location,
                star_system=star_system,
                availability=availability,
                in_stock=_in_stock,
                quantity=quantity,
            )
            ListingPriceHistory.objects.create(listing=listing, price=price_value)

            if barter_allowed and barter_for_ids:
                barter_categories = Category.objects.filter(
                    pk__in=barter_for_ids, is_active=True
                )
                listing.barter_for.set(barter_categories)

            for idx, file in enumerate(request.FILES.getlist("images")):
                ListingImage.objects.create(
                    listing=listing,
                    image=file,
                    sort_order=idx,
                )
            for idx, file in enumerate(request.FILES.getlist("videos")):
                ListingVideo.objects.create(
                    listing=listing,
                    file=file,
                    sort_order=idx,
                )

            return redirect("market:listing_detail", pk=listing.pk)
    else:
        a = randint(2, 9)
        b = randint(2, 9)
        request.session["listing_captcha_value"] = a + b
        captcha_question = f"Сколько будет {a} + {b}?"

    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    return render(
        request,
        "market/listing_form.html",
        {
            "site_settings": settings_obj,
            "categories": categories,
            "listing": None,
            "captcha_question": captcha_question,
            "errors": errors if request.method == "POST" else [],
            "user_profile": user_profile,
        },
    )


@login_required
def listing_edit(request, pk: int):
    settings_obj = get_site_settings()
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    categories = Category.objects.filter(is_active=True)
    user_profile, _ = UserProfile.objects.get_or_create(user=request.user)

    errors: list[str] = []
    original_price_display: str | None = format_price_for_input(
        listing.original_price or listing.price
    )
    price_display: str | None = format_price_for_input(
        listing.price or listing.original_price
    )

    if request.method == "POST":
        title = request.POST.get("title", "").strip()
        description = request.POST.get("description", "").strip()
        deal_type = request.POST.get(
            "deal_type", listing.deal_type or ListingDealType.SELL
        )
        original_price_raw = request.POST.get("original_price", "").strip()
        price_raw = request.POST.get("price", "").strip()
        if not price_raw and original_price_raw:
            price_raw = original_price_raw
        category_id = request.POST.get("category")
        barter_allowed = request.POST.get("barter_allowed") == "on"
        barter_for_ids = request.POST.getlist("barter_for")
        barter_custom = request.POST.get("barter_custom", "").strip()
        main_image_id = request.POST.get("main_image")
        delete_image_ids = request.POST.getlist("delete_images")
        source = request.POST.get("source", "").strip()
        location = request.POST.get("location", "").strip()
        star_system = request.POST.get("star_system", "").strip()
        availability = request.POST.get("availability", "").strip()
        in_stock = request.POST.get("in_stock") == "on"
        quantity_raw = request.POST.get("quantity", "").strip()
        try:
            quantity = int(quantity_raw) if quantity_raw else None
            if quantity is not None and quantity < 0:
                quantity = None
        except ValueError:
            quantity = None

        price_result = ListingPriceService.validate_for_edit(
            original_price_raw=original_price_raw,
            price_raw=price_raw,
            current_original=listing.original_price,
            current_price=listing.price,
        )
        original_price_value = price_result.original_price
        price_value = price_result.price
        errors.extend(price_result.errors)

        if original_price_raw:
            original_price_display = original_price_raw
        elif original_price_value is not None:
            original_price_display = format_price_for_input(original_price_value)

        _price_was_empty = not request.POST.get("price", "").strip()
        if _price_was_empty:
            price_display = None
        elif price_raw:
            price_display = price_raw
        elif price_value is not None and original_price_value is not None and price_value < original_price_value:
            price_display = format_price_for_input(price_value)
        elif price_value is not None:
            price_display = format_price_for_input(price_value)

        if (
            title
            and description
            and category_id
            and original_price_value is not None
            and price_value is not None
            and not errors
        ):
            category = get_object_or_404(Category, pk=category_id, is_active=True)
            if deal_type not in {
                ListingDealType.SELL,
                ListingDealType.BUY,
                ListingDealType.TRADE,
            }:
                deal_type = ListingDealType.SELL
            _in_stock = in_stock if deal_type != ListingDealType.BUY else True

            was_sold = listing.status == ListingStatus.SOLD

            listing.title = title
            listing.description = description
            listing.deal_type = deal_type
            listing.original_price = original_price_value
            listing.price = price_value
            listing.category = category
            listing.barter_allowed = barter_allowed
            listing.barter_custom = barter_custom
            listing.source = source
            listing.location = location
            listing.star_system = star_system
            listing.availability = availability
            listing.in_stock = _in_stock
            listing.quantity = quantity

            # Если объявление было завершено и мы снова указываем наличие товара,
            # автоматически возвращаем его в публикацию и считаем как обновлённое.
            if (
                was_sold
                and listing.deal_type != ListingDealType.BUY
                and listing.in_stock
                and (listing.quantity is None or listing.quantity > 0)
            ):
                listing.status = ListingStatus.ACTIVE
                # Обновляем время обновления, чтобы объявление поднялось выше.
                listing.updated_at = timezone.now()

            listing.save()

            last_price = listing.price_history.order_by("-recorded_at").first()
            if last_price is None or last_price.price != price_value:
                ListingPriceHistory.objects.create(listing=listing, price=price_value)

            if delete_image_ids:
                ListingImage.objects.filter(
                    listing=listing, pk__in=delete_image_ids
                ).delete()

            if barter_allowed:
                barter_categories = Category.objects.filter(
                    pk__in=barter_for_ids, is_active=True
                )
                listing.barter_for.set(barter_categories)
            else:
                listing.barter_for.clear()

            files = request.FILES.getlist("images")
            start_index = listing.images.count()
            for idx, file in enumerate(files, start=start_index):
                ListingImage.objects.create(
                    listing=listing,
                    image=file,
                    sort_order=idx,
                )
            video_files = request.FILES.getlist("videos")
            start_v_index = listing.videos.count()
            for idx, file in enumerate(video_files, start=start_v_index):
                ListingVideo.objects.create(
                    listing=listing,
                    file=file,
                    sort_order=idx,
                )

            if main_image_id:
                try:
                    main_img = listing.images.get(pk=main_image_id)
                    main_img.is_main = True
                    main_img.save()
                except ListingImage.DoesNotExist:
                    pass
            else:
                if listing.images.exists() and not listing.images.filter(is_main=True).exists():
                    first_img = listing.images.first()
                    first_img.is_main = True
                    first_img.save()

            return redirect("market:listing_detail", pk=listing.pk)

    return render(
        request,
        "market/listing_form.html",
        {
            "site_settings": settings_obj,
            "categories": categories,
            "listing": listing,
            "original_price_display": original_price_display,
            "price_display": price_display,
            "errors": errors if request.method == "POST" else [],
            "user_profile": user_profile,
        },
    )


@login_required
def listing_delete(request, pk: int):
    settings_obj = get_site_settings()
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)

    if request.method == "POST":
        listing.delete()
        return redirect("market:my_listings")

    return render(
        request,
        "market/listing_delete_confirm.html",
        {
            "site_settings": settings_obj,
            "listing": listing,
        },
    )


@login_required
def listing_toggle_status(request, pk: int):
    """Переключение публикации объявления: Активно ↔ Завершено."""
    listing = get_object_or_404(Listing, pk=pk, seller=request.user)
    if request.method == "POST":
        # Если объявление активно — просто снимаем с публикации.
        if listing.status == ListingStatus.ACTIVE:
            listing.status = ListingStatus.SOLD
            listing.in_stock = False
            listing.save(update_fields=["status", "in_stock", "updated_at"])
            return redirect("market:my_listings")

        # Если объявление завершено:
        # - для «Покупаю» можно сразу вернуть в публикацию;
        # - для «Продаю/Обмен» ведём на страницу редактирования,
        #   чтобы указать актуальное количество/наличие.
        if listing.deal_type == ListingDealType.BUY:
            listing.status = ListingStatus.ACTIVE
            listing.in_stock = True
            listing.updated_at = timezone.now()
            listing.save(update_fields=["status", "in_stock", "updated_at"])
            return redirect("market:my_listings")

        return redirect("market:listing_edit", pk=listing.pk)

    return redirect("market:my_listings")
