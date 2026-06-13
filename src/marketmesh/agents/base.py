"""Optional multi-agent crew.

The same deterministic pipeline, re-expressed as a small crew of specialised agents
collaborating on a shared *Mission* blackboard. This makes the multi-step reasoning
explicit and demoable, and adds a bounded replan loop when a policy gate fails.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..commerce import Order
from ..deal_optimizer import DealResult
from ..iq.foundry_iq import GroundedAnswer
from ..iq.work_iq import BuyerContext
from ..models import BusinessNeed


@dataclass
class AgentMessage:
    agent: str
    content: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class Mission:
    """Shared blackboard the crew reads from and writes to."""

    goal: str
    required_capabilities: list[str]
    seats: int | None = None
    term_months: int = 12

    buyer_context: BuyerContext | None = None
    need: BusinessNeed | None = None
    deal: DealResult | None = None
    grounding: list[GroundedAnswer] = field(default_factory=list)
    order: Order | None = None
    replay: Order | None = None

    policy_issues: list[str] = field(default_factory=list)
    replans: int = 0
    log: list[AgentMessage] = field(default_factory=list)

    def say(self, agent: str, content: str, **data: Any) -> None:
        self.log.append(AgentMessage(agent=agent, content=content, data=data))

    def transcript(self) -> str:
        return "\n".join(f"[{m.agent}] {m.content}" for m in self.log)


class Agent:
    name = "agent"

    def run(self, mission: Mission, mm: Any) -> None:  # pragma: no cover - interface
        raise NotImplementedError
