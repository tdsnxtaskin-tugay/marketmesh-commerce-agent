# Submission — 🧠 Reasoning Agents track (primary)

Use these fields on the Innovation Studio project page.

**Title** (≤140)
> MarketMesh — Agentic Multi-Vendor Software Commerce

**Tagline** (≤300)
> An AI agent that registers any software vendor, then reasons across all of them to
> assemble the cheapest capability-complete deal — incentive-aware, grounded by Microsoft
> Fabric IQ, Foundry IQ and Work IQ, and human-approved before a simulated checkout.

**Keywords**
> agentic-commerce, multi-vendor, software-procurement, Fabric IQ, Foundry IQ, Work IQ,
> knowledge-graph, CPQ, optimization, reasoning, multi-agent, human-in-the-loop

**Challenge**
> Reasoning Agents (Microsoft Foundry)

**Writing code?** Yes · **Code repository:** https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent

**Open for others to join?** Optional · **Skills wanted:** Python, knowledge graphs, Azure AI

**Description**

MarketMesh turns a business need into the best **cross-vendor** software deal. It is
vendor-agnostic: onboard a brand-new company at runtime and its products instantly become
searchable, configurable, and part of the optimisation.

The reasoning pipeline is explicit and auditable:
1. **Work IQ** captures genuine intent from Microsoft 365 signals (renewals, seat demand,
   budget owner, approval policy).
2. **Fabric IQ** models the multi-vendor universe as a product ontology / knowledge graph
   and decomposes the need into capabilities with candidate SKUs across every vendor.
3. A **weighted set-cover optimiser** picks the cheapest set of products that together
   cover all capabilities, removing overlap, then layers **marketing / co-sell / volume
   incentives** — including cross-vendor co-sell advantages — and shows the savings vs a
   naive baseline.
4. **Foundry IQ** validates each choice against cited product knowledge.
5. A **human approves**, then an **idempotent, DRY_RUN checkout** completes (replay proves
   no double charge).

Also runnable as a **5-agent crew** (Sourcing → Solution Architect → Pricing → Compliance
→ Closer) with a bounded replan loop. All data is synthetic; real brands are clearly
labelled illustrative; no company/PII/secrets. Runs fully offline with zero credentials.
