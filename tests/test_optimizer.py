from marketmesh.catalog import Catalog
from marketmesh.deal_optimizer import optimize_deal
from marketmesh.iq.fabric_iq import FabricIQGraph
from marketmesh.models import BusinessNeed
from marketmesh.vendor_registry import VendorRegistry


def _registry():
    r = VendorRegistry()
    r.register_vendor(
        {
            "id": "a",
            "name": "Alpha",
            "products": [
                {"id": "a-bundle", "vendor_id": "a", "name": "Bundle",
                 "unit_price_monthly": 10.0, "capabilities": ["c1", "c2"]}
            ],
            "incentives": [
                {"id": "a-vol", "vendor_id": "a", "type": "volume_rebate",
                 "description": "10% at scale", "discount_pct": 0.10,
                 "min_annual_usd": 1000, "min_seats": 5}
            ],
        }
    )
    r.register_vendor(
        {
            "id": "b",
            "name": "Beta",
            "products": [
                {"id": "b-c1", "vendor_id": "b", "name": "B-C1",
                 "unit_price_monthly": 6.0, "capabilities": ["c1"]},
                {"id": "b-c2", "vendor_id": "b", "name": "B-C2",
                 "unit_price_monthly": 6.0, "capabilities": ["c2"]},
            ],
        }
    )
    return r


def _solve(required):
    r = _registry()
    cat = Catalog(r)
    fab = FabricIQGraph(r)
    need = BusinessNeed(description="t", required_capabilities=required, seats=10, term_months=12)
    return optimize_deal(need, r, cat, fab)


def test_set_cover_prefers_bundle():
    deal = _solve(["c1", "c2"])
    sku_ids = {line.sku_id for line in deal.quote.lines}
    assert sku_ids == {"a-bundle"}  # one bundle beats two single-capability SKUs
    assert deal.quote.covered_capabilities() == {"c1", "c2"}


def test_savings_vs_naive_baseline():
    deal = _solve(["c1", "c2"])
    # naive = cheapest per cap independently = 720 + 720 = 1440; optimised list = 1200
    assert deal.naive_baseline_usd == 1440.0
    assert deal.quote.list_total_annual_usd == 1200.0
    assert deal.optimization_savings_usd == 240.0


def test_incentive_applied():
    deal = _solve(["c1", "c2"])
    assert deal.quote.total_incentive_usd == 120.0  # 10% of 1200
    assert deal.quote.net_total_annual_usd == 1080.0


def test_uncovered_capability_flagged():
    deal = _solve(["c1", "c2", "zzz"])
    assert "zzz" in deal.uncovered_capabilities
    assert deal.quote.covered_capabilities() == {"c1", "c2"}


def test_cross_vendor_cosell_requires_partner():
    r = _registry()
    # add a co-sell on Beta that only triggers when Alpha is in the deal
    r.register_vendor(
        {
            "id": "b",
            "name": "Beta",
            "products": [
                {"id": "b-c3", "vendor_id": "b", "name": "B-C3",
                 "unit_price_monthly": 5.0, "capabilities": ["c3"]}
            ],
            "incentives": [
                {"id": "b-cosell", "vendor_id": "b", "type": "co_sell",
                 "description": "co-sell with Alpha", "discount_pct": 0.20,
                 "requires_vendor_ids": ["a"]}
            ],
        }
    )
    cat = Catalog(r)
    fab = FabricIQGraph(r)
    # Need c1,c2 (Alpha bundle) AND c3 (Beta) -> both vendors present -> co-sell applies
    need = BusinessNeed("t", required_capabilities=["c1", "c2", "c3"], seats=10, term_months=12)
    deal = optimize_deal(need, r, cat, fab)
    types = {i.type for i in deal.quote.incentives}
    assert "co_sell" in types
