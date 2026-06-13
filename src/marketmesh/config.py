"""Environment-driven configuration. No hard-coded vendor, tenant, or company data.

Every setting reads from the process environment (optionally hydrated from a local
`.env` via python-dotenv when present). When integrations are unconfigured the agent
degrades gracefully to deterministic offline behaviour — see the `*_configured`
helpers used throughout the codebase.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # optional: load .env if python-dotenv is installed
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


def _get(key: str, default: str = "") -> str:
    return os.environ.get(key, default).strip()


def _get_bool(key: str, default: bool) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _get_float(key: str, default: float) -> float:
    try:
        return float(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class AzureOpenAIConfig:
    api_key: str = field(default_factory=lambda: _get("AZURE_OPENAI_API_KEY"))
    endpoint: str = field(default_factory=lambda: _get("AZURE_OPENAI_ENDPOINT"))
    api_version: str = field(
        default_factory=lambda: _get("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")
    )
    deployment: str = field(
        default_factory=lambda: _get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4o-mini")
    )

    @property
    def configured(self) -> bool:
        return bool(self.api_key and self.endpoint and self.deployment)


@dataclass(frozen=True)
class FabricIQConfig:
    endpoint: str = field(default_factory=lambda: _get("FABRIC_IQ_ENDPOINT"))
    workspace: str = field(default_factory=lambda: _get("FABRIC_IQ_WORKSPACE"))
    ontology: str = field(
        default_factory=lambda: _get("FABRIC_IQ_ONTOLOGY", "software-commerce")
    )
    api_key: str = field(default_factory=lambda: _get("FABRIC_IQ_API_KEY"))

    @property
    def configured(self) -> bool:
        return bool(self.endpoint and self.workspace)


@dataclass(frozen=True)
class FoundryIQConfig:
    project_endpoint: str = field(default_factory=lambda: _get("FOUNDRY_IQ_PROJECT_ENDPOINT"))
    knowledge_source: str = field(default_factory=lambda: _get("FOUNDRY_IQ_KNOWLEDGE_SOURCE"))
    api_key: str = field(default_factory=lambda: _get("FOUNDRY_IQ_API_KEY"))

    @property
    def configured(self) -> bool:
        return bool(self.project_endpoint and self.knowledge_source)


@dataclass(frozen=True)
class WorkIQConfig:
    tenant_id: str = field(default_factory=lambda: _get("WORK_IQ_TENANT_ID"))
    client_id: str = field(default_factory=lambda: _get("WORK_IQ_CLIENT_ID"))
    client_secret: str = field(default_factory=lambda: _get("WORK_IQ_CLIENT_SECRET"))
    user_id: str = field(default_factory=lambda: _get("WORK_IQ_USER_ID"))

    @property
    def configured(self) -> bool:
        return bool(self.tenant_id and self.client_id and self.client_secret)


@dataclass(frozen=True)
class CommerceConfig:
    dry_run: bool = field(default_factory=lambda: _get_bool("DRY_RUN", True))
    max_transaction_usd: float = field(
        default_factory=lambda: _get_float("MAX_TRANSACTION_USD", 500_000.0)
    )
    default_currency: str = field(default_factory=lambda: _get("DEFAULT_CURRENCY", "USD"))
    default_budget_usd: float = field(
        default_factory=lambda: _get_float("DEFAULT_BUDGET_USD", 500_000.0)
    )


@dataclass(frozen=True)
class Settings:
    azure_openai: AzureOpenAIConfig = field(default_factory=AzureOpenAIConfig)
    fabric_iq: FabricIQConfig = field(default_factory=FabricIQConfig)
    foundry_iq: FoundryIQConfig = field(default_factory=FoundryIQConfig)
    work_iq: WorkIQConfig = field(default_factory=WorkIQConfig)
    commerce: CommerceConfig = field(default_factory=CommerceConfig)


def load_settings() -> Settings:
    """Build a fresh Settings snapshot from the current environment."""
    return Settings()
