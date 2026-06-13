"""Commerce engine — cart → human approval → idempotent simulated checkout.

Implements emerging *agentic commerce* safety patterns in a synthetic sandbox:

  * **Delegated human-approval token (mandate)** bound to a specific quote fingerprint,
    so the agent can never approve its own spend or swap in a bigger cart afterwards.
  * **Per-transaction spend cap** and **budget enforcement**.
  * **Idempotent checkout** — replaying with the same key returns the same order.
  * **DRY_RUN** — orders are marked ``SIMULATED``; no real payment is captured.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field

from . import guardrails
from .config import CommerceConfig, load_settings
from .models import Quote


def _fingerprint(quote: Quote) -> str:
    parts = [quote.currency, f"{quote.net_total_annual_usd:.2f}"]
    for line in sorted(quote.lines, key=lambda x: x.sku_id):
        parts.append(f"{line.sku_id}:{line.seats}:{line.list_annual_usd:.2f}")
    return guardrails.idempotency_key(*parts)


@dataclass
class ApprovalRequest:
    id: str
    quote_fingerprint: str
    annual_usd: float
    justification: str
    status: str = "PENDING"


@dataclass
class ApprovalToken:
    token: str
    request_id: str
    quote_fingerprint: str
    approver: str
    issued_at: float


@dataclass
class Order:
    id: str
    status: str  # SIMULATED | CONFIRMED
    quote: Quote
    annual_usd: float
    approver: str
    idempotency_key: str
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "status": self.status,
            "annual_usd": round(self.annual_usd, 2),
            "approver": self.approver,
            "idempotency_key": self.idempotency_key,
            "quote": self.quote.to_dict(),
        }


class ApprovalError(guardrails.GuardrailError):
    pass


class CommerceEngine:
    def __init__(self, config: CommerceConfig | None = None) -> None:
        self.config = config or load_settings().commerce
        self._requests: dict[str, ApprovalRequest] = {}
        self._idempotency = guardrails.IdempotencyStore()
        self._orders: dict[str, Order] = {}

    # ── step 1: request approval (agent → human) ──────────────────────────
    def request_approval(self, quote: Quote, justification: str) -> ApprovalRequest:
        guardrails.assert_no_secrets(justification)  # never leak secrets in free text
        req = ApprovalRequest(
            id=f"appr_{uuid.uuid4().hex[:10]}",
            quote_fingerprint=_fingerprint(quote),
            annual_usd=quote.net_total_annual_usd,
            justification=justification,
        )
        self._requests[req.id] = req
        return req

    # ── step 2: human approves (NOT something the agent can do itself) ────
    def approve(self, request_id: str, approver: str) -> ApprovalToken:
        req = self._requests.get(request_id)
        if not req:
            raise ApprovalError(f"Unknown approval request '{request_id}'.")
        if not approver.strip():
            raise ApprovalError("An approver identity is required (human-in-the-loop).")
        req.status = "APPROVED"
        return ApprovalToken(
            token=f"tok_{uuid.uuid4().hex}",
            request_id=req.id,
            quote_fingerprint=req.quote_fingerprint,
            approver=approver,
            issued_at=time.time(),
        )

    # ── step 3: checkout (idempotent, capped, budget-enforced, DRY_RUN) ───
    def checkout(
        self,
        quote: Quote,
        approval_token: ApprovalToken,
        *,
        remaining_budget_usd: float,
        idempotency_key: str | None = None,
    ) -> Order:
        fp = _fingerprint(quote)
        if approval_token.quote_fingerprint != fp:
            raise ApprovalError(
                "Approval token does not match this quote — the cart changed after approval."
            )
        key = idempotency_key or guardrails.idempotency_key(fp, approval_token.token)
        existing_id = self._idempotency.get(key)
        if existing_id:
            return self._orders[existing_id]  # replay → same order, no double charge

        annual = quote.net_total_annual_usd
        guardrails.check_spend_cap(annual, self.config.max_transaction_usd)
        guardrails.check_budget(annual, remaining_budget_usd)

        status = "SIMULATED" if self.config.dry_run else "CONFIRMED"
        order = Order(
            id=f"ord_{uuid.uuid4().hex[:12]}",
            status=status,
            quote=quote,
            annual_usd=annual,
            approver=approval_token.approver,
            idempotency_key=key,
        )
        self._orders[order.id] = order
        self._idempotency.put(key, order.id)
        return order

    def orders(self) -> list[Order]:
        return list(self._orders.values())
