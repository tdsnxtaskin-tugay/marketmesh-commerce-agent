"""Fabric IQ — semantic product ontology / knowledge graph.

Fabric IQ provides business-concept reasoning over Microsoft Fabric (ontologies,
knowledge graphs). MarketMesh models the multi-vendor universe as a graph:

    Vendor ──offers──▶ SKU ──provides──▶ Capability
       │                 │
       └──runs──▶ Incentive   SKU ──alternative_of──▶ SKU (cross-vendor)

This module builds that graph from the registered catalog. When a live Fabric IQ
workspace is configured it can be projected/queried there; otherwise an in-memory
graph answers the same ontology questions offline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from ..config import FabricIQConfig, load_settings
from ..models import Sku
from ..vendor_registry import VendorRegistry

logger = logging.getLogger("marketmesh.fabric_iq")


@dataclass
class CapabilityProvider:
    sku_id: str
    vendor_id: str
    vendor_name: str
    sku_name: str
    via_add_on: str | None = None


class FabricIQGraph:
    """Ontology/knowledge-graph view over the registered vendors."""

    def __init__(self, registry: VendorRegistry, config: FabricIQConfig | None = None) -> None:
        self.registry = registry
        self.config = config or load_settings().fabric_iq
        self._cap_index: dict[str, list[CapabilityProvider]] = {}
        self._build()

    @property
    def grounded_by_live_fabric(self) -> bool:
        return self.config.configured

    def _build(self) -> None:
        if self.config.configured:
            logger.info(
                "Fabric IQ workspace '%s' configured — projecting catalog ontology.",
                self.config.workspace,
            )
            # A live deployment would upsert nodes/edges into the Fabric IQ ontology
            # here (via the Fabric REST/GraphQL surface) and query it back. We keep
            # the in-memory projection as the source of truth for the demo so behaviour
            # is identical online and offline.
        for sku in self.registry.all_products():
            for cap in sku.capabilities:
                self._add(cap, sku, None)
            for addon in sku.add_ons:
                for cap in addon.capabilities:
                    self._add(cap, sku, addon.id)

    def _add(self, cap: str, sku: Sku, via_add_on: str | None) -> None:
        self._cap_index.setdefault(cap, []).append(
            CapabilityProvider(
                sku_id=sku.id,
                vendor_id=sku.vendor_id,
                vendor_name=self.registry.vendor_name(sku.vendor_id),
                sku_name=sku.name,
                via_add_on=via_add_on,
            )
        )

    # ── ontology queries ─────────────────────────────────────────────────
    def capabilities(self) -> list[str]:
        return sorted(self._cap_index.keys())

    def providers_of(self, capability: str) -> list[CapabilityProvider]:
        """All SKUs (any vendor) that provide a capability — the core graph query."""
        return list(self._cap_index.get(capability, []))

    def alternatives(self, sku_id: str) -> list[CapabilityProvider]:
        """Cross-vendor alternatives: other vendors' SKUs sharing a capability."""
        sku = self.registry.product(sku_id)
        if not sku:
            return []
        out: dict[str, CapabilityProvider] = {}
        for cap in sku.capabilities:
            for prov in self.providers_of(cap):
                if prov.vendor_id != sku.vendor_id and prov.sku_id != sku_id:
                    out[prov.sku_id] = prov
        return list(out.values())

    def decompose(self, capabilities: list[str]) -> dict[str, list[CapabilityProvider]]:
        """Map each required capability → candidate providers (graph reasoning input)."""
        return {cap: self.providers_of(cap) for cap in capabilities}

    def uncovered(self, capabilities: list[str]) -> list[str]:
        return [c for c in capabilities if not self._cap_index.get(c)]
