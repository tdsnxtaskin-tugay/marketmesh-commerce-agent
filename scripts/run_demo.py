#!/usr/bin/env python3
"""MarketMesh demo CLI.

Run the full agentic, multi-vendor commerce flow offline (no credentials needed):

    python scripts/run_demo.py                 # narrated single-agent demo
    python scripts/run_demo.py --mode crew     # multi-agent crew transcript
    python scripts/run_demo.py status          # show Microsoft IQ wiring + DRY_RUN
    python scripts/run_demo.py vendors          # list registered vendors
    python scripts/run_demo.py search "vpn security"
    python scripts/run_demo.py ground "does the productivity suite include SSO?"
    python scripts/run_demo.py register path/to/vendor.json

Everything is synthetic and runs in DRY_RUN — no real payment is ever captured.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from marketmesh.agents import run_crew  # noqa: E402
from marketmesh.pipeline import MarketMesh  # noqa: E402

# Capabilities the headline scenario requires (a secure creative + productivity stack).
SCENARIO_CAPS = [
    "design", "pdf", "esign", "office_productivity", "email", "collaboration",
    "identity", "meetings", "network_security", "vpn", "analytics",
]
SCENARIO_GOAL = "Stand up a secure creative + productivity stack for the design team"

# A brand-new vendor registered live to prove dynamic onboarding.
LIVE_VENDOR = {
    "id": "lumino",
    "name": "Lumino",
    "is_real_brand": False,
    "disclaimer": "Fictional vendor registered live during the demo.",
    "products": [
        {
            "id": "lumino-sign",
            "vendor_id": "lumino",
            "name": "Lumino Sign (fictional)",
            "family": "Documents",
            "category_code": "43232104",
            "pricing_model": "per_seat",
            "unit_price_monthly": 4.0,
            "capabilities": ["esign"],
            "keywords": ["esign", "signature", "contract", "sign"],
        }
    ],
    "knowledge": [
        {
            "source": "Lumino — Sign overview (fictional)",
            "snippet": "Lumino Sign (fictional) is a standalone e-signature service priced per user.",
        }
    ],
}

BAR = "─" * 78


def _banner(mm: MarketMesh) -> None:
    s = mm.iq_status()
    print(BAR)
    print("MarketMesh — Agentic Multi-Vendor Software Commerce")
    print(BAR)
    mode = lambda live: "LIVE" if live else "offline-sample"  # noqa: E731
    print(f"  Fabric IQ  (product ontology) : {mode(s['fabric_iq_live'])}")
    print(f"  Foundry IQ (grounded retrieval): {mode(s['foundry_iq_live'])}")
    print(f"  Work IQ    (M365 buyer signals): {mode(s['work_iq_live'])}")
    print(f"  Azure OpenAI (narration)       : {mode(s['azure_openai_live'])}")
    print(f"  Checkout mode                  : {'DRY_RUN (simulated)' if s['dry_run'] else 'LIVE'}")
    print(BAR)


def _print_vendors(mm: MarketMesh) -> None:
    for v in mm.registry.vendors:
        tag = "real brand" if v.is_real_brand else "fictional"
        print(f"  • {v.name} ({tag}) — {len(v.products)} product(s)")
        if v.disclaimer:
            print(f"      {v.disclaimer}")


def _print_quote(outcome) -> None:
    q = outcome.deal.quote
    print("\nRecommended cross-vendor deal:")
    print(f"  {'Vendor':<11}{'Product':<36}{'Seats':>6}  {'Annual (USD)':>14}")
    for line in q.lines:
        print(
            f"  {line.vendor_name:<11}{line.sku_name:<36}{line.seats:>6}  "
            f"{line.list_annual_usd:>14,.0f}"
        )
    print(f"  {'':<53}{'─' * 14}")
    print(f"  {'List total':<53}{q.list_total_annual_usd:>14,.0f}")
    for inc in q.incentives:
        label = f"  {inc.type} ({inc.vendor_id})"
        print(f"  {label:<53}{-inc.savings_usd:>14,.0f}")
    print(f"  {'Net total / year':<53}{q.net_total_annual_usd:>14,.0f}")
    print(
        f"\n  Naive baseline ${outcome.deal.naive_baseline_usd:,.0f}/yr → "
        f"total savings ${outcome.deal.total_savings_usd:,.0f}/yr."
    )
    if outcome.deal.uncovered_capabilities:
        print("  Uncovered:", ", ".join(outcome.deal.uncovered_capabilities))


def _print_grounding(outcome) -> None:
    grounded = [g for g in outcome.grounding if g.grounded]
    if not grounded:
        return
    print("\nFoundry IQ grounded validation (cited):")
    for g in grounded[:4]:
        cite = g.citations[0].source if g.citations else "—"
        print(f"  • {g.answer}  [{cite}]")


def cmd_demo(mm: MarketMesh, args: argparse.Namespace) -> int:
    _banner(mm)
    print("\nRegistered vendors:")
    _print_vendors(mm)

    if not args.no_live_vendor:
        print("\n▶ Registering a brand-new vendor live (dynamic onboarding)…")
        v = mm.register_vendor(LIVE_VENDOR)
        print(f"  Registered '{v.name}' with {len(v.products)} product — now searchable:")
        for hit in mm.search("esign signature")[:3]:
            print(f"      {hit.sku.name} ({mm.catalog.vendor_name(hit.sku.vendor_id)})")

    if args.mode == "crew":
        print("\n▶ Running the multi-agent crew…\n")
        mission = run_crew(mm, SCENARIO_GOAL, SCENARIO_CAPS, seats=args.seats)
        print(mission.transcript())
        if args.json:
            print("\n" + json.dumps(
                {"transcript": [m.__dict__ for m in mission.log],
                 "order": mission.order.to_dict() if mission.order else None}, indent=2))
        return 0

    print("\n▶ Solving the cross-vendor deal (single-agent pipeline)…")
    need, ctx = mm.build_need(SCENARIO_CAPS, description=SCENARIO_GOAL, seats=args.seats)
    print(f"  Work IQ grounded: {ctx.department}, {need.seats} seats, "
          f"budget ${need.budget_annual_usd:,.0f}/yr, approver {ctx.approver}.")
    outcome = mm.solve(need, ctx)
    _print_quote(outcome)
    _print_grounding(outcome)

    print("\n▶ Reasoning steps:")
    for i, step in enumerate(outcome.deal.reasoning_steps, 1):
        print(f"  {i}. {step}")

    print("\n▶ Human approval + idempotent simulated checkout…")
    order, replay = mm.transact(outcome)
    print(f"  {order.status} order {order.id} — ${order.annual_usd:,.0f}/yr, "
          f"approved by {order.approver}.")
    print(f"  Replay of checkout → {'SAME order (no double charge)' if order.id == replay.id else 'DIFFERENT (BUG)'}.")

    print("\n▶ Recommendation:")
    print("  " + outcome.narration)
    if args.json:
        print("\n" + json.dumps(outcome.to_dict(), indent=2))
    return 0


def cmd_status(mm: MarketMesh, args: argparse.Namespace) -> int:
    _banner(mm)
    print(f"Vendors registered: {len(mm.registry)} | Products: {len(mm.registry.all_products())}")
    print(f"Capabilities in ontology: {len(mm.catalog.capabilities())}")
    return 0


def cmd_vendors(mm: MarketMesh, args: argparse.Namespace) -> int:
    _print_vendors(mm)
    return 0


def cmd_search(mm: MarketMesh, args: argparse.Namespace) -> int:
    hits = mm.search(args.query, vendor_id=args.vendor, capability=args.capability)
    if not hits:
        print("No matches.")
        return 0
    for h in hits:
        print(f"  [{h.score:>4}] {h.sku.name} ({mm.catalog.vendor_name(h.sku.vendor_id)}) "
              f"— caps: {', '.join(h.sku.capabilities)}")
    return 0


def cmd_ground(mm: MarketMesh, args: argparse.Namespace) -> int:
    ans = mm.ground(args.query)
    print(f"Answer ({'grounded' if ans.grounded else 'no evidence'}): {ans.answer}")
    for c in ans.citations:
        print(f"  [cite] {c.source}: {c.snippet}")
    return 0


def cmd_register(mm: MarketMesh, args: argparse.Namespace) -> int:
    with open(args.file, encoding="utf-8") as fh:
        payload = json.load(fh)
    v = mm.register_vendor(payload)
    print(f"Registered '{v.name}' with {len(v.products)} product(s). Disclaimer: {v.disclaimer}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="MarketMesh demo CLI")
    sub = parser.add_subparsers(dest="command")

    p_demo = sub.add_parser("demo", help="run the full narrated demo (default)")
    p_demo.add_argument("--mode", choices=["single", "crew"], default="single")
    p_demo.add_argument("--seats", type=int, default=None)
    p_demo.add_argument("--no-live-vendor", action="store_true")
    p_demo.add_argument("--json", action="store_true")

    sub.add_parser("status", help="show Microsoft IQ wiring + DRY_RUN")
    sub.add_parser("vendors", help="list registered vendors")

    p_search = sub.add_parser("search", help="cross-vendor product search")
    p_search.add_argument("query")
    p_search.add_argument("--vendor", default=None)
    p_search.add_argument("--capability", default=None)

    p_ground = sub.add_parser("ground", help="Foundry IQ grounded answer")
    p_ground.add_argument("query")

    p_reg = sub.add_parser("register", help="register a vendor from a JSON file")
    p_reg.add_argument("file")

    # Allow top-level flags so `run_demo.py --mode crew` works without the subcommand.
    parser.add_argument("--mode", choices=["single", "crew"], default="single")
    parser.add_argument("--seats", type=int, default=None)
    parser.add_argument("--no-live-vendor", action="store_true")
    parser.add_argument("--json", action="store_true")

    args = parser.parse_args(argv)
    mm = MarketMesh()

    handlers = {
        None: cmd_demo,
        "demo": cmd_demo,
        "status": cmd_status,
        "vendors": cmd_vendors,
        "search": cmd_search,
        "ground": cmd_ground,
        "register": cmd_register,
    }
    return handlers[args.command](mm, args)


if __name__ == "__main__":
    raise SystemExit(main())
