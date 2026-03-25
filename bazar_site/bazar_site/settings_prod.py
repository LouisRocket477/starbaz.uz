"""
Продакшн‑настройки Django для BAZAR.

Используются вместе со стеком:
- PostgreSQL — основная БД
- Redis — кэш + rate limit
- Gunicorn — WSGI‑сервер
- Nginx — reverse proxy и статика

Запуск:
    export DJANGO_SETTINGS_MODULE=bazar_site.settings_prod
    gunicorn bazar_site.wsgi:application ...
"""

import os

from .settings import *  # noqa

# === Базовые флаги ===

DEBUG = False

# Сюда добавь реальные домены/IPv4 сервера
ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


# === PostgreSQL как основная БД ===
# Параметры берём из переменных окружения, с безопасными значениями по умолчанию.

DB_NAME = os.environ.get("BAZAR_DB_NAME", "bazar")
DB_USER = os.environ.get("BAZAR_DB_USER", "bazar")
DB_PASSWORD = os.environ.get("BAZAR_DB_PASSWORD", "CHANGE_ME_STRONG_PASSWORD")
DB_HOST = os.environ.get("BAZAR_DB_HOST", "127.0.0.1")
DB_PORT = os.environ.get("BAZAR_DB_PORT", "5432")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": DB_NAME,
        "USER": DB_USER,
        "PASSWORD": DB_PASSWORD,
        "HOST": DB_HOST,
        "PORT": DB_PORT,
    }
}


# === Redis для кэша и rate‑limit ===

REDIS_URL = os.environ.get("BAZAR_REDIS_URL", "redis://127.0.0.1:6379/0")
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": REDIS_URL,
    }
}

# Сессии через кэш (можно отключить, если не нужно)
SESSION_ENGINE = "django.contrib.sessions.backends.cache"
SESSION_CACHE_ALIAS = "default"


# === Безопасность и HTTPS за Nginx ===

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"


# === Логирование в файл на сервере ===

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "WARNING",
            "class": "logging.FileHandler",
            "filename": "/var/log/bazar/django.log",
        },
        "console": {
            "level": "INFO",
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
}

