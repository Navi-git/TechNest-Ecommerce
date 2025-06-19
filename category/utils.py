from decimal import Decimal
from django.utils import timezone
from .models import CategoryOffer
from products.models import ProductVariant


def get_category_discount_price(variant: ProductVariant) -> Decimal:
    """
    Returns the discounted price for a variant based on its category offer.
    If no active category offer, returns the original price.
    """
    product = variant.product
    base_price = variant.price

    category_offer = getattr(product.category, 'offer', None)
    if category_offer and category_offer.start_date <= timezone.now().date() <= category_offer.end_date:
        discount_percent = category_offer.discount_percentage
        discount_amount = base_price * (Decimal(discount_percent) / Decimal('100'))
        return base_price - discount_amount
    return base_price


def get_variant_discount_price(variant: ProductVariant) -> Decimal:
    """
    Returns the variant's own discounted price if available.
    """
    return variant.discount if variant.discount > 0 else variant.price


def get_best_discounted_price(variant: ProductVariant) -> Decimal:
    """
    Returns the better of category offer price and variant discount price.
    Prioritizes the lowest price (maximum discount for user).
    """
    variant_price = get_variant_discount_price(variant)
    category_price = get_category_discount_price(variant)
    return min(variant_price, category_price)


def get_discount_summary(variant: ProductVariant) -> dict:
    """
    Optional helper: Returns a breakdown of which discount applied.
    Useful for admin/debugging/logging.
    """
    base_price = variant.price
    variant_price = get_variant_discount_price(variant)
    category_price = get_category_discount_price(variant)

    best_price = min(variant_price, category_price)
    applied_offer = "variant" if variant_price <= category_price else "category"

    return {
        "base_price": base_price,
        "variant_price": variant_price,
        "category_price": category_price,
        "best_price": best_price,
        "applied_offer": applied_offer,
        "discount_percentage": round(((base_price - best_price) / base_price) * 100, 2) if base_price > 0 else 0
    }
