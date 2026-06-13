"""Work IQ — Microsoft 365 buyer signals.

Work IQ surfaces permission-enforced M365 memory (mail, meetings, chats, documents).
MarketMesh grounds a deal in the buyer's real work context: which software is up for
renewal, who is genuinely asking for more seats, what the budget/approval policy is,
and who must approve.

Live path: Microsoft Graph (client-credentials or delegated) over ``/messages``,
``/calendarView`` etc. Offline path: ``samples/work_iq_signals.json``.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path

from ..config import WorkIQConfig, load_settings

logger = logging.getLogger("marketmesh.work_iq")


@dataclass
class WorkSignal:
    kind: str  # email | meeting | chat | document
    summary: str
    source: str = "work-iq"

    def to_dict(self) -> dict:
        return {"kind": self.kind, "summary": self.summary, "source": self.source}


@dataclass
class BuyerContext:
    """The grounded intent + policy extracted from M365 signals."""

    department: str = "General"
    requested_seats: int = 0
    renewal_subject: str = ""
    renewal_date: str = ""
    approval_threshold_usd: float = 0.0
    approver: str = ""
    budget_annual_usd: float = 0.0
    signals: list[WorkSignal] = field(default_factory=list)
    grounded: bool = False

    def to_dict(self) -> dict:
        return {
            "department": self.department,
            "requested_seats": self.requested_seats,
            "renewal_subject": self.renewal_subject,
            "renewal_date": self.renewal_date,
            "approval_threshold_usd": self.approval_threshold_usd,
            "approver": self.approver,
            "budget_annual_usd": self.budget_annual_usd,
            "grounded": self.grounded,
            "signals": [s.to_dict() for s in self.signals],
        }


class WorkIQProvider:
    def __init__(
        self,
        sample_path: str | Path | None = None,
        config: WorkIQConfig | None = None,
    ) -> None:
        self.sample_path = Path(sample_path) if sample_path else None
        self.config = config or load_settings().work_iq

    @property
    def grounded_by_live_graph(self) -> bool:
        return self.config.configured

    def get_context(self) -> BuyerContext:
        if self.config.configured:
            try:  # pragma: no cover - requires live creds
                return self._from_graph()
            except Exception as exc:
                logger.warning("Work IQ Graph fetch failed: %s. Using offline sample.", exc)
        return self._from_sample()

    def _from_graph(self) -> BuyerContext:  # pragma: no cover - requires live creds
        import requests

        token = self._acquire_token()
        headers = {"Authorization": f"Bearer {token}"}
        base = "https://graph.microsoft.com/v1.0"
        user = self.config.user_id or "me"
        signals: list[WorkSignal] = []
        mail = requests.get(
            f"{base}/users/{user}/messages?$top=5&$select=subject,bodyPreview",
            headers=headers,
            timeout=20,
        )
        if mail.ok:
            for m in mail.json().get("value", []):
                signals.append(WorkSignal("email", m.get("subject", "")))
        # A full implementation parses renewal/seat/policy entities from these signals.
        return BuyerContext(signals=signals, grounded=True)

    def _acquire_token(self) -> str:  # pragma: no cover - requires live creds
        import requests

        url = f"https://login.microsoftonline.com/{self.config.tenant_id}/oauth2/v2.0/token"
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "scope": "https://graph.microsoft.com/.default",
            "grant_type": "client_credentials",
        }
        resp = requests.post(url, data=data, timeout=20)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _from_sample(self) -> BuyerContext:
        if not self.sample_path or not self.sample_path.exists():
            logger.info("No Work IQ sample found; returning empty (ungrounded) context.")
            return BuyerContext()
        with open(self.sample_path, encoding="utf-8") as fh:
            d = json.load(fh)
        ctx = BuyerContext(
            department=d.get("department", "General"),
            requested_seats=int(d.get("requested_seats", 0)),
            renewal_subject=d.get("renewal_subject", ""),
            renewal_date=d.get("renewal_date", ""),
            approval_threshold_usd=float(d.get("approval_threshold_usd", 0.0)),
            approver=d.get("approver", ""),
            budget_annual_usd=float(d.get("budget_annual_usd", 0.0)),
            signals=[WorkSignal(**s) for s in d.get("signals", [])],
            grounded=True,
        )
        return ctx
