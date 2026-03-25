from collections import defaultdict
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone

from .models import FooterLink, FooterSocialLink, Message, MusicTrack, SiteSettings, UserProfile, VisitSession


def footer(request):
    """Глобальный контекст для футера и настроек сайта."""
    settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)

    links = FooterLink.objects.filter(is_active=True).order_by(
        "column", "sort_order", "title"
    )
    socials = FooterSocialLink.objects.filter(is_active=True).order_by("sort_order")

    columns = defaultdict(list)
    for link in links:
        columns[link.column].append(link)

    # Активные сессии за последние 10 минут — приближённое количество пользователей онлайн.
    active_since = timezone.now() - timedelta(minutes=10)
    online_sessions = VisitSession.objects.filter(last_seen__gte=active_since)
    online_count = online_sessions.count()

    # Плейлист для глобального медиаплеера (треки из media/music/).
    music_tracks = MusicTrack.objects.filter(is_active=True).order_by("sort_order", "id")
    media_playlist = [
        {"name": t.name, "url": request.build_absolute_uri(t.file.url)}
        for t in music_tracks
        if t.file
    ]

    og_default_image = request.build_absolute_uri("/static/market/images/logo.png")

    result = {
        "site_settings": settings_obj,
        "footer_columns": columns,
        "footer_socials": socials,
        "site_online_now": online_count,
        "media_playlist": media_playlist,
        "og_default_image": og_default_image,
    }

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        result["nav_user_profile"] = profile
        unread = Message.objects.filter(
            Q(conversation__buyer=request.user) | Q(conversation__seller=request.user),
            is_read=False,
        ).exclude(sender=request.user).count()
        result["nav_unread_chat_count"] = unread

        # Для админов/операторов показываем счётчик открытых тикетов прямо в "Чат".
        if getattr(profile, "is_project_admin", False) or getattr(profile, "is_operator", False):
            try:
                from .support.models import SupportRequest

                result["nav_open_support_tickets"] = SupportRequest.objects.filter(is_resolved=False).count()
            except Exception:
                result["nav_open_support_tickets"] = 0

    return result

