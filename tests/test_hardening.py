"""Regression tests for issues found in code review (hardening pass)."""

import pytest

from marketmesh.catalog import Catalog
from marketmesh.deal_optimizer import optimize_deal
from marketmesh.guardrails import GuardrailError
from marketmesh.iq.fabric_iq import FabricIQGraph
from marketmesh.models import BusinessNeed
from marketmesh.pipeline import MarketMesh
from marketmesh.vendor_registry import VendorRegistry


def _solve(registry, required, seats):
    cat = Catalog(registry)
    fab = FabricIQGraph(registry)
    need = BusinessNeed("t", required_capabilities=required, seats=seats, term_months=12)
    return optimize_deal(need, registry, cat, fab)


# ── Issue: seats above a SKU's ceiling must not be silently under-provisioned ──
def test_seat_ceiling_rejects_candidate():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "v",
            "name": "V",
            "products": [
                {"id": "small", "vendor_id": "v", "name": "Small", "unit_price_monthly": 10.0,
                 "max_seats": 50, "capabilities": ["cap"]}
            ],
        }
    )
    deal = _solve(r, ["cap"], seats=200)  # need exceeds the SKU's 50-seat ceiling
    assert "cap" in deal.uncovered_capabilities
    assert deal.quote.lines == []  # nothing under-provisioned


def test_seat_ceiling_ok_when_within_bounds():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "v",
            "name": "V",
            "products": [
                {"id": "ok", "vendor_id": "v", "name": "OK", "unit_price_monthly": 10.0,
                 "max_seats": 500, "capabilities": ["cap"]}
            ],
        }
    )
    deal = _solve(r, ["cap"], seats=200)
    assert deal.uncovered_capabilities == []
    assert deal.quote.lines[0].seats == 200


# ── Issue: incentive applies_to_categories must scope the discounted subtotal ──
def test_incentive_category_scoping():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "a",
            "name": "Alpha",
            "products": [
                {"id": "a1", "vendor_id": "a", "name": "A1", "unit_price_monthly": 10.0,
                 "category_code": "100", "capabilities": ["c1"]},
                {"id": "a2", "vendor_id": "a", "name": "A2", "unit_price_monthly": 10.0,
                 "category_code": "200", "capabilities": ["c2"]},
            ],
            "incentives": [
                {"id": "a-cat", "vendor_id": "a", "type": "volume_rebate",
                 "description": "cat-100 only", "discount_pct": 0.10,
                 "applies_to_categories": ["100"]}
            ],
        }
    )
    deal = _solve(r, ["c1", "c2"], seats=100)
    # Each line = 10*12*100 = 12000. Discount applies ONLY to the category-100 line.
    assert deal.quote.total_incentive_usd == 1200.0  # 10% of 12000, not of 24000


# ── Issue: deterministic incentive order (largest discount credited first) ──
def test_incentive_ordering_deterministic():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "a",
            "name": "Alpha",
            "products": [
                {"id": "a1", "vendor_id": "a", "name": "A1", "unit_price_monthly": 100.0,
                 "capabilities": ["c1"]}
            ],
            "incentives": [
                {"id": "small", "vendor_id": "a", "type": "promo",
                 "description": "5%", "discount_pct": 0.05},
                {"id": "big", "vendor_id": "a", "type": "co_sell",
                 "description": "40%", "discount_pct": 0.40, "requires_vendor_ids": ["a"]},
            ],
        }
    )
    deal = _solve(r, ["c1"], seats=10)
    # Cap is 40% per vendor; the 40% incentive should be credited first and in full.
    assert deal.quote.incentives[0].incentive_id == "big"
    assert deal.quote.total_incentive_usd == round(0.40 * deal.quote.list_total_annual_usd, 2)


# ── Issue: crew must not drop a mandatory capability and must not place empty orders ──
def test_crew_blocks_when_mandatory_identity_uncoverable():
    from marketmesh.agents import run_crew

    mm = MarketMesh(load_samples=False)
    mm.register_vendor(
        {"id": "v", "name": "V",
         "products": [{"id": "mail", "vendor_id": "v", "name": "Mail", "unit_price_monthly": 5.0,
                       "capabilities": ["email"]}]}
    )
    mission = run_crew(mm, "stack", ["email", "identity"], seats=50)
    assert mission.order is None  # mandatory identity uncoverable → no order
    assert any(i.startswith("block:") for i in mission.policy_issues)


def test_crew_blocks_when_nothing_coverable():
    from marketmesh.agents import run_crew

    mm = MarketMesh(load_samples=False)
    mm.register_vendor(
        {"id": "v", "name": "V",
         "products": [{"id": "mail", "vendor_id": "v", "name": "Mail", "unit_price_monthly": 5.0,
                       "capabilities": ["email"]}]}
    )
    mission = run_crew(mm, "stack", ["totally_unknown_cap"], seats=10)
    assert mission.order is None  # no $0 empty order is ever placed
    assert any("no products" in i for i in mission.policy_issues)


# ── Issue: single pipeline transact must refuse an empty quote ──
def test_transact_refuses_empty_quote():
    mm = MarketMesh()  # loads samples
    need, ctx = mm.build_need(["nonexistent_capability"], seats=10)
    outcome = mm.solve(need, ctx)
    assert outcome.deal.quote.lines == []
    with pytest.raises(GuardrailError):
        mm.transact(outcome)
