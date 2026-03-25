from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required

from ..site.services import get_site_settings
from ..support.models import SupportRequest, SupportFAQ, SupportMessage
from ..models import Conversation, PurchaseRequest


def support_hub(request):
    """Хаб поддержки: три больших кнопки на отдельные страницы."""
    settings_obj = get_site_settings()
    return render(
        request,
        "market/support_hub.html",
        {
            "site_settings": settings_obj,
            "page_title": "Поддержка StarBaz",
            "meta_description": "Центр поддержки StarBaz: создайте тикет, проверьте статус обращений и найдите ответы в разделе FAQ.",
            "meta_keywords": "StarBaz, поддержка, тикет, FAQ, помощь",
        },
    )


@login_required
def support_new(request):
    """Страница создания нового тикета."""
    settings_obj = get_site_settings()

    # Значения по умолчанию из query‑параметров (например, при переходе со страницы продавца)
    initial_request_type = request.GET.get("request_type") or SupportRequest.Type.OTHER
    initial_subject = (request.GET.get("subject") or "").strip()
    seller_name = (request.GET.get("seller") or "").strip()
    seller_id = (request.GET.get("seller_id") or "").strip()
    if not initial_subject and seller_name:
        if seller_id.isdigit():
            initial_subject = f"Вопрос по продавцу {seller_name} (ID: {seller_id})"
        else:
            initial_subject = f"Вопрос по продавцу {seller_name}"

    if request.method == "POST":
        request_type = request.POST.get("request_type") or SupportRequest.Type.OTHER
        subject = (request.POST.get("subject") or "").strip()
        message = (request.POST.get("message") or "").strip()
        contact = (request.POST.get("contact") or "").strip()
        screenshot = request.FILES.get("screenshot")

        if message or screenshot:
            support_request = SupportRequest.objects.create(
                author=request.user,
                contact=contact,
                request_type=request_type,
                subject=subject,
                message=message or "(пустое сообщение, только вложение)",
            )
            if message or screenshot:
                SupportMessage.objects.create(
                    request=support_request,
                    author=request.user,
                    text=message,
                    screenshot=screenshot,
                )
            return redirect("market:support_thanks")

    return render(
        request,
        "market/support_new.html",
        {
            "site_settings": settings_obj,
            "initial_request_type": initial_request_type,
            "initial_subject": initial_subject,
            "page_title": "Создать тикет — Поддержка StarBaz",
            "meta_description": "Создайте обращение в поддержку StarBaz: вопросы по продавцу, баги, идеи, премиум и другие темы.",
            "meta_keywords": "StarBaz, поддержка, тикет, обращение, баг, премиум",
        },
    )


def support_my(request):
    """Отдельная страница со списком тикетов пользователя и ответами администрации."""
    settings_obj = get_site_settings()
    open_requests = []
    closed_requests = []
    if request.user.is_authenticated:
        qs = (
            SupportRequest.objects.filter(author=request.user)
            .prefetch_related("messages")
        )
        open_requests = list(qs.filter(is_resolved=False).order_by("-created_at")[:50])
        closed_requests = list(qs.filter(is_resolved=True).order_by("-created_at")[:50])

    return render(
        request,
        "market/support_my.html",
        {
            "site_settings": settings_obj,
            "open_support_requests": open_requests,
            "closed_support_requests": closed_requests,
            # Backward-compatible key: старые шаблоны/код могли ожидать support_requests.
            "support_requests": open_requests + closed_requests,
            "page_title": "Мои тикеты — Поддержка StarBaz",
            "meta_description": "Личный кабинет поддержки: ваши обращения, статусы и ответы администрации StarBaz.",
            "meta_keywords": "StarBaz, мои тикеты, поддержка, обращения",
        },
    )


def support_faq(request):
    """Отдельная страница с вопросами‑ответами по сайту."""
    settings_obj = get_site_settings()
    faqs = SupportFAQ.objects.filter(is_active=True).order_by("sort_order", "id")
    return render(
        request,
        "market/support_faq.html",
        {
            "site_settings": settings_obj,
            "faqs": faqs,
            "page_title": "FAQ — Поддержка StarBaz",
            "meta_description": "FAQ StarBaz: ответы на популярные вопросы о работе сайта, правилах, сделках и обращениях в поддержку.",
            "meta_keywords": "StarBaz, FAQ, вопросы, ответы, правила, поддержка",
        },
    )


@login_required
def premium_options(request):
    """Страница выбора премиум‑пакета (создаёт заявку в поддержку)."""
    settings_obj = get_site_settings()

    if request.method == "POST":
        package = request.POST.get("package") or "month"
        package_map = {
            "month": "Премиум на 1 месяц",
            "quarter": "Премиум на 3 месяца",
            "year": "Премиум на 12 месяцев",
        }
        boosts_map = {
            "month": 5,
            "quarter": 20,
            "year": 250,
        }
        subject = package_map.get(package, "Премиум‑статус")
        boosts = boosts_map.get(package)

        message_lines = [
            f"Пользователь просит выдать пакет: {subject}.",
        ]
        if boosts:
            message_lines.append(
                f"В пакет входит лимит на {boosts} поднятий объявления(ий) в топ "
                "в течение срока действия премиума."
            )
        message_lines.append(
            "Это добровольное пожертвование, не дающее финансовых гарантий. "
            "После получения оплаты администратор вручную активирует премиум‑статус "
            "и начислит соответствующее количество очков поднятия."
        )
        message = "\n\n".join(message_lines)

        SupportRequest.objects.create(
            author=request.user,
            contact="",
            request_type=SupportRequest.Type.PREMIUM,
            subject=subject,
            message=message,
        )
        return redirect("market:support_thanks")

    return render(
        request,
        "market/premium_options.html",
        {
            "site_settings": settings_obj,
        },
    )


def support_thanks(request):
    settings_obj = get_site_settings()
    return render(
        request,
        "market/support_thanks.html",
        {
            "site_settings": settings_obj,
        },
    )


@login_required
def support_dispute(request, conversation_id: int):
    """Создать тикет-спор по последней завершённой сделке в диалоге.

    UX:
    - GET: показать форму (пользователь описывает, что произошло)
    - POST: создать тикет и сразу открыть его в «Мои тикеты»
    """

    conversation = get_object_or_404(
        Conversation.objects.select_related("listing", "buyer", "seller"),
        pk=conversation_id,
    )
    if request.user not in {conversation.buyer, conversation.seller}:
        return HttpResponseForbidden("forbidden")

    last_pr = (
        conversation.purchase_requests.filter(status=PurchaseRequest.Status.COMPLETED)
        .order_by("-created_at")
        .first()
    )
    if not last_pr:
        return redirect("market:conversation_detail", pk=conversation.id)

    other_user = conversation.seller if request.user == conversation.buyer else conversation.buyer
    listing = conversation.listing
    listing_title = (listing.title or "").strip() if listing else ""

    subject = f"Спор по сделке #{conversation.id}"
    if listing_title:
        subject = f"{subject}: {listing_title[:80]}"

    if request.method == "GET":
        return render(
            request,
            "market/support_dispute.html",
            {
                "site_settings": get_site_settings(),
                "conversation": conversation,
                "listing": listing,
                "purchase_request": last_pr,
                "other_user": other_user,
                "subject": subject,
            },
        )

    # POST
    details = (request.POST.get("details") or "").strip()
    dispute_kind = request.POST.get("dispute_kind") or SupportRequest.DisputeKind.NOT_RECEIVED
    if dispute_kind not in dict(SupportRequest.DisputeKind.choices):
        dispute_kind = SupportRequest.DisputeKind.NOT_RECEIVED

    header_lines = [
        "Спор по завершённой сделке.",
        f"Диалог: #{conversation.id}",
        f"Запрос на покупку: #{last_pr.id}",
    ]
    if listing:
        header_lines.append(f"Объявление: #{listing.id} — {listing.title}")
    header_lines.append(f"Заявитель: {request.user.username} (ID: {request.user.id})")
    header_lines.append(f"Оппонент: {other_user.username} (ID: {other_user.id})")
    header_lines.append("")
    header_lines.append("Описание пользователя:")
    header_lines.append(details or "(пусто)")
    message = "\n".join(header_lines)

    support_request = SupportRequest.objects.create(
        author=request.user,
        contact="",
        request_type=SupportRequest.Type.SELLER,
        subject=subject,
        message=message,
        related_conversation=conversation,
        related_listing=listing,
        related_purchase_request=last_pr,
        against_user=other_user,
        dispute_kind=dispute_kind,
        dispute_details=details,
    )

    # Сразу ведём пользователя в «Мои тикеты» и раскрываем созданный тикет.
    return redirect(f"/support/my/#ticket-{support_request.id}")

