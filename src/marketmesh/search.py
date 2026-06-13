"""Cross-vendor product search.

Deterministic, dependency-free relevance scoring over the registered catalog. Matches
a free-text query against SKU name, family, keywords and capability ids. When a live
Foundry IQ retriever is wired in, the pipeline can re-rank these results with grounded
evidence — but search always works offline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import Sku

_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN.findall(text.lower()))


def _sku_corpus(sku: Sku) -> set[str]:
    parts = [sku.name, sku.family, sku.vendor_id, sku.category_code]
    parts.extend(sku.keywords)
    parts.extend(sku.capabilities)
    return _tokens(" ".join(parts))


@dataclass
class SearchHit:
    sku: Sku
    score: float
    matched: list[str]


def search_products(
    products: list[Sku],
    query: str,
    *,
    vendor_id: str | None = None,
    capability: str | None = None,
    limit: int = 10,
) -> list[SearchHit]:
    """Return the best-matching SKUs for ``query``, highest score first."""
    q_tokens = _tokens(query)
    hits: list[SearchHit] = []
    for sku in products:
        if vendor_id and sku.vendor_id != vendor_id:
            continue
        if capability and capability not in sku.capabilities:
            continue
        corpus = _sku_corpus(sku)
        overlap = q_tokens & corpus
        if not overlap and query.strip():
            continue
        # Score: token overlap, with a small boost for direct capability matches.
        cap_boost = len(q_tokens & set(sku.capabilities)) * 0.5
        score = len(overlap) + cap_boost
        hits.append(SearchHit(sku=sku, score=round(score, 3), matched=sorted(overlap)))
    hits.sort(key=lambda h: (h.score, h.sku.id), reverse=True)
    return hits[:limit]
