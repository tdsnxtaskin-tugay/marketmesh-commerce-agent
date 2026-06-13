# How MarketMesh maps to the judging rubric

The Agents League rubric and how this project targets each weighted criterion.

## Accuracy & Relevance — 20%
- Solves the stated problem precisely: a **multi-vendor** software-buying agent that
  registers any company and assembles the **cheapest capability-complete deal**.
- Grounded answers (Foundry IQ) prevent the agent from claiming a SKU has a capability it
  doesn't — recommendations are backed by cited evidence.
- Deterministic optimiser + tests guarantee the numbers are correct and reproducible.

## Reasoning & Multi-step Thinking — 20%
- Explicit, logged pipeline: intent → capability decomposition → candidate SKUs →
  weighted set-cover → CPQ pricing → incentives → grounded validation → approval →
  idempotent checkout. Each step is printed in the demo (`reasoning_steps`).
- Optional **5-agent crew** (Sourcing → Solution Architect → Pricing → Compliance →
  Closer) with a **bounded replan loop** makes the collaboration explicit.

## Reliability & Safety — 20%
- DRY_RUN, mandatory human approval token bound to the quote, spend cap, budget
  enforcement, idempotent checkout, secret scanning, illustrative-data labelling.
- Graceful degradation: missing IQ/LLM/deps never crash — the offline demo always runs.
- 31 unit tests cover pricing, set-cover, incentives, and every guardrail.

## Creativity & Originality — 15%
- A **vendor-agnostic marketplace/distributor brain** (not just a buyer-side tool):
  register a brand-new vendor mid-demo and the deal **instantly re-optimises**.
- **Cross-vendor co-sell / marketing incentives** — a genuinely novel optimisation signal.
- Uses **all three Microsoft IQ layers** together, each for what it's best at.

## User Experience & Presentation — 15%
- One command runs a clean, narrated, numbers-first transcript with a quote table,
  incentive breakdown, savings, and cited grounding — ideal for the demo video.
- Also shippable as a **Microsoft 365 Copilot** declarative agent (`appPackage/`).

## Community vote — 10%
- Public repo, clear README + architecture diagram, easy to run with zero credentials,
  relatable B2B problem with an eye-catching "register a vendor live" moment.

## Microsoft IQ requirement — mandatory
- **Fabric IQ** (product ontology/graph), **Foundry IQ** (grounded retrieval), and
  **Work IQ** (M365 buyer signals) are all integrated, each with a live path and an
  offline fallback.
