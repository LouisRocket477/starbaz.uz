from __future__ import annotations

from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from market.models import Message


class Command(BaseCommand):
    help = "Удаляет старые сообщения из личных диалогов (таблица market_message)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=60,
            help="Удалить сообщения старше N дней (по created_at). По умолчанию: 60.",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Подтвердить удаление. Без --yes команда работает в режиме dry-run.",
        )
        parser.add_argument(
            "--keep-per-conversation",
            type=int,
            default=0,
            help=(
                "Если > 0 — дополнительно пытается оставить последние N сообщений "
                "в каждом диалоге (даже если они старые). По умолчанию: 0 (не сохранять)."
            ),
        )

    def handle(self, *args, **options):
        days: int = options["days"]
        confirm: bool = options["yes"]
        keep_per_conversation: int = options["keep_per_conversation"]

        if days < 1:
            raise CommandError("--days должен быть >= 1")
        if keep_per_conversation < 0:
            raise CommandError("--keep-per-conversation должен быть >= 0")

        cutoff = timezone.now() - timedelta(days=days)
        qs = Message.objects.filter(created_at__lt=cutoff)

        # Опционально: исключаем последние N сообщений в каждом диалоге.
        # Реализовано без сложных оконных функций для совместимости:
        # просто берём список id “последних N” и исключаем их.
        keep_ids: set[int] = set()
        if keep_per_conversation > 0:
            convo_ids = (
                Message.objects.values_list("conversation_id", flat=True)
                .distinct()
            )
            for cid in convo_ids:
                ids = list(
                    Message.objects.filter(conversation_id=cid)
                    .order_by("-created_at")
                    .values_list("id", flat=True)[:keep_per_conversation]
                )
                keep_ids.update(ids)
            if keep_ids:
                qs = qs.exclude(id__in=keep_ids)

        total = qs.count()
        self.stdout.write(
            f"Cutoff: {cutoff:%Y-%m-%d %H:%M:%S} | candidates to delete: {total}"
        )

        if not confirm:
            self.stdout.write("Dry-run: добавь --yes чтобы удалить.")
            return

        if total == 0:
            self.stdout.write("Нечего удалять.")
            return

        with transaction.atomic():
            deleted, _ = qs.delete()
        self.stdout.write(self.style.SUCCESS(f"Удалено объектов: {deleted}"))

