"""Crew orchestrator with a bounded replan loop."""

from __future__ import annotations

from typing import Any

from .base import Mission
from .closer import CloserAgent
from .compliance import ComplianceAgent
from .pricing import PricingAgent
from .solution_architect import SolutionArchitectAgent
from .sourcing import SourcingAgent

MAX_REPLANS = 1


def _replannable(issues: list[str]) -> list[str]:
    # Only non-mandatory uncovered capabilities may be dropped and retried. Mandatory
    # gaps are emitted as `block:` issues by ComplianceAgent and are never droppable.
    caps = []
    for issue in issues:
        if issue.startswith("uncovered:"):
            caps.append(issue.split(":", 1)[1])
    return caps


def _blocking(issues: list[str]) -> bool:
    return any(i.startswith("block:") for i in issues)


def run_crew(
    mm: Any,
    goal: str,
    required_capabilities: list[str],
    *,
    seats: int | None = None,
    term_months: int = 12,
) -> Mission:
    mission = Mission(
        goal=goal,
        required_capabilities=list(required_capabilities),
        seats=seats,
        term_months=term_months,
    )

    architect = SolutionArchitectAgent()
    pricing = PricingAgent()
    compliance = ComplianceAgent()

    SourcingAgent().run(mission, mm)
    architect.run(mission, mm)
    pricing.run(mission, mm)
    compliance.run(mission, mm)

    # Bounded replan: drop capabilities no vendor can cover and try once more.
    while (
        mission.replans < MAX_REPLANS
        and not _blocking(mission.policy_issues)
        and _replannable(mission.policy_issues)
    ):
        drop = set(_replannable(mission.policy_issues))
        assert mission.need is not None
        kept = [c for c in mission.need.required_capabilities if c not in drop]
        mission.replans += 1
        mission.say(
            "Crew",
            f"Replan {mission.replans}: dropping unfulfillable capabilities "
            f"{', '.join(sorted(drop))} and re-optimizing.",
        )
        mission.need.required_capabilities = kept
        mission.required_capabilities = kept
        architect.run(mission, mm)
        pricing.run(mission, mm)
        compliance.run(mission, mm)

    if _blocking(mission.policy_issues):
        mission.say("Crew", "Checkout blocked by a hard guardrail — no order placed.")
        return mission

    CloserAgent().run(mission, mm)
    return mission
