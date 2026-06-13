# 📨 Agents League @ AISF 2026 — Consolidated Submission Guide

One place with everything needed to submit on **Innovation Studio** (Projects tab). All
fields below are copy-paste ready. Everything here is **public-safe** — no company,
customer, tenant, PII, or confidential information; all vendor/pricing data is synthetic
and clearly labelled illustrative; checkout runs in `DRY_RUN`.

- **Hackathon:** Microsoft Agents League @ AI Skills Fest 2026 (submission deadline **June 14, 2026**)
- **Author:** Tugay Taskin · GitHub: https://github.com/tdsnxtaskin-tugay
- **Primary project (this repo):** MarketMesh — https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent

---

## 0) Participant profile (Innovation Studio)

- **Name:** Taskin, Tugay
- **Skills:** Python, AI Agents, Azure, Microsoft 365 Copilot, Knowledge Graphs, Prompt Engineering, API Design, Software Architecture
- **Interests:** AI, Agentic Commerce, Developer Experience, Enterprise Software, Automation
- **Professional links:** LinkedIn — `linkedin.com/in/<your_username>` · GitHub — `github.com/tdsnxtaskin-tugay`

---

## 1) MarketMesh — primary submission (all three tracks)

> One project, engineered to compete in every track. Submit it under the track you want it
> judged in (Reasoning recommended), or enter it in all three with the variants below.

**Microsoft IQ integration (required): ALL THREE**
- **Fabric IQ** — semantic product ontology / knowledge graph across vendors (the reasoning brain).
- **Foundry IQ** — grounded retrieval over product knowledge (cited answers).
- **Work IQ** — permission-enforced Microsoft 365 buyer signals (intent, renewals, budget, approver).

Each layer has a live path and a deterministic offline fallback (the demo runs with **zero
credentials**).

**Repository:** https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent
**Writing code?** Yes · **Open to others?** Optional

### 1a) 🧠 Reasoning Agents track (recommended)

- **Title:** `MarketMesh — Agentic Multi-Vendor Software Commerce`
- **Tagline:** `An AI agent that registers any software vendor, then reasons across all of them to assemble the cheapest capability-complete deal — incentive-aware, grounded by Microsoft Fabric IQ, Foundry IQ and Work IQ, and human-approved before a simulated checkout.`
- **Keywords:** `agentic-commerce, multi-vendor, software-procurement, Fabric IQ, Foundry IQ, Work IQ, knowledge-graph, CPQ, optimization, reasoning, multi-agent, human-in-the-loop`
- **Challenge:** Reasoning Agents (Microsoft Foundry)
- **Description:**

> MarketMesh turns a business need into the best **cross-vendor** software deal. It is
> vendor-agnostic: onboard a brand-new company at runtime and its products instantly become
> searchable, configurable, and part of the optimisation.
>
> The reasoning pipeline is explicit and auditable: **Work IQ** captures genuine intent from
> Microsoft 365 signals (renewals, seat demand, budget owner, approval policy); **Fabric IQ**
> models the multi-vendor universe as a product ontology / knowledge graph and decomposes the
> need into capabilities with candidate SKUs across every vendor; a **greedy cost-minimising
> set-cover** picks the products that together cover all capabilities while minimising
> redundancy, then layers **marketing / co-sell / volume incentives** — including cross-vendor
> co-sell advantages — and shows savings vs a naive baseline; **Foundry IQ** validates each
> choice against cited product knowledge; a **human approves**, then an **idempotent, DRY_RUN
> checkout** completes (replay proves no double charge).
>
> Also runnable as a **5-agent crew** (Sourcing → Solution Architect → Pricing → Compliance →
> Closer) with a bounded replan loop. All data is synthetic; real brands are clearly labelled
> illustrative; no company/PII/secrets. Runs fully offline with zero credentials.

### 1b) 💼 Enterprise Agents track

- **Title:** `MarketMesh for Microsoft 365 Copilot — Multi-Vendor Software Buying`
- **Tagline:** `A Microsoft 365 Copilot declarative agent that helps teams buy software across vendors: grounded in Work IQ, it assembles cost-optimised, incentive-aware deals and routes them for human approval before a simulated, idempotent checkout.`
- **Keywords:** `M365 Copilot, declarative agent, Work IQ, Fabric IQ, Foundry IQ, procurement, OAuth2, Entra ID, API plugin, agentic-commerce, enterprise`
- **Challenge:** Enterprise Agents (Microsoft 365 Copilot)
- **Description:**

> MarketMesh ships as a **Microsoft 365 Copilot declarative agent** (`appPackage/`). Inside
> Copilot Chat a buyer asks *"we need a secure creative + productivity stack for 200 people"*
> and the agent grounds the request in **Work IQ** (the user's permitted M365 signals),
> searches and configures products across every registered vendor, assembles the cheapest
> cross-vendor deal with marketing / co-sell incentives (Fabric IQ ontology + Foundry IQ
> grounded validation), routes to a **human approver**, and runs an **idempotent, DRY_RUN
> checkout**. The API actions are exposed via OpenAPI and secured with **OAuth 2.0 / Microsoft
> Entra ID** (placeholders for `TEAMS_APP_ID` and the OAuth configuration id; secrets via Key
> Vault). Enterprise-grade safety: spend cap, budget enforcement, secret scanning, mandatory
> human approval, idempotency. Synthetic data only; no company/PII/secrets.

### 1c) 🎨 Creative Apps track

- **Title:** `MarketMesh — Register Any Vendor, Let AI Build the Deal`
- **Tagline:** `A playful, powerful agentic-commerce app built with GitHub Copilot: onboard a brand-new software vendor live and watch the agent instantly re-optimise a cross-vendor deal — grounded by Microsoft Fabric IQ, Foundry IQ and Work IQ.`
- **Keywords:** `GitHub Copilot, agentic-commerce, multi-vendor, live demo, Fabric IQ, Foundry IQ, Work IQ, optimization, developer-experience, Python`
- **Challenge:** Creative Apps (GitHub Copilot)
- **Description:**

> MarketMesh reimagines software buying as an **agent you can play with**. The signature
> moment: **register a brand-new vendor mid-demo** and the agent immediately makes its products
> searchable, configurable, and part of the optimisation — recomputing a cheaper,
> capability-complete cross-vendor deal in real time. Under the hood it combines a product
> **knowledge graph** (Fabric IQ), **grounded retrieval** (Foundry IQ), and **Microsoft 365
> buyer signals** (Work IQ) with a cost-minimising optimiser, a CPQ pricing engine, and
> cross-vendor co-sell incentives. Built with **GitHub Copilot CLI**; runs fully offline in one
> command. Synthetic data only; real brands labelled illustrative; no company/PII/secrets.

---

## 2) How MarketMesh maps to the judging rubric

| Criterion (weight) | How it is addressed |
|---|---|
| **Accuracy & Relevance (20%)** | Solves a real multi-vendor buying problem; grounded (Foundry IQ) recommendations; deterministic, tested numbers (38 tests). |
| **Reasoning & Multi-step (20%)** | Explicit logged pipeline + optional 5-agent crew with a bounded replan loop. |
| **Reliability & Safety (20%)** | DRY_RUN, mandatory human-approval token bound to the quote, spend cap, budget enforcement, idempotent checkout, secret scanning, graceful degradation. |
| **Creativity & Originality (15%)** | Vendor-agnostic marketplace brain; register-a-vendor-live moment; cross-vendor co-sell incentives; all three IQ layers. |
| **UX & Presentation (15%)** | One-command narrated, numbers-first demo; also a Microsoft 365 Copilot agent. |
| **Community vote (10%)** | Public repo, clear README + diagram, zero-credential run, relatable B2B story. |

See [`docs/JUDGING.md`](docs/JUDGING.md) for detail.

---

## 3) Compliance sign-off (all projects)

- [x] Public repository with complete `README.md` + architecture diagram
- [x] Integrates ≥ 1 Microsoft IQ (MarketMesh integrates all three)
- [x] Original work, MIT licensed
- [x] **No secrets / keys / tokens** committed (`.env` git-ignored; only `.env.example`)
- [x] **No PII / customer / tenant / company-confidential** data; no internal URLs or library deps
- [x] Real brand names appear **only** as clearly-labelled *illustrative demo data — not official pricing or endorsement*; fictional vendors are explicitly marked
- [x] `DRY_RUN` checkout — no real payment possible
- [ ] Demo video ≤ 5 min on YouTube/Vimeo — *record before submitting* (storyboard in [`docs/DEMO_SCRIPT.md`](docs/DEMO_SCRIPT.md))
- [ ] Register + submit on Innovation Studio — *your action*

Full per-project checklist: [`submissions/COMPLIANCE_CHECKLIST.md`](submissions/COMPLIANCE_CHECKLIST.md).

---

## 4) Run / demo (zero credentials)

```bash
pip install -r requirements.txt
python scripts/run_demo.py            # narrated single-agent demo
python scripts/run_demo.py --mode crew
ruff check . && pytest                 # 38 tests, lint clean
```

To go live, copy `.env.example` → `.env` and fill in any of Azure OpenAI / Fabric IQ /
Foundry IQ / Work IQ (each activates independently).

---

## 5) Portfolio — other Agents League entries by the same author

All public, CI-green, and built clean-room with **no company/confidential data**. Each can be
submitted as its own project.

| Project | Track | Microsoft IQ | Repository |
|---|---|---|---|
| **MarketMesh** (this repo) | Reasoning / Enterprise / Creative | Fabric IQ + Foundry IQ + Work IQ | https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent |
| **AI Tester Agent** | Creative Apps (+ Reasoning via crew) | Foundry IQ | https://github.com/tdsnxtaskin-tugay/ai-tester-agent |
| **AI PR Review Agent** | Creative Apps | Foundry IQ | https://github.com/tdsnxtaskin-tugay/ai-pr-review-agent |
| **Delivery Pulse Copilot** | Enterprise Agents | Work IQ | https://github.com/tdsnxtaskin-tugay/delivery-pulse-copilot |

> **AI Tester Agent** — drives a real browser through plain-English test steps, records video,
> and posts results + attachments to Azure DevOps; multi-agent collaborate mode (Planner →
> Tester → Analyst → Reporter), grounded by Foundry IQ.
>
> **AI PR Review Agent** — reviews GitHub PRs against the linked issue's **business acceptance
> criteria** (scope-gap + scope-creep + alignment score + security/perf), grounded by Foundry
> IQ — going beyond code-only review.
>
> **Delivery Pulse Copilot** — a Microsoft 365 Copilot declarative agent that turns delivery
> signals into status, blockers, owner context, and escalation drafts, grounded by Work IQ via
> Microsoft Graph.
