# Demo video script (≤ 5 minutes)

Goal: show MarketMesh solving a real multi-vendor buying problem end-to-end, with all
three Microsoft IQ layers, and one memorable "wow" moment.

Run everything with: `python scripts/run_demo.py` (and `--mode crew` for the crew view).

---

**0:00 — The problem (20s)**
> "Enterprises buy software from dozens of vendors. Capabilities overlap, pricing is a
> maze, and nobody finds the cheapest set of products that actually covers the need.
> MarketMesh is an agent that does."

**0:20 — Status & vendors (20s)**
- `python scripts/run_demo.py status`
- Point out: all three IQ layers wired (offline fallback for the demo), `DRY_RUN` on,
  real brands labelled **illustrative**, plus a fictional vendor.

**0:40 — The "wow": register a vendor live (40s)**
- Start the demo; when it reaches "Registering a brand-new vendor live", call out:
  > "I just onboarded a brand-new vendor, *Lumino*. No redeploy — it's instantly
  > searchable and part of the optimisation."
- Show the search result listing Lumino.

**1:20 — Work IQ grounds the intent (30s)**
> "From the buyer's Microsoft 365 signals (Work IQ): 200 seats, a renewal, a $50k approval
> policy, and an IT rule that SSO is mandatory."

**1:50 — Fabric IQ + the optimiser (60s)**
- Walk the quote table: a multi-vendor deal across Adobe, Cisco, Microsoft, NovaForge,
  Lumino — each line covering specific capabilities.
> "Fabric IQ's product graph decomposed the need into capabilities and found candidates
> across every vendor. A greedy cost-minimising set cover picked the covering set and
> avoided redundant SKUs."

**2:50 — Incentives & savings (40s)**
> "Then it layered marketing incentives — a volume rebate, MDF co-marketing credit, and a
> **cross-vendor co-sell** discount that only unlocks because two specific vendors are in
> the deal. Net result: hundreds of thousands below the naive baseline."

**3:30 — Foundry IQ grounding (20s)**
> "Every capability claim is validated against cited product knowledge (Foundry IQ) — the
> agent doesn't guess."

**3:50 — Safety: approval + idempotent checkout (40s)**
> "It routes to a human approver, the token is bound to this exact quote, spend cap and
> budget are enforced, and checkout is idempotent and simulated — replaying it returns the
> same order. No double charge, no real payment."

**4:30 — Crew view + close (30s)**
- Flash `--mode crew` transcript (Sourcing → Architect → Pricing → Compliance → Closer).
> "Same flow as a multi-agent crew. All three Microsoft IQ layers, fully auditable, public
> and synthetic. That's MarketMesh."

---

Tips: terminal at large font; pre-run once to warm up; keep under 5:00.
