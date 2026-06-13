# Compliance checklist — Agents League @ AISF 2026

Project: **MarketMesh — Agentic Multi-Vendor Software Commerce**
Repo: https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent

## Submission requirements
- [x] Repository is **public** with a complete `README.md`
- [x] Architecture diagram showing Microsoft IQ integration (README + `ARCHITECTURE.md`)
- [x] Project description, features, problem solved, technologies (README + `submissions/`)
- [x] Integrates **≥ 1 Microsoft IQ** — integrates **all three**: Fabric IQ, Foundry IQ, Work IQ
- [x] Original work, MIT licensed
- [ ] Demo video ≤ 5 min on YouTube/Vimeo (storyboard in `docs/DEMO_SCRIPT.md`) — *record before submitting*
- [ ] Register on Innovation Studio and submit on the Projects tab — *user action*

## No-confidential-information sign-off
- [x] **No secrets / API keys / tokens / credentials** committed (`.env` git-ignored; only `.env.example`)
- [x] **No PII, customer, tenant, or company-confidential** information anywhere
- [x] **No internal URLs, org/project names, or internal library dependencies**
- [x] Real brand names appear **only** as clearly-labelled *illustrative demo data — not official pricing or endorsement*
- [x] Two vendors (NovaForge, Lumino) are explicitly fictional
- [x] Checkout runs in `DRY_RUN` — no real payment is possible
- [x] Clean-room build — copies nothing from any private/company repository

## Safety & reliability
- [x] Mandatory human approval (token bound to the exact quote)
- [x] Per-transaction spend cap + department budget enforcement
- [x] Idempotent checkout (no double charge)
- [x] Secret scanner on free-text justifications
- [x] Graceful degradation when any IQ / LLM / dependency is absent
- [x] 31 unit tests; `ruff` clean; CI configured

## Verification commands
```bash
pip install -r requirements.txt
python scripts/run_demo.py            # offline end-to-end demo
python scripts/run_demo.py --mode crew
ruff check . && pytest
```
