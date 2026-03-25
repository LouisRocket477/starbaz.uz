from __future__ import annotations

"""
Общие валидаторы для загрузки файлов/картинок.

- Ограничение размера (по умолчанию до 5 МБ)
- Проверка, что файл действительно картинка (MIME/формат через Pillow)
- Разрешены только JPG / PNG / WebP
"""

from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible

try:  # Pillow уже используется в проекте для ресайза
    from PIL import Image, UnidentifiedImageError  # type: ignore
except Exception:  # pragma: no cover - Pillow обязателен в окружении
    Image = None  # type: ignore  # noqa: N816
    UnidentifiedImageError = Exception  # type: ignore


ALLOWED_IMAGE_FORMATS = {"jpeg", "jpg", "png", "webp"}


@dataclass
@deconstructible
class ImageUploadValidator:
    """
    Универсальный валидатор для ImageField.

    Проверяет:
    - максимальный размер файла (max_mb)
    - что файл корректно открывается как изображение
    - что формат входит в список разрешённых (JPG/PNG/WebP)
    """

    max_mb: int = 5

    def __post_init__(self) -> None:
        self.max_bytes = self.max_mb * 1024 * 1024

    def __call__(self, value) -> None:
        file_obj = getattr(value, "file", value)
        size = getattr(file_obj, "size", None)

        if size is not None and size > self.max_bytes:
            raise ValidationError(
                f"Размер файла слишком большой: максимум {self.max_mb} МБ."
            )

        if Image is None:
            # Если Pillow недоступен, просто пропускаем проверку формата
            return

        # Сохраняем позицию указателя и откатываем после проверки
        position = None
        if hasattr(file_obj, "tell") and hasattr(file_obj, "seek"):
            try:
                position = file_obj.tell()
            except Exception:
                position = None

        try:
            img = Image.open(file_obj)
            img.verify()  # быстрая проверка целостности
            fmt = (img.format or "").lower()
        except (UnidentifiedImageError, OSError, ValueError):
            raise ValidationError("Загрузите корректное изображение JPG, PNG или WebP.")
        finally:
            if position is not None:
                try:
                    file_obj.seek(position)
                except Exception:
                    pass

        if fmt == "jpeg":
            fmt = "jpg"

        if fmt not in ALLOWED_IMAGE_FORMATS:
            raise ValidationError("Разрешены только изображения JPG, PNG или WebP.")


image_upload_validator = ImageUploadValidator()

