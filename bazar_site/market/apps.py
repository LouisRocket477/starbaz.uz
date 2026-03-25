from django.apps import AppConfig


class MarketConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "market"

    def ready(self) -> None:
        """
        Хук инициализации приложения.

        Здесь мягко отключаем встроенный rate limit django-allauth, так как
        он у нас дублирует и конфликтует с собственным RateLimitMiddleware
        и django-axes и в текущей версии даёт ошибку
        \"'NoneType' object has no attribute 'method'\".
        """
        import market.checks  # noqa: F401
        import market.signals  # noqa: F401

        from django.contrib import admin

        from market.admin_forms import RecaptchaAdminAuthenticationForm
        from market.admin_access import user_can_access_admin

        if not getattr(admin.site, "_starbaz_admin_login_configured", False):
            admin.site._starbaz_admin_login_configured = True
            admin.site.login_form = RecaptchaAdminAuthenticationForm
            admin.site.site_header = "StarBaz — администрирование"
            admin.site.site_title = "StarBaz Admin"
            admin.site.index_title = "Панель управления"

            _original_each_context = admin.site.each_context

            def _each_context_with_recaptcha(request):
                ctx = _original_each_context(request)
                return ctx

            admin.site.each_context = _each_context_with_recaptcha

            # Права на доступ к страницам админки (/admin/*) — только по белому списку.
            admin.site.has_permission = lambda request: user_can_access_admin(
                getattr(request, "user", None)
            )

        try:
            from allauth.core.internal import ratelimit as core_ratelimit  # type: ignore
        except Exception:
            return

        # Заменяем декоратор на no-op, чтобы он никак не влиял на вьюхи.
        def _noop_rate_limit(*dargs, **dkwargs):  # type: ignore[override]
            def decorator(fn):
                return fn

            return decorator

        def _noop_consume(*args, **kwargs):
            return None

        def _noop_consume_or_429(request, *args, **kwargs):
            return None

        def _noop_clear(*args, **kwargs):
            return None

        core_ratelimit.rate_limit = _noop_rate_limit  # type: ignore[attr-defined]
        core_ratelimit.consume = _noop_consume  # type: ignore[assignment]
        if hasattr(core_ratelimit, "consume_or_429"):
            core_ratelimit.consume_or_429 = _noop_consume_or_429  # type: ignore[assignment]
        core_ratelimit.clear = _noop_clear  # type: ignore[assignment]
