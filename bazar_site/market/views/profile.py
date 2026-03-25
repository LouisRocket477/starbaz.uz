"""
Профиль пользователя и heartbeat для онлайн-статуса.
"""

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone

from ..models import UserProfile
from ._helpers import get_site_settings


@login_required
def profile_view(request):
    settings_obj = get_site_settings()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        profile.game_nickname = request.POST.get("game_nickname", "").strip()
        profile.telegram = request.POST.get("telegram", "").strip()
        profile.discord = request.POST.get("discord", "").strip()
        profile.steam = request.POST.get("steam", "").strip()
        profile.youtube = request.POST.get("youtube", "").strip()
        profile.twitch = request.POST.get("twitch", "").strip()
        profile.instagram = request.POST.get("instagram", "").strip()
        profile.vk = request.POST.get("vk", "").strip()
        profile.extra_link = request.POST.get("extra_link", "").strip()
        profile.operator = request.POST.get("operator", "").strip()
        profile.working_hours = request.POST.get("working_hours", "").strip()
        profile.preferred_language = request.POST.get("preferred_language", "").strip()
        profile.org_url = request.POST.get("org_url", "").strip()
        profile.org_logo_url = request.POST.get("org_logo_url", "").strip()
        avatar = request.FILES.get("avatar")
        if avatar:
            profile.avatar = avatar
        profile.save()
        return redirect("market:profile")

    return render(
        request,
        "market/profile.html",
        {
            "site_settings": settings_obj,
            "profile": profile,
        },
    )


@login_required
def heartbeat(request):
    """Обновляет last_seen профиля, чтобы помечать пользователя онлайн."""
    if request.method == "GET":
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.last_seen = timezone.now()
        profile.save(update_fields=["last_seen"])
        return JsonResponse({"ok": True})
    return JsonResponse({"ok": False}, status=405)
