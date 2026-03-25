from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional

from ..langvars import Lang


@dataclass
class PriceValidationResult:
    original_price: Optional[Decimal]
    price: Optional[Decimal]
    errors: list[str]


class ListingPriceService:
    """Инкапсулирует всю логику проверки и вычисления цен объявления."""

    MAX_PRICE = Decimal("999999999999999.99")

    @classmethod
    def _clean(cls, raw: str) -> str:
        return raw.replace(" ", "").replace(",", "")

    @classmethod
    def validate_for_create(
        cls,
        original_price_raw: str,
        price_raw: str,
    ) -> PriceValidationResult:
        errors: list[str] = []
        original_price_value: Optional[Decimal] = None
        price_value: Optional[Decimal] = None

        # Рыночная цена (обязательна)
        if not original_price_raw:
            errors.append(Lang.ListingValidation.ORIGINAL_REQUIRED)
        else:
            clean_original = cls._clean(original_price_raw)
            try:
                original_dec = Decimal(clean_original)
            except InvalidOperation:
                errors.append(Lang.ListingValidation.ORIGINAL_MUST_BE_NUMBER)
            else:
                if original_dec < 0:
                    errors.append(Lang.ListingValidation.ORIGINAL_NON_NEGATIVE)
                elif original_dec > cls.MAX_PRICE:
                    errors.append(Lang.ListingValidation.ORIGINAL_MAX_LIMIT)
                else:
                    original_price_value = original_dec

        # Цена со скидкой (если пусто — берём рыночную)
        if price_raw:
            clean_price = cls._clean(price_raw)
            try:
                price_dec = Decimal(clean_price)
            except InvalidOperation:
                errors.append(Lang.ListingValidation.DISCOUNT_MUST_BE_NUMBER)
            else:
                if price_dec < 0:
                    errors.append(Lang.ListingValidation.DISCOUNT_NON_NEGATIVE)
                elif price_dec > cls.MAX_PRICE:
                    errors.append(Lang.ListingValidation.DISCOUNT_MAX_LIMIT)
                else:
                    price_value = price_dec
        elif original_price_value is not None:
            price_value = original_price_value

        # Если указана цена выше рыночной — просто обнуляем скидку,
        # приравнивая её к рыночной, вместо ошибки.
        if (
            original_price_value is not None
            and price_value is not None
            and price_value > original_price_value
        ):
            price_value = original_price_value

        return PriceValidationResult(
            original_price=original_price_value,
            price=price_value,
            errors=errors,
        )

    @classmethod
    def validate_for_edit(
        cls,
        original_price_raw: str,
        price_raw: str,
        current_original: Optional[Decimal],
        current_price: Optional[Decimal],
    ) -> PriceValidationResult:
        """
        Валидация цен при редактировании:
        - пустое поле рыночной цены оставляет старое значение;
        - пустое поле цены со скидкой выравнивает её по рыночной (скидка обнуляется).
        """
        errors: list[str] = []
        original_price_value: Optional[Decimal] = None
        price_value: Optional[Decimal] = None

        # Рыночная цена
        if not original_price_raw:
            original_price_value = current_original or current_price
        else:
            clean_original = cls._clean(original_price_raw)
            try:
                original_dec = Decimal(clean_original)
            except InvalidOperation:
                errors.append(Lang.ListingValidation.ORIGINAL_MUST_BE_NUMBER)
            else:
                if original_dec < 0:
                    errors.append(Lang.ListingValidation.ORIGINAL_NON_NEGATIVE)
                elif original_dec > cls.MAX_PRICE:
                    errors.append(Lang.ListingValidation.ORIGINAL_MAX_LIMIT)
                else:
                    original_price_value = original_dec

        # Цена со скидкой
        if not price_raw:
            price_value = (
                original_price_value
                if original_price_value is not None
                else (current_price or current_original)
            )
        else:
            clean_price = cls._clean(price_raw)
            try:
                price_dec = Decimal(clean_price)
            except InvalidOperation:
                errors.append(Lang.ListingValidation.DISCOUNT_MUST_BE_NUMBER)
            else:
                if price_dec < 0:
                    errors.append(Lang.ListingValidation.DISCOUNT_NON_NEGATIVE)
                elif price_dec > cls.MAX_PRICE:
                    errors.append(Lang.ListingValidation.DISCOUNT_MAX_LIMIT)
                else:
                    price_value = price_dec

        # Аналогично созданию: если новая цена выше рыночной,
        # просто считаем, что скидки нет.
        if (
            original_price_value is not None
            and price_value is not None
            and price_value > original_price_value
        ):
            price_value = original_price_value

        return PriceValidationResult(
            original_price=original_price_value,
            price=price_value,
            errors=errors,
        )

