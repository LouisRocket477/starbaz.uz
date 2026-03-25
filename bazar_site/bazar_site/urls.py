"""
URL configuration for bazar_site project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from market import views as market_views

urlpatterns = [
    path("admin/", admin.site.urls),
    # Переопределяем страницы логина/регистрации allauth нашими вьюхами
    path("accounts/login/", market_views.account_login_view, name="account_login"),
    path("accounts/signup/", market_views.account_signup_view, name="account_signup"),
    path("accounts/", include("allauth.urls")),
    path("", include("market.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


# Кастомные обработчики ошибок
handler400 = "market.views.error_400"  # type: ignore[assignment]
handler403 = "market.views.error_403"  # type: ignore[assignment]
handler404 = "market.views.error_404"  # type: ignore[assignment]
handler500 = "market.views.error_500"  # type: ignore[assignment]
