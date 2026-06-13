"""Pricing agent — explains incentives and the savings story."""

from __future__ import annotations

from typing import Any

from .base import Agent, Mission


class PricingAgent(Agent):
    name = "Pricing"

    def run(self, mission: Mission, mm: Any) -> None:
        assert mission.deal is not None
        quote = mission.deal.quote
        if quote.incentives:
            detail = "; ".join(
                f"{i.type} -${i.savings_usd:,.0f}" for i in quote.incentives
            )
            mission.say(
                self.name,
                f"Applied {len(quote.incentives)} incentives ({detail}); net "
                f"${quote.net_total_annual_usd:,.0f}/yr.",
            )
        else:
            mission.say(self.name, "No incentives qualified for this deal.")
        mission.say(
            self.name,
            f"Total savings ${mission.deal.total_savings_usd:,.0f} vs naive baseline "
            f"${mission.deal.naive_baseline_usd:,.0f}/yr.",
            total_savings=mission.deal.total_savings_usd,
        )
