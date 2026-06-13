# Submission — 💼 Enterprise Agents track

Use these fields on the Innovation Studio project page.

**Title** (≤140)
> MarketMesh for Microsoft 365 Copilot — Multi-Vendor Software Buying

**Tagline** (≤300)
> A Microsoft 365 Copilot declarative agent that helps teams buy software across vendors:
> grounded in Work IQ, it assembles cost-optimised, incentive-aware deals and routes them
> for human approval before a simulated, idempotent checkout.

**Keywords**
> M365 Copilot, declarative agent, Work IQ, Fabric IQ, Foundry IQ, procurement, OAuth2,
> Entra ID, API plugin, agentic-commerce, enterprise

**Challenge**
> Enterprise Agents (Microsoft 365 Copilot)

**Writing code?** Yes · **Code repository:** https://github.com/tdsnxtaskin-tugay/marketmesh-commerce-agent

**Open for others to join?** Optional · **Skills wanted:** M365 Agents Toolkit, Azure, Python

**Description**

MarketMesh ships as a **Microsoft 365 Copilot declarative agent** (`appPackage/`:
`manifest.json`, `declarativeAgent.json`, `ai-plugin.json`, `openapi.yaml`,
`instructions.md`). Inside Copilot Chat a buyer can say *"we need a secure creative +
productivity stack for 200 people"* and the agent:

- grounds the request in **Work IQ** (the user's permitted M365 signals — renewals, seat
  demand, budget owner, approval policy);
- searches and configures products across every registered vendor;
- assembles the cheapest cross-vendor deal and applies marketing / co-sell incentives
  (Fabric IQ ontology + Foundry IQ grounded validation);
- routes to a **human approver** and runs an **idempotent, DRY_RUN checkout**.

The API actions are exposed via OpenAPI and secured with **OAuth 2.0 / Microsoft Entra ID**
(placeholders for `TEAMS_APP_ID` and the OAuth configuration id; secrets via Key Vault).
Enterprise-grade safety: spend cap, budget enforcement, secret scanning, mandatory human
approval, idempotency. All data is synthetic; real brands are labelled illustrative; no
company/PII/secrets.
