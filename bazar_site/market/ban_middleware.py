from __future__ import annotations

from django.contrib.auth import logout
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .models import UserProfile


class BanCheckMiddleware:
    """
    Проверяет, не заблокирован ли пользователь в профиле.

    Если профиль помечен как is_banned=True, пользователь разлогинивается,
    и ему показывается красивая страница блокировки.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            try:
                profile = user.profile
            except UserProfile.DoesNotExist:
                profile = None

            if profile and profile.is_banned:
                # Не мешаем работе админки — админы сами себя не банят.
                if not request.path.startswith("/admin/"):
                    logout(request)
                    return render(
                        request,
                        "market/ban.html",
                        {"ban_reason": profile.ban_reason},
                        status=403,
                    )

        return self.get_response(request)


