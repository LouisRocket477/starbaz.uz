from __future__ import annotations

"""
Промежуточные слои (middleware) приложения `market`.

- RateLimitMiddleware   — защита от флуда/частых запросов по IP
- VisitTrackingMiddleware — простая статистика сессий и просмотров страниц
"""

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from .langvars import Lang
from .models import SiteSettings, VisitSession
from .admin_access import user_can_access_admin


class RateLimitMiddleware(MiddlewareMixin):
    """
    Простая защита от DDoS/флуда: ограничение частоты запросов по IP.

    Использует кеш Django (по умолчанию LocMemCache). Для продакшена
    рекомендуется подключить Redis/Memcached.
    """

    # Общее ограничение: не более 200 запросов в минуту с одного IP
    GENERAL_LIMIT = 200
    GENERAL_WINDOW = 60  # секунд

    # Лимиты для чувствительных эндпоинтов
    LOGIN_LIMIT = 20
    LOGIN_WINDOW = 60  # секунд

    REG_LIMIT = 5
    REG_WINDOW = 60 * 60  # 1 час

    AUTH_LOGIN_PATHS = ("/accounts/login", "/admin/login")
    AUTH_REG_PATHS = ("/accounts/signup",)

    def process_request(self, request: HttpRequest) -> HttpResponse | None:
        ip = self._get_ip(request)
        if not ip:
            return None

        # На локальной машине (127.0.0.1 / ::1) никогда не режем запросы,
        # и одновременно очищаем все счётчики, чтобы не висели старые блокировки.
        if ip in ("127.0.0.1", "::1"):
            for suffix in (f"reg:{ip}", f"login:{ip}", f"gen:{ip}"):
                cache.delete(f"rl:{suffix}")
            return None

        # В режиме разработки (DEBUG=True) также не ограничиваем запросы,
        # но при этом не трогаем кеш для других IP.
        if settings.DEBUG:
            return None

        path = request.path or ""

        # Регистрация: не более REG_LIMIT в REG_WINDOW с одного IP
        for prefix in self.AUTH_REG_PATHS:
            if path.startswith(prefix):
                if self._is_rate_limited(f"reg:{ip}", self.REG_LIMIT, self.REG_WINDOW):
                    return self._too_many_requests_response(request)
                return None

        # Логин: отдельный более жёсткий лимит
        for prefix in self.AUTH_LOGIN_PATHS:
            if path.startswith(prefix):
                if self._is_rate_limited(
                    f"login:{ip}", self.LOGIN_LIMIT, self.LOGIN_WINDOW
                ):
                    return self._too_many_requests_response(request)
                break

        # Общее ограничение на все запросы
        if self._is_rate_limited(f"gen:{ip}", self.GENERAL_LIMIT, self.GENERAL_WINDOW):
            return self._too_many_requests_response(request)

        return None

    @staticmethod
    def _get_ip(request: HttpRequest) -> str | None:
        # Если будете стоять за nginx/прокси — можно расширить поддержку X-Forwarded-For
        ip = request.META.get("REMOTE_ADDR")
        if not ip:
            return None
        return str(ip)

    @staticmethod
    def _too_many_requests_response(request: HttpRequest) -> HttpResponse:
        # Пытаемся отрисовать аккуратную страницу 429 в общем стиле сайта.
        try:
            settings_obj, _ = SiteSettings.objects.get_or_create(pk=1)
            context = {
                "site_settings": settings_obj,
                "page_title": "Слишком много запросов",
                "message": Lang.RateLimit.TOO_MANY_REQUESTS,
            }
            return render(request, "429.html", context, status=429)
        except Exception:
            # В крайнем случае — простой текстовый ответ
            return HttpResponse(Lang.RateLimit.TOO_MANY_REQUESTS, status=429)

    @staticmethod
    def _is_rate_limited(key_suffix: str, limit: int, window: int) -> bool:
        """
        Увеличивает счётчик и возвращает True, если лимит превышен.
        """
        key = f"rl:{key_suffix}"

        # Пытаемся создать ключ с начальным значением 1 и TTL = window.
        # Если ключ уже есть, add вернёт False.
        added = cache.add(key, 1, timeout=window)
        if added:
            return False

        try:
            current = cache.incr(key)
        except ValueError:
            # Если по какой‑то причине значение не int — переустанавливаем.
            cache.set(key, 1, timeout=window)
            current = 1

        return current > limit


class ChatFloodControl:
    """
    Вспомогательный класс для анти‑спама в чатах.

    Используется во вьюхах личных и глобального чатов, опирается на
    Redis/кэш Django. Ограничивает отправку сообщений не чаще, чем
    раз в CHAT_COOLDOWN секунд для одного пользователя.
    """

    # за сколько секунд считаем всплеск
    BURST_WINDOW = 1  # секунда
    # сколько сообщений подряд за BURST_WINDOW ещё считаем нормой
    BURST_LIMIT = 2
    # на сколько секунд блокируем после всплеска
    BLOCK_TIME = 7  # секунд

    @classmethod
    def is_blocked(cls, user_id: int, channel: str) -> bool:
        """
        Анти‑спам: если за BURST_WINDOW секунд прилетело больше BURST_LIMIT
        сообщений от одного пользователя в один канал, то блокируем его
        на BLOCK_TIME секунд.
        """
        block_key = f"chat_block:{channel}:{user_id}"
        if cache.get(block_key):
            return True

        burst_key = f"chat_burst:{channel}:{user_id}"
        # пытаемся создать счётчик на BURST_WINDOW секунд
        added = cache.add(burst_key, 1, timeout=cls.BURST_WINDOW)
        if added:
            return False

        try:
            count = cache.incr(burst_key)
        except ValueError:
            cache.set(burst_key, 1, timeout=cls.BURST_WINDOW)
            count = 1

        if count > cls.BURST_LIMIT:
            cache.set(block_key, 1, timeout=cls.BLOCK_TIME)
            return True

        return False

    @classmethod
    def cooldown_json(cls) -> JsonResponse:
        return JsonResponse(
            {
                "error": "cooldown",
                "detail": f"Слишком часто. Попробуйте ещё раз через {cls.BLOCK_TIME} секунд.",
            },
            status=429,
        )


class VisitTrackingMiddleware:
    """
    Простейшая статистика посещений: одна запись на сессию.

    Сохраняем:
    - IP
    - пользователя (если авторизован)
    - первый/последний путь и реферер
    - количество просмотренных страниц
    - длительность сессии (first_seen / last_seen)
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        response = self.get_response(request)
        self._track(request)
        return response

    @staticmethod
    def _track(request: HttpRequest) -> None:
        try:
            # В режиме разработки статистика не должна мешать (SQLite легко ловит "database is locked").
            if settings.DEBUG:
                return
            if request.method != "GET":
                return
            path = request.path or ""
            if path.startswith("/static/") or path.startswith("/media/"):
                return
            # Админку и страницы аккаунта исключаем всегда — там много чувствительных POST/редактирования.
            if path.startswith("/admin/") or path.startswith("/accounts/"):
                return

            # гарантируем наличие session_key
            session = request.session
            if not session.session_key:
                session.save()
            session_key = session.session_key
            if not session_key:
                return

            ip = request.META.get("REMOTE_ADDR") or ""
            ua = request.META.get("HTTP_USER_AGENT", "") or ""
            ref = request.META.get("HTTP_REFERER", "") or ""

            obj, created = VisitSession.objects.get_or_create(
                session_key=session_key,
                defaults={
                    "user": request.user if request.user.is_authenticated else None,
                    "ip_address": ip or None,
                    "user_agent": ua,
                    "first_path": path[:512],
                    "last_path": path[:512],
                    "first_referrer": ref[:512],
                    "last_referrer": ref[:512],
                    "pageviews": 1,
                },
            )
            if not created:
                fields = ["last_seen", "last_path", "last_referrer", "pageviews"]
                obj.last_seen = timezone.now()
                obj.last_path = path[:512]
                if ref:
                    obj.last_referrer = ref[:512]
                obj.pageviews += 1
                if request.user.is_authenticated and obj.user is None:
                    obj.user = request.user
                    fields.append("user")

                obj.save(update_fields=fields)
        except Exception:
            # статистика не должна ломать сайт
            return


class AdminWhitelistMiddleware:
    """
    Блокируем прямой доступ к /admin/* пользователям,
    которые не входят в белый список админов.

    Если пользователь не залогинен — админка отработает стандартно (логин).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        path = request.path or ""
        if path.startswith("/admin/"):
            # Снаружи на /admin не пускаем: только залогиненный пользователь из
            # белого списка может открывать админку.
            if not request.user.is_authenticated or not user_can_access_admin(request.user):
                from django.shortcuts import redirect

                return redirect("/")
        return self.get_response(request)

