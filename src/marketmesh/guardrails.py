"""Guardrails — the reliability & safety layer.

  * Secret scanning of free-text (justifications never leak keys/tokens).
  * Per-transaction spend cap.
  * Budget enforcement.
  * Idempotency keys (replaying a checkout never double-charges).
  * Illustrative-data labelling for real public brands.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

# Common secret shapes — intentionally conservative.
_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),  # OpenAI-style keys
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),  # GitHub tokens
    re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS access key id
    re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),  # Slack tokens
    re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),  # PEM private key
]


class GuardrailError(Exception):
    """Raised when a hard safety rule is violated."""


def scan_for_secrets(text: str) -> list[str]:
    """Return a list of redacted findings; empty when clean."""
    findings: list[str] = []
    for pattern in _SECRET_PATTERNS:
        for match in pattern.findall(text or ""):
            token = match if isinstance(match, str) else match[0]
            findings.append(token[:4] + "…redacted")
    return findings


def assert_no_secrets(text: str) -> None:
    findings = scan_for_secrets(text)
    if findings:
        raise GuardrailError(
            f"Refusing to proceed: free text contains {len(findings)} possible secret(s)."
        )


def check_spend_cap(annual_usd: float, cap_usd: float) -> None:
    if annual_usd > cap_usd:
        raise GuardrailError(
            f"Annual total ${annual_usd:,.0f} exceeds per-transaction cap ${cap_usd:,.0f}."
        )


def check_budget(annual_usd: float, remaining_budget_usd: float) -> None:
    if annual_usd > remaining_budget_usd:
        raise GuardrailError(
            f"Annual total ${annual_usd:,.0f} exceeds remaining budget "
            f"${remaining_budget_usd:,.0f}."
        )


def idempotency_key(*parts: str) -> str:
    """Stable key for a deal so a retried checkout returns the same order."""
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return f"idem_{digest[:16]}"


@dataclass
class IdempotencyStore:
    """Maps idempotency keys → order ids (in-memory; swap for a datastore in prod)."""

    _seen: dict[str, str] = field(default_factory=dict)

    def get(self, key: str) -> str | None:
        return self._seen.get(key)

    def put(self, key: str, order_id: str) -> None:
        self._seen[key] = order_id
