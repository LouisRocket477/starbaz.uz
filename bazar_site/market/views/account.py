"""
Вьюхи входа и регистрации (кастомный логин без rate limit allauth).
"""

from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import get_user_model
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from allauth.account import app_settings as allauth_settings
from allauth.account.utils import complete_signup

from ..forms import SignupFormWithCaptcha, SimpleLoginForm
from ._helpers import get_site_settings
from market.recaptcha_keys import get_admin_recaptcha_public_key


def account_login_view(request: HttpRequest) -> HttpResponse:
    """Простой логин без внутренних блокировок по попыткам."""
    settings_obj = get_site_settings()
    recaptcha_public_key = get_admin_recaptcha_public_key()
    redirect_url = request.GET.get("next") or None

    if request.method == "POST":
        form = SimpleLoginForm(request.POST, request=request)
        if form.is_valid():
            login_value = form.cleaned_data["login"].strip()
            password = form.cleaned_data["password"]

            user_model = get_user_model()
            user_obj = None

            try:
                user_obj = user_model.objects.get(username__iexact=login_value)
            except user_model.DoesNotExist:
                user_obj = None

            if user_obj is None and "@" in login_value:
                try:
                    user_obj = user_model.objects.get(email__iexact=login_value)
                except user_model.DoesNotExist:
                    user_obj = None

            user = None
            if user_obj is not None:
                user = authenticate(request, username=user_obj.username, password=password)

            if user is None:
                form.add_error(
                    None,
                    "Неверный e‑mail / логин или пароль. Попробуйте ещё раз.",
                )
            else:
                auth_login(request, user)
                if not form.cleaned_data.get("remember"):
                    request.session.set_expiry(0)
                return redirect(redirect_url or "/")
    else:
        form = SimpleLoginForm(request=request)

    return render(
        request,
        "account/login.html",
        {
            "site_settings": settings_obj,
            "form": form,
            "recaptcha_public_key": recaptcha_public_key,
        },
    )


def account_signup_view(request: HttpRequest) -> HttpResponse:
    """
    Регистрация через allauth, но без их rate limit, с нашей CAPTCHA.
    """
    settings_obj = get_site_settings()
    recaptcha_public_key = get_admin_recaptcha_public_key()

    if request.method == "POST":
        form = SignupFormWithCaptcha(request.POST, request=request)
        if form.is_valid():
            try:
                user = form.save(request)
            except ValueError:
                # allauth может выбросить ValueError (например, при конфликте email)
                # — показываем понятную ошибку в форме, а не 500.
                form.add_error(
                    "email",
                    "Пользователь с таким e-mail уже зарегистрирован. Используйте другой адрес или войдите в аккаунт.",
                )
            else:
                return complete_signup(
                    request,
                    user,
                    email_verification=allauth_settings.EMAIL_VERIFICATION,
                    success_url="/",
                )
    else:
        form = SignupFormWithCaptcha(request=request)

    return render(
        request,
        "account/signup.html",
        {
            "site_settings": settings_obj,
            "form": form,
            "recaptcha_public_key": recaptcha_public_key,
        },
    )
