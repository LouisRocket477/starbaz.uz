from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from ..models import UserProfile
from ..site.services import get_site_settings
from .models import SupportMessage, SupportRequest


def _can_manage_support(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return bool(profile.is_project_admin or profile.is_operator)


@login_required
def support_admin_list(request):
    if not _can_manage_support(request.user):
        return HttpResponseForbidden("forbidden")

    settings_obj = get_site_settings()
    open_tickets = list(
        SupportRequest.objects.select_related("author")
        .filter(is_resolved=False)
        .order_by("-created_at")[:200]
    )
    closed_tickets = list(
        SupportRequest.objects.select_related("author")
        .filter(is_resolved=True)
        .order_by("-resolved_at", "-created_at")[:100]
    )

    return render(
        request,
        "market/support_admin_list.html",
        {
            "site_settings": settings_obj,
            "open_tickets": open_tickets,
            "closed_tickets": closed_tickets,
            "page_title": "Тикеты поддержки — Панель",
        },
    )


@login_required
def support_admin_ticket(request, pk: int):
    if not _can_manage_support(request.user):
        return HttpResponseForbidden("forbidden")

    ticket = get_object_or_404(
        SupportRequest.objects.select_related("author"),
        pk=pk,
    )
    settings_obj = get_site_settings()

    if request.method == "POST":
        action = (request.POST.get("action") or "").strip()

        if action == "reply" and not ticket.is_closed:
            text = (request.POST.get("reply_text") or "").strip()
            screenshot = request.FILES.get("reply_screenshot")
            final_reply = (request.POST.get("final_reply") or "").strip()

            if text or screenshot:
                SupportMessage.objects.create(
                    request=ticket,
                    author=request.user,
                    text=text,
                    screenshot=screenshot,
                )
                ticket.admin_replied_at = timezone.now()
                ticket.admin_replied_by = request.user
                ticket.save(update_fields=["admin_replied_at", "admin_replied_by"])

            if final_reply and final_reply != (ticket.admin_reply or ""):
                ticket.admin_reply = final_reply
                ticket.admin_replied_at = timezone.now()
                ticket.admin_replied_by = request.user
                ticket.save(update_fields=["admin_reply", "admin_replied_at", "admin_replied_by"])

            return redirect("market:support_admin_ticket", pk=ticket.id)

        if action == "close" and not ticket.is_closed:
            ticket.is_resolved = True
            ticket.resolved_at = timezone.now()
            ticket.resolved_by = request.user
            ticket.save(update_fields=["is_resolved", "resolved_at", "resolved_by"])
            return redirect("market:support_admin_ticket", pk=ticket.id)

        if action == "reopen" and ticket.is_closed:
            ticket.is_resolved = False
            ticket.resolved_at = None
            ticket.resolved_by = None
            ticket.save(update_fields=["is_resolved", "resolved_at", "resolved_by"])
            return redirect("market:support_admin_ticket", pk=ticket.id)

        return redirect("market:support_admin_ticket", pk=ticket.id)

    messages = list(
        SupportMessage.objects.select_related("author")
        .filter(request=ticket)
        .order_by("created_at", "pk")
    )

    return render(
        request,
        "market/support_admin_ticket.html",
        {
            "site_settings": settings_obj,
            "ticket": ticket,
            "messages": messages,
            "page_title": f"Тикет #{ticket.id} — Поддержка",
        },
    )

