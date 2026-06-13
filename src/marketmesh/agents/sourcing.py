"""Sourcing agent — turns Work IQ buyer signals into a structured BusinessNeed."""

from __future__ import annotations

from typing import Any

from .base import Agent, Mission


class SourcingAgent(Agent):
    name = "Sourcing"

    def run(self, mission: Mission, mm: Any) -> None:
        need, ctx = mm.build_need(
            mission.required_capabilities,
            description=mission.goal,
            seats=mission.seats,
            term_months=mission.term_months,
        )
        mission.buyer_context = ctx
        mission.need = need
        grounded = "Work IQ" if ctx.grounded else "defaults"
        mission.say(
            self.name,
            f"From {grounded}: {need.department} needs {need.seats} seats for "
            f"{len(need.required_capabilities)} capabilities; budget "
            f"${need.budget_annual_usd:,.0f}/yr; approver {ctx.approver or 'n/a'}.",
            seats=need.seats,
            budget=need.budget_annual_usd,
        )
