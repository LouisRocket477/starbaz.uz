"""
Проверка ответа Google reCAPTCHA на стороне сервера.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request

logger = logging.getLogger(__name__)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"


def verify_recaptcha_token_v2(
    secret_key: str,
    response_token: str,
    remote_ip: str | None = None,
    timeout: float = 10.0,
) -> bool:
    if not secret_key or not (response_token or "").strip():
        return False
    data = urllib.parse.urlencode(
        {
            "secret": secret_key,
            "response": response_token.strip(),
            **({"remoteip": remote_ip} if remote_ip else {}),
        }
    ).encode()
    req = urllib.request.Request(
        RECAPTCHA_VERIFY_URL,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("reCAPTCHA verify request failed: %s", exc)
        return False
    return bool(payload.get("success"))


def verify_recaptcha_token_v3(
    secret_key: str,
    response_token: str,
    remote_ip: str | None = None,
    expected_action: str | None = None,
    min_score: float = 0.5,
    timeout: float = 10.0,
) -> tuple[bool, float | None, str | None]:
    """
    Возвращает (ok, score, action).
    ok=True если success=True, score>=min_score и (если задан expected_action) action совпал.
    """
    if not secret_key or not (response_token or "").strip():
        return (False, None, None)
    data = urllib.parse.urlencode(
        {
            "secret": secret_key,
            "response": response_token.strip(),
            **({"remoteip": remote_ip} if remote_ip else {}),
        }
    ).encode()
    req = urllib.request.Request(
        RECAPTCHA_VERIFY_URL,
        data=data,
        method="POST",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            payload = json.loads(resp.read().decode())
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        logger.warning("reCAPTCHA verify request failed: %s", exc)
        return (False, None, None)

    success = bool(payload.get("success"))
    score = payload.get("score", None)
    action = payload.get("action", None)
    try:
        score_f = float(score) if score is not None else None
    except (TypeError, ValueError):
        score_f = None

    ok = success
    if score_f is not None:
        ok = ok and score_f >= float(min_score)
    if expected_action:
        ok = ok and (action == expected_action)

    return (bool(ok), score_f, action)
