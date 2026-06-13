"""Solution Architect agent — Fabric IQ graph reasoning + cross-vendor optimization."""

from __future__ import annotations

from typing import Any

from ..deal_optimizer import optimize_deal
from .base import Agent, Mission


class SolutionArchitectAgent(Agent):
    name = "SolutionArchitect"

    def run(self, mission: Mission, mm: Any) -> None:
        assert mission.need is not None
        deal = optimize_deal(mission.need, mm.registry, mm.catalog, mm.fabric)
        mission.deal = deal

        # Foundry IQ: validate each chosen SKU delivers its capability (grounded).
        mission.grounding = []
        for line in deal.quote.lines:
            cap = line.capabilities[0] if line.capabilities else ""
            ans = mm.foundry.retrieve(f"{line.sku_name} {cap} license terms", limit=2)
            mission.grounding.append(ans)
            if ans.grounded:
                deal.quote.notes.append(f"[Foundry IQ] {line.sku_name}: {ans.answer}")

        vendors = sorted({line.vendor_name for line in deal.quote.lines})
        mission.say(
            self.name,
            f"Assembled a {len(vendors)}-vendor solution ({', '.join(vendors)}) covering "
            f"{len(deal.quote.covered_capabilities())} capabilities; "
            f"list ${deal.quote.list_total_annual_usd:,.0f}/yr.",
            vendors=vendors,
        )
        if deal.uncovered_capabilities:
            mission.say(
                self.name,
                "No vendor covers: " + ", ".join(deal.uncovered_capabilities) + ".",
            )
