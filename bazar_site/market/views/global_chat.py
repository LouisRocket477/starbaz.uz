"""
API глобального чата на главной странице.
"""

from datetime import timedelta

from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.utils import timezone

from ..middleware import ChatFloodControl
from ..models import GlobalChatMessage


GLOBAL_CHAT_CLEANUP_CACHE_KEY = "global_chat_cleanup_last_run"
GLOBAL_CHAT_CLEANUP_INTERVAL_SECONDS = 3600
GLOBAL_CHAT_RETENTION_HOURS = 1


def _cleanup_global_chat_if_needed() -> None:
    """
    Автоочистка общего чата:
    - не чаще 1 раза в час;
    - удаляем сообщения старше 1 часа.
    """
    now = timezone.now()
    last_run = cache.get(GLOBAL_CHAT_CLEANUP_CACHE_KEY)
    if last_run and (now - last_run).total_seconds() < GLOBAL_CHAT_CLEANUP_INTERVAL_SECONDS:
        return

    threshold = now - timedelta(hours=GLOBAL_CHAT_RETENTION_HOURS)
    GlobalChatMessage.objects.filter(created_at__lt=threshold).delete()
    cache.set(GLOBAL_CHAT_CLEANUP_CACHE_KEY, now, timeout=GLOBAL_CHAT_CLEANUP_INTERVAL_SECONDS)


@csrf_exempt
def global_chat_api(request):
    """Простой API для общего чата на главной странице."""
    _cleanup_global_chat_if_needed()

    if request.method == "GET":
        messages_qs = (
            GlobalChatMessage.objects.select_related("user", "reply_to", "reply_to__user")
            .all()
            .order_by("-created_at")[:30]
        )
        data = [
            {
                "id": msg.id,
                "user": msg.user.username,
                "user_id": msg.user_id,
                "content": msg.content,
                "created_at": msg.created_at.strftime("%H:%M"),
                "reply_to": msg.reply_to_id,
                "reply_to_user": msg.reply_to.user.username if msg.reply_to_id and msg.reply_to.user_id else None,
                "reply_to_content": (msg.reply_to.content[:80] if msg.reply_to_id and msg.reply_to.content else None),
            }
            for msg in reversed(list(messages_qs))
        ]
        return JsonResponse({"messages": data})

    if request.method == "POST":
        if not request.user.is_authenticated:
            return JsonResponse({"error": "auth_required"}, status=403)

        content = request.POST.get("content", "").strip()
        if not content:
            return JsonResponse({"error": "empty"}, status=400)
        if len(content) > 500:
            return JsonResponse({"error": "too_long"}, status=400)

        reply_to_id_raw = request.POST.get("reply_to")
        reply_to_obj = None
        if reply_to_id_raw:
            try:
                reply_to_obj = GlobalChatMessage.objects.get(pk=int(reply_to_id_raw))
            except (ValueError, GlobalChatMessage.DoesNotExist):
                reply_to_obj = None

        if ChatFloodControl.is_blocked(request.user.id, "global"):
            return ChatFloodControl.cooldown_json()

        msg = GlobalChatMessage.objects.create(
            user=request.user,
            content=content,
            reply_to=reply_to_obj,
        )
        data = {
            "id": msg.id,
            "user": msg.user.username,
            "user_id": msg.user_id,
            "content": msg.content,
            "created_at": msg.created_at.strftime("%H:%M"),
            "reply_to": msg.reply_to_id,
        }
        return JsonResponse({"message": data}, status=201)

    return JsonResponse({"error": "method_not_allowed"}, status=405)
