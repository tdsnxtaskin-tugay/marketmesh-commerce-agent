"""Closer agent — human approval (simulated) + idempotent simulated checkout."""

from __future__ import annotations

from typing import Any

from .base import Agent, Mission


class CloserAgent(Agent):
    name = "Closer"

    def run(self, mission: Mission, mm: Any) -> None:
        assert mission.deal is not None and mission.buyer_context is not None
        quote = mission.deal.quote
        ctx = mission.buyer_context
        approver = ctx.approver or "approver@example.com"
        justification = (
            f"Capability-complete, right-sized deal for {mission.need.department}."
            if mission.need
            else "Software purchase."
        )
        budget = ctx.budget_annual_usd or mm.settings.commerce.default_budget_usd

        req = mm.commerce.request_approval(quote, justification)
        token = mm.commerce.approve(req.id, approver)  # human-in-the-loop
        order = mm.commerce.checkout(quote, token, remaining_budget_usd=budget)
        replay = mm.commerce.checkout(quote, token, remaining_budget_usd=budget)
        mission.order = order
        mission.replay = replay
        mission.say(
            self.name,
            f"{order.status} order {order.id} for ${order.annual_usd:,.0f}/yr, approved by "
            f"{approver}. Replay returned the same order (idempotent, no double charge).",
            order_id=order.id,
        )
