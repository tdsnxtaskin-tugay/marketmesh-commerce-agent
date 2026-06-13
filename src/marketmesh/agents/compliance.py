"""Compliance agent — policy gates + guardrails before any spend is requested."""

from __future__ import annotations

from typing import Any

from .. import guardrails
from .base import Agent, Mission

MANDATORY_CAPABILITY = "identity"  # IT standard: SSO/identity required for new SaaS


class ComplianceAgent(Agent):
    name = "Compliance"

    def run(self, mission: Mission, mm: Any) -> None:
        assert mission.deal is not None and mission.need is not None
        mission.policy_issues = []
        quote = mission.deal.quote
        net = quote.net_total_annual_usd

        # 1) Replannable gate: required capabilities that no vendor covers.
        if mission.deal.uncovered_capabilities:
            for cap in mission.deal.uncovered_capabilities:
                mission.policy_issues.append(f"uncovered:{cap}")

        # 2) Policy gate: mandatory identity/SSO when requested.
        covered = quote.covered_capabilities()
        if MANDATORY_CAPABILITY in mission.need.required_capabilities and (
            MANDATORY_CAPABILITY not in covered
        ):
            mission.policy_issues.append("missing:identity")

        # 3) Hard guardrails: spend cap + budget (blocking).
        try:
            guardrails.check_spend_cap(net, mm.settings.commerce.max_transaction_usd)
        except guardrails.GuardrailError as exc:
            mission.policy_issues.append(f"block:{exc}")
        try:
            guardrails.check_budget(net, mission.need.budget_annual_usd)
        except guardrails.GuardrailError as exc:
            mission.policy_issues.append(f"block:{exc}")

        if mission.policy_issues:
            mission.say(self.name, "Policy issues: " + "; ".join(mission.policy_issues))
        else:
            mission.say(
                self.name,
                f"All gates passed: identity present, ${net:,.0f}/yr within cap and budget. "
                "Routing for human approval.",
            )
