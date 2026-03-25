"""
Пример конфига gunicorn для проекта BAZAR.

Запуск (из корня проекта):
    DJANGO_SETTINGS_MODULE=bazar_site.settings_prod \\
    gunicorn bazar_site.wsgi:application -c gunicorn.conf.py
"""

bind = "127.0.0.1:8000"

# Количество воркеров — по правилу (2 * CPU) + 1
workers = 3

# Рабочий класс по умолчанию (sync) подходит для Django
worker_class = "sync"

timeout = 60
graceful_timeout = 30
max_requests = 1000
max_requests_jitter = 100

accesslog = "-"
errorlog = "-"
loglevel = "info"

