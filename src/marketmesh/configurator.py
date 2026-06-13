"""CPQ — Configure, Price, Quote.

Validates a configuration against a SKU's constraints (seat bounds, valid add-ons,
term), then prices it across the supported pricing models (per-seat, flat, usage,
tiered) and returns a :class:`QuoteLine`. Pure, deterministic, and unit-tested.
"""

from __future__ import annotations

from .models import ConfiguredItem, PricingModel, QuoteLine, Sku


class ConfigurationError(ValueError):
    """Raised when a configuration violates a SKU's constraints."""


def _annual_addons_per_seat(sku: Sku, add_on_ids: list[str], seats: int) -> float:
    monthly = 0.0
    for aid in add_on_ids:
        addon = sku.add_on(aid)
        if addon is None:
            raise ConfigurationError(f"SKU '{sku.id}' has no add-on '{aid}'.")
        monthly += addon.unit_price_monthly
    return monthly * 12 * seats


def _tier_unit_monthly(sku: Sku, seats: int) -> float:
    # Pick the first tier whose max_seats covers the requested seat count.
    for tier in sorted(sku.tiers, key=lambda t: t.max_seats):
        if seats <= tier.max_seats:
            return tier.unit_price_monthly
    # Above the highest tier → use the highest (largest-volume) tier price.
    if sku.tiers:
        return sorted(sku.tiers, key=lambda t: t.max_seats)[-1].unit_price_monthly
    return sku.unit_price_monthly


def validate(sku: Sku, item: ConfiguredItem) -> None:
    if item.seats < sku.min_seats:
        raise ConfigurationError(
            f"SKU '{sku.id}' requires at least {sku.min_seats} seats (got {item.seats})."
        )
    if item.seats > sku.max_seats:
        raise ConfigurationError(
            f"SKU '{sku.id}' allows at most {sku.max_seats} seats (got {item.seats})."
        )
    if item.term_months <= 0:
        raise ConfigurationError("term_months must be positive.")
    for aid in item.add_on_ids:
        if sku.add_on(aid) is None:
            raise ConfigurationError(f"SKU '{sku.id}' has no add-on '{aid}'.")


def price_annual(sku: Sku, item: ConfiguredItem) -> float:
    """Annualised list price (USD) for a configuration."""
    seats = item.seats
    base = 0.0
    if sku.pricing_model == PricingModel.PER_SEAT:
        base = sku.unit_price_monthly * 12 * seats
    elif sku.pricing_model == PricingModel.TIERED:
        base = _tier_unit_monthly(sku, seats) * 12 * seats
    elif sku.pricing_model == PricingModel.FLAT:
        base = sku.flat_price_annual
    elif sku.pricing_model == PricingModel.USAGE:
        # ``seats`` doubles as the estimated monthly usage-unit volume.
        base = sku.usage_price * seats * 12
    base += _annual_addons_per_seat(sku, item.add_on_ids, seats)
    return round(base, 2)


def configure(sku: Sku, item: ConfiguredItem, vendor_name: str) -> QuoteLine:
    """Validate + price a configuration into a QuoteLine."""
    validate(sku, item)
    capabilities = list(sku.capabilities)
    for aid in item.add_on_ids:
        addon = sku.add_on(aid)
        if addon:
            capabilities.extend(addon.capabilities)
    return QuoteLine(
        sku_id=sku.id,
        sku_name=sku.name,
        vendor_id=sku.vendor_id,
        vendor_name=vendor_name,
        seats=item.seats,
        term_months=item.term_months,
        add_on_ids=list(item.add_on_ids),
        list_annual_usd=price_annual(sku, item),
        capabilities=sorted(set(capabilities)),
    )
