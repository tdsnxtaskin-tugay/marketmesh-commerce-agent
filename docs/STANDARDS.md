# Industry standards covered

MarketMesh deliberately models real software-commerce and agentic-commerce standards so
the design is credible and extensible — not a toy.

## Commerce & procurement

| Standard / pattern | Where it shows up |
|---|---|
| **CPQ (Configure → Price → Quote)** | `configurator.py` validates a configuration against SKU constraints, then prices it; `Quote` is the output artifact. |
| **Pricing models** | Per-seat, flat, usage, and **tiered volume** pricing — the common SaaS shapes (`PricingModel`). |
| **ISO 4217 currency codes** | `Quote.currency` / `DEFAULT_CURRENCY` (USD by default). |
| **UNSPSC-style category taxonomy** | `Sku.category_code` uses UNSPSC-style numeric codes (e.g. `43232107`). |
| **SKU / part-number model** | Every product is a uniquely-identified SKU under a vendor. |
| **Co-sell / MDF (Market Development Funds)** | `Incentive` models volume rebates, MDF co-marketing credits, cross-vendor co-sell, promos, and bundle attach discounts. |

## Agentic commerce & payments

| Standard / pattern | Where it shows up |
|---|---|
| **Cart / quote → mandate → checkout** | The emerging *agentic commerce* shape (e.g. Agent Payments Protocol / Agentic Commerce Protocol): a structured quote, a **delegated human-approval token (mandate)**, then checkout. |
| **Human-in-the-loop approval** | `commerce.approve()` is a separate step the agent cannot perform itself; the token is bound to the exact quote fingerprint. |
| **Idempotency keys** | `checkout` is idempotent — replays return the same order, never double-charging. |
| **Spend controls** | Per-transaction cap + budget enforcement before any order. |

## Identity, security & hosting (production)

| Standard | Plan |
|---|---|
| **OAuth 2.0 / OpenID Connect, Microsoft Entra ID** | Fronts the M365 Copilot action / API (`ai-plugin.json` uses `OAuthPluginVault`). |
| **Least-privilege delegated Graph scopes** | Work IQ reads only what the signed-in user is permitted to see. |
| **Azure Key Vault** | All secrets; nothing committed; `.env` git-ignored. |
| **Model Context Protocol (MCP) / OpenAPI actions** | `appPackage/openapi.yaml` exposes the commerce actions for the declarative agent. |

## Knowledge & semantics (Microsoft IQ)

| Standard | Plan |
|---|---|
| **Knowledge graph / ontology (Fabric IQ)** | Vendor → SKU → Capability → Incentive graph; business-concept reasoning over it. |
| **Grounded retrieval with citations (Foundry IQ)** | Every capability claim is backed by retrieved, cited product knowledge. |
| **Permission-enforced M365 memory (Work IQ)** | Intent, renewals, budget owner and approval policy come from the user's permitted signals. |
