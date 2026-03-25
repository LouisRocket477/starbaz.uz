from __future__ import annotations

from allauth.account.forms import SignupForm
from django import forms
from django.core.exceptions import ValidationError

from market.recaptcha_keys import get_admin_recaptcha_secret_key
from market.recaptcha_utils import verify_recaptcha_token_v3


class SignupFormWithCaptcha(SignupForm):
    """
    Форма регистрации с Google reCAPTCHA v3.
    """
    accept_rules = forms.BooleanField(
        label="Я ознакомился и принимаю Правила проекта, условия модерации и юридическую информацию",
        required=True,
        error_messages={
            "required": "Для регистрации необходимо подтвердить согласие с правилами и условиями проекта."
        },
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        secret = get_admin_recaptcha_secret_key()
        if not secret:
            return cleaned_data

        if self.request is None:
            return cleaned_data

        token = self.request.POST.get("g-recaptcha-response", "") or ""
        remote_ip = self.request.META.get("REMOTE_ADDR")

        ok, score, _action = verify_recaptcha_token_v3(
            secret,
            token,
            remote_ip=remote_ip,
            expected_action="signup",
            min_score=0.5,
        )
        if not ok:
            raise ValidationError(
                f"Проверка reCAPTCHA не пройдена. Score: {score if score is not None else '—'}.",
                code="recaptcha_failed",
            )

        return cleaned_data


class SimpleLoginForm(forms.Form):
    """
    Простая форма логина без внутренних ограничений по попыткам.
    """

    login = forms.CharField(
        label="E‑mail или имя пользователя",
        widget=forms.TextInput(attrs={"placeholder": "Имя пользователя или e-mail"}),
    )
    password = forms.CharField(
        label="Пароль",
        widget=forms.PasswordInput(attrs={"placeholder": "Пароль"}),
    )
    remember = forms.BooleanField(
        label="Запомнить меня",
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop("request", None)
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned_data = super().clean()

        secret = get_admin_recaptcha_secret_key()
        if not secret:
            return cleaned_data

        if self.request is None:
            return cleaned_data

        token = self.request.POST.get("g-recaptcha-response", "") or ""
        remote_ip = self.request.META.get("REMOTE_ADDR")

        ok, score, _action = verify_recaptcha_token_v3(
            secret,
            token,
            remote_ip=remote_ip,
            expected_action="login",
            min_score=0.5,
        )
        if not ok:
            raise ValidationError(
                f"Проверка reCAPTCHA не пройдена. Score: {score if score is not None else '—'}.",
                code="recaptcha_failed",
            )

        return cleaned_data

