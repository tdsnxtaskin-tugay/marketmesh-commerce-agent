"""Cross-vendor deal optimizer — the multi-step reasoning core.

Given a business need (a set of required capabilities + seats + term), it:

  1. Decomposes the need into capabilities (Fabric IQ ontology).
  2. Finds candidate SKUs per capability across every registered vendor.
  3. Runs a **greedy, cost-minimising set cover**: it repeatedly picks the SKU that
     covers the most still-needed capabilities per dollar, until everything coverable is
     covered. This is a fast approximation (not a guaranteed-optimal exact cover) that
     favours multi-capability SKUs and avoids selecting SKUs that add no new coverage.
  4. Configures + prices each chosen SKU (CPQ).
  5. Applies marketing / co-sell / volume incentives **after** selection (a common CPQ
     pattern). Note this means selection minimises *list* price; incentive-aware global
     optimisation is a documented extension.
  6. Reports the delta vs a naive one-SKU-per-capability baseline.

A SKU is only considered for a capability if it can serve the requested seat count
(``need.seats <= sku.max_seats``); capabilities that cannot be assigned are reported as
uncovered rather than silently under-provisioned.

Pure and deterministic, so the rationale is fully auditable.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import Catalog
from .configurator import price_annual
from .iq.fabric_iq import FabricIQGraph
from .models import (
    AppliedIncentive,
    BusinessNeed,
    ConfiguredItem,
    Incentive,
    IncentiveType,
    Quote,
    QuoteLine,
    Sku,
)
from .vendor_registry import VendorRegistry

MAX_VENDOR_DISCOUNT = 0.40  # realism cap on stacked incentives per vendor


@dataclass
class Candidate:
    sku: Sku
    item: ConfiguredItem
    covers: set[str]
    cost_annual: float


@dataclass
class DealResult:
    quote: Quote
    uncovered_capabilities: list[str] = field(default_factory=list)
    naive_baseline_usd: float = 0.0
    reasoning_steps: list[str] = field(default_factory=list)

    @property
    def optimization_savings_usd(self) -> float:
        return round(self.naive_baseline_usd - self.quote.list_total_annual_usd, 2)

    @property
    def total_savings_usd(self) -> float:
        return round(self.naive_baseline_usd - self.quote.net_total_annual_usd, 2)

    def to_dict(self) -> dict:
        return {
            "quote": self.quote.to_dict(),
            "uncovered_capabilities": list(self.uncovered_capabilities),
            "naive_baseline_usd": round(self.naive_baseline_usd, 2),
            "optimization_savings_usd": self.optimization_savings_usd,
            "total_savings_usd": self.total_savings_usd,
            "reasoning_steps": list(self.reasoning_steps),
        }


def _seats_for(sku: Sku, need: BusinessNeed) -> int:
    # Clamp up to the SKU minimum (you must buy at least the minimum), but never
    # clamp *down*: a SKU that cannot serve the requested seats is rejected as a
    # candidate (see _candidate_for) rather than silently under-provisioning.
    return max(need.seats, sku.min_seats)


def _candidate_for(sku: Sku, needed: set[str], need: BusinessNeed) -> Candidate | None:
    """Build the cheapest configuration of ``sku`` that covers some of ``needed``.

    Returns ``None`` when the SKU cannot genuinely serve the need — either it covers
    none of the needed capabilities, or its seat ceiling is below the requested seats
    (we never quietly buy fewer seats than the buyer asked for).
    """
    if need.seats > sku.max_seats:
        return None
    base_cover = set(sku.capabilities) & needed
    chosen_addons: list[str] = []
    addon_cover: set[str] = set()
    for addon in sku.add_ons:
        contrib = (set(addon.capabilities) & needed) - base_cover - addon_cover
        if contrib:
            chosen_addons.append(addon.id)
            addon_cover |= contrib
    covers = base_cover | addon_cover
    if not covers:
        return None
    item = ConfiguredItem(
        sku_id=sku.id,
        vendor_id=sku.vendor_id,
        seats=_seats_for(sku, need),
        term_months=need.term_months,
        add_on_ids=chosen_addons,
    )
    cost = price_annual(sku, item)
    if cost < 0:  # defensive: prices must be non-negative
        return None
    return Candidate(sku=sku, item=item, covers=covers, cost_annual=cost)


def _naive_baseline(catalog: Catalog, need: BusinessNeed, required: set[str]) -> float:
    """Cheapest single SKU per capability, bought independently (with overlap)."""
    total = 0.0
    for cap in required:
        cheapest: float | None = None
        for sku in catalog.skus_for_capability(cap):
            cand = _candidate_for(sku, {cap}, need)
            if cand and (cheapest is None or cand.cost_annual < cheapest):
                cheapest = cand.cost_annual
        if cheapest is not None:
            total += cheapest
    return round(total, 2)


def optimize_deal(
    need: BusinessNeed,
    registry: VendorRegistry,
    catalog: Catalog,
    fabric: FabricIQGraph,
) -> DealResult:
    required = set(need.required_capabilities)
    steps: list[str] = []
    steps.append(
        f"Decomposed need into {len(required)} capabilities: {', '.join(sorted(required))}."
    )

    uncovered_all = set(fabric.uncovered(sorted(required)))
    coverable = required - uncovered_all
    if uncovered_all:
        steps.append(
            "No registered vendor covers: " + ", ".join(sorted(uncovered_all)) + "."
        )

    # ── greedy cost-minimising set cover over all vendors' SKUs ──
    # (a greedy approximation, not a guaranteed-optimal exact cover; it prefers SKUs
    #  that cover the most new capabilities per dollar.)
    remaining = set(coverable)
    chosen: list[Candidate] = []
    chosen_sku_ids: set[str] = set()
    while remaining:
        best: Candidate | None = None
        best_ratio = -1.0
        for sku in catalog.registry.all_products():
            if sku.id in chosen_sku_ids:
                continue
            cand = _candidate_for(sku, remaining, need)
            if not cand:
                continue
            new_cover = cand.covers & remaining
            if not new_cover:
                continue
            # Capabilities-per-dollar; a free SKU is infinitely attractive.
            ratio = float("inf") if cand.cost_annual == 0 else len(new_cover) / cand.cost_annual
            if ratio > best_ratio or (
                ratio == best_ratio and best and cand.cost_annual < best.cost_annual
            ):
                best, best_ratio = cand, ratio
        if best is None:
            break
        chosen.append(best)
        chosen_sku_ids.add(best.sku.id)
        newly = best.covers & remaining
        remaining -= best.covers
        steps.append(
            f"Selected {best.sku.name} ({catalog.vendor_name(best.sku.vendor_id)}) "
            f"covering {', '.join(sorted(newly))} at ${best.cost_annual:,.0f}/yr."
        )

    # Any capability we could not actually assign (e.g. only available on a SKU whose
    # seat ceiling is too low) is reported as uncovered — never silently hidden.
    if remaining:
        uncovered_all |= remaining
        steps.append(
            "Could not assemble coverage for: " + ", ".join(sorted(remaining)) + "."
        )

    # ── build the quote ──
    quote = Quote(currency=need_currency(need))
    for cand in chosen:
        caps = sorted((set(cand.sku.capabilities) | _addon_caps(cand)) & coverable)
        quote.lines.append(
            QuoteLine(
                sku_id=cand.sku.id,
                sku_name=cand.sku.name,
                vendor_id=cand.sku.vendor_id,
                vendor_name=catalog.vendor_name(cand.sku.vendor_id),
                seats=cand.item.seats,
                term_months=cand.item.term_months,
                add_on_ids=list(cand.item.add_on_ids),
                list_annual_usd=cand.cost_annual,
                capabilities=caps,
                category_code=cand.sku.category_code,
            )
        )

    vendors_in_deal = {line.vendor_id for line in quote.lines}
    if len(vendors_in_deal) > 1:
        steps.append(
            f"Assembled a {len(vendors_in_deal)}-vendor solution, minimising redundant "
            "SKU selection across vendors."
        )

    # ── incentives ──
    applied = apply_incentives(quote, registry)
    quote.incentives = applied
    for inc in applied:
        steps.append(
            f"Applied {inc.type} incentive from {registry.vendor_name(inc.vendor_id)}: "
            f"-${inc.savings_usd:,.0f} ({inc.description})."
        )

    baseline = _naive_baseline(catalog, need, coverable)
    result = DealResult(
        quote=quote,
        uncovered_capabilities=sorted(uncovered_all),
        naive_baseline_usd=baseline,
        reasoning_steps=steps,
    )
    steps.append(
        f"Optimized list ${quote.list_total_annual_usd:,.0f} vs naive baseline "
        f"${baseline:,.0f}; net after incentives ${quote.net_total_annual_usd:,.0f}."
    )
    return result


def _addon_caps(cand: Candidate) -> set[str]:
    out: set[str] = set()
    for aid in cand.item.add_on_ids:
        addon = cand.sku.add_on(aid)
        if addon:
            out.update(addon.capabilities)
    return out


def need_currency(need: BusinessNeed) -> str:
    return "USD"


def _incentive_applies(inc: Incentive, quote: Quote) -> bool:
    vendors = {line.vendor_id for line in quote.lines}
    if inc.type in (IncentiveType.CO_SELL, IncentiveType.BUNDLE):
        # Cross-vendor incentive: every required partner vendor must be in the deal.
        if not inc.requires_vendor_ids:
            return False
        if not set(inc.requires_vendor_ids).issubset(vendors):
            return False
    return True


def _vendor_applicable_subtotal(inc: Incentive, quote: Quote) -> tuple[float, int]:
    """Subtotal + max seats of the lines an incentive actually applies to.

    Restricted to the incentive's vendor and, when ``applies_to_categories`` is set,
    to lines whose SKU category code is in that list — so a category-scoped incentive
    never discounts (or unlocks its threshold from) unrelated spend.
    """
    categories = set(inc.applies_to_categories)
    subtotal = 0.0
    seats = 0
    for line in quote.lines:
        if line.vendor_id != inc.vendor_id:
            continue
        if categories and line.category_code not in categories:
            continue
        subtotal += line.list_annual_usd
        seats = max(seats, line.seats)
    return round(subtotal, 2), seats


def apply_incentives(quote: Quote, registry: VendorRegistry) -> list[AppliedIncentive]:
    """Apply qualifying incentives, capping cumulative discount per vendor.

    Incentives are evaluated in a deterministic order — largest discount first, then by
    id — so that when the per-vendor cap binds, the most valuable incentive is credited
    first and the outcome does not depend on registration order.
    """
    applied: list[AppliedIncentive] = []
    vendor_discounted: dict[str, float] = {}
    incentives = sorted(
        registry.all_incentives(), key=lambda i: (-i.discount_pct, i.vendor_id, i.id)
    )
    for inc in incentives:
        if not _incentive_applies(inc, quote):
            continue
        subtotal, seats = _vendor_applicable_subtotal(inc, quote)
        if subtotal <= 0:
            continue
        if subtotal < inc.min_annual_usd or seats < inc.min_seats:
            continue
        already = vendor_discounted.get(inc.vendor_id, 0.0)
        cap_room = max(0.0, MAX_VENDOR_DISCOUNT - already)
        effective_pct = min(inc.discount_pct, cap_room)
        if effective_pct <= 0:
            continue
        savings = round(subtotal * effective_pct, 2)
        vendor_discounted[inc.vendor_id] = already + effective_pct
        applied.append(
            AppliedIncentive(
                incentive_id=inc.id,
                vendor_id=inc.vendor_id,
                type=inc.type.value,
                description=inc.description,
                savings_usd=savings,
            )
        )
    return applied
