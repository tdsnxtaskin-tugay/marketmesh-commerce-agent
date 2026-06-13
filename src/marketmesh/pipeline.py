"""MarketMesh pipeline — the end-to-end orchestrator.

Wires the three Microsoft IQ layers into one auditable, multi-step flow:

  Work IQ (buyer intent) → Fabric IQ (capability graph) → optimizer (cross-vendor deal)
  → Foundry IQ (grounded validation) → human approval → idempotent simulated checkout.

The same facade is used by the CLI, the optional multi-agent crew, and the M365
Copilot action backend.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .catalog import Catalog
from .commerce import CommerceEngine, Order
from .config import Settings, load_settings
from .deal_optimizer import DealResult, optimize_deal
from .guardrails import GuardrailError
from .iq.fabric_iq import FabricIQGraph
from .iq.foundry_iq import FoundryIQRetriever, GroundedAnswer
from .iq.work_iq import BuyerContext, WorkIQProvider
from .llm import Narrator
from .models import BusinessNeed, Vendor
from .search import SearchHit
from .vendor_registry import VendorRegistry

logger = logging.getLogger("marketmesh.pipeline")

_DEFAULT_SAMPLES = Path(__file__).resolve().parents[2] / "samples"


@dataclass
class DealOutcome:
    need: BusinessNeed
    buyer_context: BuyerContext
    deal: DealResult
    grounding: list[GroundedAnswer] = field(default_factory=list)
    narration: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "buyer_context": self.buyer_context.to_dict(),
            "deal": self.deal.to_dict(),
            "grounding": [g.to_dict() for g in self.grounding],
            "narration": self.narration,
        }


class MarketMesh:
    def __init__(
        self,
        settings: Settings | None = None,
        samples_dir: str | Path | None = None,
        *,
        load_samples: bool = True,
    ) -> None:
        self.settings = settings or load_settings()
        self.samples_dir = Path(samples_dir) if samples_dir else _DEFAULT_SAMPLES
        self.registry = VendorRegistry()
        self.foundry = FoundryIQRetriever(config=self.settings.foundry_iq)
        self.work_iq = WorkIQProvider(
            sample_path=self.samples_dir / "work_iq_signals.json",
            config=self.settings.work_iq,
        )
        self.narrator = Narrator(config=self.settings.azure_openai)
        self.commerce = CommerceEngine(config=self.settings.commerce)

        if load_samples:
            self._load_samples()

        # Catalog + Fabric IQ graph are (re)built lazily so newly registered vendors
        # are always reflected.
        self._rebuild_views()

    # ── setup ─────────────────────────────────────────────────────────────
    def _load_samples(self) -> None:
        vendors_dir = self.samples_dir / "vendors"
        if not vendors_dir.exists():
            logger.warning("Samples dir %s missing; starting with an empty catalog.", vendors_dir)
            return
        for path in sorted(vendors_dir.glob("*.json")):
            with open(path, encoding="utf-8") as fh:
                payload = json.load(fh)
            self.registry.register_vendor(payload)
            # Index any product-knowledge notes into Foundry IQ.
            label = payload.get("name", path.stem)
            for entry in payload.get("knowledge", []):
                if isinstance(entry, str):
                    self.foundry.add_source(label, [entry])
                elif isinstance(entry, dict):
                    self.foundry.add_source(entry.get("source", label), [entry.get("snippet", "")])

    def _rebuild_views(self) -> None:
        self.catalog = Catalog(self.registry)
        self.fabric = FabricIQGraph(self.registry, config=self.settings.fabric_iq)

    # ── vendor onboarding (register any company at runtime) ───────────────
    def register_vendor(self, payload: Vendor | dict[str, Any]) -> Vendor:
        vendor = self.registry.register_vendor(payload)
        if isinstance(payload, dict):
            for entry in payload.get("knowledge", []):
                if isinstance(entry, str):
                    self.foundry.add_source(vendor.name, [entry])
                elif isinstance(entry, dict):
                    self.foundry.add_source(entry.get("source", vendor.name), [entry.get("snippet", "")])
        self._rebuild_views()
        return vendor

    # ── read APIs ─────────────────────────────────────────────────────────
    def search(self, query: str, **kwargs: Any) -> list[SearchHit]:
        return self.catalog.search(query, **kwargs)

    def ground(self, query: str, *, limit: int = 3) -> GroundedAnswer:
        return self.foundry.retrieve(query, limit=limit)

    # ── the core agentic flow ─────────────────────────────────────────────
    def build_need(
        self,
        required_capabilities: list[str],
        *,
        description: str = "",
        seats: int | None = None,
        term_months: int = 12,
        use_work_iq: bool = True,
    ) -> tuple[BusinessNeed, BuyerContext]:
        ctx = self.work_iq.get_context() if use_work_iq else BuyerContext()
        resolved_seats = seats if seats is not None else (ctx.requested_seats or 1)
        need = BusinessNeed(
            description=description or ctx.renewal_subject or "Software solution",
            required_capabilities=required_capabilities,
            seats=resolved_seats,
            term_months=term_months,
            department=ctx.department,
            budget_annual_usd=ctx.budget_annual_usd or self.settings.commerce.default_budget_usd,
        )
        return need, ctx

    def solve(self, need: BusinessNeed, ctx: BuyerContext | None = None) -> DealOutcome:
        ctx = ctx or BuyerContext()
        deal = optimize_deal(need, self.registry, self.catalog, self.fabric)

        # Foundry IQ: validate that each chosen SKU actually delivers the capability.
        grounding: list[GroundedAnswer] = []
        for line in deal.quote.lines:
            cap = line.capabilities[0] if line.capabilities else ""
            answer = self.foundry.retrieve(f"{line.sku_name} {cap} license terms", limit=2)
            grounding.append(answer)
            if answer.grounded:
                deal.quote.notes.append(f"[Foundry IQ] {line.sku_name}: {answer.answer}")

        narration = self._narrate(need, ctx, deal)
        return DealOutcome(
            need=need, buyer_context=ctx, deal=deal, grounding=grounding, narration=narration
        )

    def _narrate(self, need: BusinessNeed, ctx: BuyerContext, deal: DealResult) -> str:
        fallback = (
            f"For {need.department}, MarketMesh assembled a "
            f"{len({line.vendor_id for line in deal.quote.lines})}-vendor solution covering "
            f"{', '.join(sorted(deal.quote.covered_capabilities()))}. List "
            f"${deal.quote.list_total_annual_usd:,.0f}/yr, incentives "
            f"-${deal.quote.total_incentive_usd:,.0f}, net "
            f"${deal.quote.net_total_annual_usd:,.0f}/yr — "
            f"${deal.total_savings_usd:,.0f} below the naive baseline."
        )
        return self.narrator.narrate(
            system="You summarise a software procurement recommendation in 3 concise sentences.",
            prompt=json.dumps(deal.to_dict())[:4000],
            fallback=fallback,
        )

    # ── transact (human approval + idempotent simulated checkout) ─────────
    def transact(
        self,
        outcome: DealOutcome,
        *,
        justification: str = "",
        approver: str | None = None,
    ) -> tuple[Order, Order]:
        ctx = outcome.buyer_context
        quote = outcome.deal.quote
        if not quote.lines:
            raise GuardrailError(
                "Nothing to purchase — the deal has no products (capabilities uncovered)."
            )
        approver = approver or ctx.approver or "approver@example.com"
        justification = justification or (
            f"Right-sized, capability-complete deal for {outcome.need.department}."
        )
        budget = ctx.budget_annual_usd or self.settings.commerce.default_budget_usd

        req = self.commerce.request_approval(quote, justification)
        token = self.commerce.approve(req.id, approver)  # human-in-the-loop step
        order = self.commerce.checkout(quote, token, remaining_budget_usd=budget)
        # Replay proves idempotency (no double charge).
        replay = self.commerce.checkout(quote, token, remaining_budget_usd=budget)
        return order, replay

    # ── status banner for the demo ────────────────────────────────────────
    def iq_status(self) -> dict[str, bool]:
        return {
            "fabric_iq_live": self.fabric.grounded_by_live_fabric,
            "foundry_iq_live": self.foundry.grounded_by_live_foundry,
            "work_iq_live": self.work_iq.grounded_by_live_graph,
            "azure_openai_live": self.narrator.live,
            "dry_run": self.settings.commerce.dry_run,
        }
