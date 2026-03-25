# Продакшн‑деплой BAZAR

Этот каталог содержит инфраструктурные конфиги для стандартного стека:

- **Nginx** — reverse proxy, статика/медиа, базовый rate limit.
- **Gunicorn** — WSGI‑сервер Django.
- **PostgreSQL** — основная база.
- **Redis** — кэш Django и backend для rate‑limit middleware.

## 1. Django (settings_prod.py)

Используй файл `bazar_site/settings_prod.py`:

```bash
export DJANGO_SETTINGS_MODULE=bazar_site.settings_prod
python manage.py collectstatic
```

Настройки БД и Redis берутся из переменных окружения:

- `BAZAR_DB_NAME`, `BAZAR_DB_USER`, `BAZAR_DB_PASSWORD`, `BAZAR_DB_HOST`, `BAZAR_DB_PORT`
- `BAZAR_REDIS_URL`

## 2. Gunicorn (systemd)

Пример юнита: `deploy/systemd.bazar-gunicorn.service`.

Скопируй его в `/etc/systemd/system/bazar-gunicorn.service`, поправь пути
(`/srv/bazar_site`, путь к venv) и пароль БД, затем:

```bash
sudo systemctl daemon-reload
sudo systemctl enable bazar-gunicorn
sudo systemctl start bazar-gunicorn
```

## 3. Nginx

Пример конфига: `deploy/nginx.bazar.conf`.

Скопируй его в `/etc/nginx/sites-available/bazar`, поправь `server_name`
и пути к `static`/`media`, затем:

```bash
sudo ln -s /etc/nginx/sites-available/bazar /etc/nginx/sites-enabled/bazar
sudo nginx -t
sudo systemctl reload nginx
```

## 4. PostgreSQL и Redis

Минимальный пример создания базы:

```bash
sudo -u postgres createuser bazar --pwprompt
sudo -u postgres createdb bazar -O bazar
```

Redis можно использовать с настройками по умолчанию (`redis://127.0.0.1:6379/0`),
они уже заложены в `settings_prod.py` как дефолт.

