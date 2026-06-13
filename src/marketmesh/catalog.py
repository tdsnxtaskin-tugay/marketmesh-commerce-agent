"""Catalog facade — a friendly read API over the vendor registry.

Wraps :class:`VendorRegistry` to provide search, capability indexing, and the
"which SKUs can satisfy capability X" lookups the deal optimizer needs.
"""

from __future__ import annotations

from .models import Sku
from .search import SearchHit, search_products
from .vendor_registry import VendorRegistry


class Catalog:
    def __init__(self, registry: VendorRegistry) -> None:
        self.registry = registry

    # ── search ────────────────────────────────────────────────────────────
    def search(
        self,
        query: str,
        *,
        vendor_id: str | None = None,
        capability: str | None = None,
        limit: int = 10,
    ) -> list[SearchHit]:
        return search_products(
            self.registry.all_products(),
            query,
            vendor_id=vendor_id,
            capability=capability,
            limit=limit,
        )

    # ── capability index ──────────────────────────────────────────────────
    def capabilities(self) -> set[str]:
        out: set[str] = set()
        for sku in self.registry.all_products():
            out.update(sku.capabilities)
        return out

    def skus_for_capability(self, capability: str) -> list[Sku]:
        """All SKUs (across every vendor) that provide ``capability``.

        Considers capabilities delivered both by the base SKU and by any add-on,
        so the optimizer can attach an add-on to cover a gap.
        """
        out: list[Sku] = []
        for sku in self.registry.all_products():
            if capability in sku.capabilities or any(
                capability in a.capabilities for a in sku.add_ons
            ):
                out.append(sku)
        return out

    def sku(self, sku_id: str) -> Sku | None:
        return self.registry.product(sku_id)

    def vendor_name(self, vendor_id: str) -> str:
        return self.registry.vendor_name(vendor_id)
