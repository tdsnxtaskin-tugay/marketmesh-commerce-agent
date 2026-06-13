import pytest

from marketmesh.configurator import ConfigurationError, configure, price_annual
from marketmesh.models import AddOn, ConfiguredItem, PricingModel, Sku, Tier


def _per_seat_sku():
    return Sku(
        id="s1",
        vendor_id="v",
        name="Suite",
        pricing_model=PricingModel.PER_SEAT,
        unit_price_monthly=10.0,
        min_seats=5,
        max_seats=1000,
        capabilities=["a"],
        add_ons=[AddOn(id="x", name="X", unit_price_monthly=2.0, capabilities=["b"])],
    )


def test_per_seat_pricing():
    sku = _per_seat_sku()
    item = ConfiguredItem("s1", "v", seats=50, term_months=12, add_on_ids=[])
    # 10 * 12 * 50
    assert price_annual(sku, item) == 6000.0


def test_addon_pricing_and_capabilities():
    sku = _per_seat_sku()
    item = ConfiguredItem("s1", "v", seats=10, term_months=12, add_on_ids=["x"])
    line = configure(sku, item, "Vendor")
    # (10 + 2) * 12 * 10
    assert line.list_annual_usd == 1440.0
    assert set(line.capabilities) == {"a", "b"}


def test_seat_bounds_enforced():
    sku = _per_seat_sku()
    with pytest.raises(ConfigurationError):
        configure(sku, ConfiguredItem("s1", "v", seats=1, term_months=12), "V")


def test_unknown_addon_rejected():
    sku = _per_seat_sku()
    with pytest.raises(ConfigurationError):
        configure(sku, ConfiguredItem("s1", "v", seats=10, term_months=12, add_on_ids=["nope"]), "V")


def test_tiered_pricing_picks_correct_tier():
    sku = Sku(
        id="t1",
        vendor_id="v",
        name="Tiered",
        pricing_model=PricingModel.TIERED,
        tiers=[Tier(100, 26.0), Tier(1000, 22.0)],
        min_seats=1,
        max_seats=100000,
        capabilities=["a"],
    )
    # 200 seats -> 22/seat tier: 22 * 12 * 200
    assert price_annual(sku, ConfiguredItem("t1", "v", seats=200, term_months=12)) == 52800.0


def test_flat_pricing():
    sku = Sku(id="f1", vendor_id="v", name="Flat", pricing_model=PricingModel.FLAT,
              flat_price_annual=9000.0, capabilities=["a"])
    assert price_annual(sku, ConfiguredItem("f1", "v", seats=1, term_months=12)) == 9000.0
