from marketmesh.agents import run_crew
from marketmesh.pipeline import MarketMesh

SCENARIO_CAPS = [
    "design", "pdf", "esign", "office_productivity", "email", "collaboration",
    "identity", "meetings", "network_security", "vpn", "analytics",
]


def test_pipeline_loads_samples():
    mm = MarketMesh()
    assert len(mm.registry) >= 4
    assert "design" in mm.catalog.capabilities()


def test_single_pipeline_end_to_end():
    mm = MarketMesh()
    need, ctx = mm.build_need(SCENARIO_CAPS, seats=None)
    assert need.seats == 200  # grounded from the Work IQ sample
    outcome = mm.solve(need, ctx)
    q = outcome.deal.quote
    assert not outcome.deal.uncovered_capabilities  # all capabilities covered
    assert len({line.vendor_id for line in q.lines}) >= 2  # genuinely cross-vendor
    assert q.net_total_annual_usd < outcome.deal.naive_baseline_usd  # optimisation saves
    order, replay = mm.transact(outcome)
    assert order.status == "SIMULATED"
    assert order.id == replay.id  # idempotent


def test_crew_end_to_end_places_order():
    mm = MarketMesh()
    mission = run_crew(mm, "Secure stack", SCENARIO_CAPS)
    assert mission.order is not None
    assert mission.order.status == "SIMULATED"
    assert not any(i.startswith("block:") for i in mission.policy_issues)


def test_live_vendor_registration_reoptimizes():
    mm = MarketMesh()
    before = mm.solve(*mm.build_need(["esign"], seats=100)).deal.quote.net_total_annual_usd
    mm.register_vendor(
        {
            "id": "lumino",
            "name": "Lumino",
            "products": [
                {"id": "lumino-sign", "vendor_id": "lumino", "name": "Lumino Sign",
                 "unit_price_monthly": 4.0, "capabilities": ["esign"]}
            ],
        }
    )
    after = mm.solve(*mm.build_need(["esign"], seats=100)).deal.quote.net_total_annual_usd
    assert after <= before  # a cheaper new vendor can only help
