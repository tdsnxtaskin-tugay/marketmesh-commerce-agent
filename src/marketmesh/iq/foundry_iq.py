"""Foundry IQ — grounded knowledge retrieval.

Foundry IQ provides agentic, permission-aware retrieval over enterprise knowledge with
grounded, cited answers. MarketMesh uses it to answer product-knowledge questions —
"does this SKU include SSO?", "what are the license terms?", "is it FedRAMP eligible?"
— with citations, instead of letting the model guess.

Live path: ``azure-ai-projects`` knowledge retrieval against a configured knowledge
source. Offline path: retrieve from the per-SKU ``knowledge`` notes shipped in the
sample vendors, returning the same grounded shape (answer + citations).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

from ..config import FoundryIQConfig, load_settings

logger = logging.getLogger("marketmesh.foundry_iq")

_TOKEN = re.compile(r"[a-z0-9]+")


@dataclass
class Citation:
    source: str
    snippet: str

    def to_dict(self) -> dict:
        return {"source": self.source, "snippet": self.snippet}


@dataclass
class GroundedAnswer:
    query: str
    answer: str
    citations: list[Citation] = field(default_factory=list)
    grounded: bool = False  # True when backed by retrieved evidence

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "answer": self.answer,
            "grounded": self.grounded,
            "citations": [c.to_dict() for c in self.citations],
        }


class FoundryIQRetriever:
    def __init__(
        self,
        knowledge: dict[str, list[str]] | None = None,
        config: FoundryIQConfig | None = None,
    ) -> None:
        # knowledge: source label -> list of fact snippets
        self.knowledge = knowledge or {}
        self.config = config or load_settings().foundry_iq
        self._client = None
        if self.config.configured:
            self._client = self._try_live_client()

    @property
    def grounded_by_live_foundry(self) -> bool:
        return self._client is not None

    def _try_live_client(self):  # pragma: no cover - requires live creds
        try:
            from azure.ai.projects import AIProjectClient
            from azure.identity import DefaultAzureCredential

            client = AIProjectClient(
                endpoint=self.config.project_endpoint,
                credential=DefaultAzureCredential(),
            )
            logger.info("Foundry IQ live retrieval enabled.")
            return client
        except Exception as exc:
            logger.warning("Foundry IQ configured but client init failed: %s. Using offline.", exc)
            return None

    def add_source(self, label: str, snippets: list[str]) -> None:
        self.knowledge.setdefault(label, []).extend(snippets)

    def retrieve(self, query: str, *, limit: int = 3) -> GroundedAnswer:
        if self._client is not None:  # pragma: no cover - requires live creds
            try:
                return self._retrieve_live(query, limit=limit)
            except Exception as exc:
                logger.warning("Foundry IQ live retrieval failed: %s. Falling back.", exc)
        return self._retrieve_offline(query, limit=limit)

    def _retrieve_live(self, query: str, *, limit: int) -> GroundedAnswer:  # pragma: no cover
        result = self._client.knowledge_retrieval.retrieve(
            knowledge_source=self.config.knowledge_source, query=query, top=limit
        )
        citations = [
            Citation(source=getattr(r, "source", "foundry-iq"), snippet=getattr(r, "content", ""))
            for r in getattr(result, "results", [])
        ]
        answer = citations[0].snippet if citations else "No grounded evidence found."
        return GroundedAnswer(query=query, answer=answer, citations=citations, grounded=bool(citations))

    def _retrieve_offline(self, query: str, *, limit: int) -> GroundedAnswer:
        q = set(_TOKEN.findall(query.lower()))
        scored: list[tuple[int, str, str]] = []
        for source, snippets in self.knowledge.items():
            for snip in snippets:
                overlap = len(q & set(_TOKEN.findall(snip.lower())))
                if overlap:
                    scored.append((overlap, source, snip))
        scored.sort(key=lambda t: t[0], reverse=True)
        top = scored[:limit]
        if not top:
            return GroundedAnswer(
                query=query,
                answer="No grounded evidence found in the indexed product knowledge.",
                citations=[],
                grounded=False,
            )
        citations = [Citation(source=s, snippet=snip) for _, s, snip in top]
        return GroundedAnswer(
            query=query, answer=top[0][2], citations=citations, grounded=True
        )
