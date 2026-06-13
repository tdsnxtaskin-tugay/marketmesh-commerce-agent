"""Dynamic, vendor-agnostic registry.

Any company — a well-known public brand or a brand-new one invented at runtime — can
be registered through :meth:`VendorRegistry.register_vendor`. The registry validates
the vendor-agnostic schema, enforces the illustrative-data disclaimer for real public
brands, and indexes products + incentives for fast lookup.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .models import Incentive, Sku, Vendor

ILLUSTRATIVE_DISCLAIMER = (
    "Illustrative demo data only — not official pricing, specifications, or an endorsement."
)


class RegistrationError(ValueError):
    """Raised when a vendor payload fails validation."""


class VendorRegistry:
    def __init__(self) -> None:
        self._vendors: dict[str, Vendor] = {}

    # ── registration ────────────────────────────────────────────────────────
    def register_vendor(self, vendor: Vendor | dict[str, Any]) -> Vendor:
        """Register (or replace) a vendor. Returns the stored Vendor.

        Accepts either a :class:`Vendor` or a raw dict (e.g. parsed JSON), so a new
        company can be onboarded live from an agent tool call.
        """
        if isinstance(vendor, dict):
            try:
                vendor = Vendor.from_dict(vendor)
            except (KeyError, ValueError) as exc:
                raise RegistrationError(f"Invalid vendor payload: {exc}") from exc

        self._validate(vendor)

        # Real public brands MUST carry the illustrative-data disclaimer (trademark safety).
        if vendor.is_real_brand and not vendor.disclaimer:
            vendor.disclaimer = ILLUSTRATIVE_DISCLAIMER

        self._vendors[vendor.id] = vendor
        return vendor

    def register_many(self, vendors: list[Vendor | dict[str, Any]]) -> list[Vendor]:
        return [self.register_vendor(v) for v in vendors]

    def load_dir(self, directory: str | Path) -> int:
        """Load every ``*.json`` vendor file under ``directory``. Returns count loaded."""
        directory = Path(directory)
        count = 0
        for path in sorted(directory.glob("*.json")):
            with open(path, encoding="utf-8") as fh:
                self.register_vendor(json.load(fh))
            count += 1
        return count

    def _validate(self, vendor: Vendor) -> None:
        if not vendor.id or not vendor.id.strip():
            raise RegistrationError("Vendor 'id' is required.")
        if not vendor.name or not vendor.name.strip():
            raise RegistrationError("Vendor 'name' is required.")
        seen: set[str] = set()
        for sku in vendor.products:
            if not sku.id:
                raise RegistrationError(f"Vendor '{vendor.id}' has a product without an id.")
            if sku.id in seen:
                raise RegistrationError(f"Duplicate SKU id '{sku.id}' in vendor '{vendor.id}'.")
            seen.add(sku.id)
            if sku.vendor_id != vendor.id:
                # Normalise so a SKU always points back at its owning vendor.
                sku.vendor_id = vendor.id
        for inc in vendor.incentives:
            if inc.vendor_id != vendor.id:
                inc.vendor_id = vendor.id

    # ── lookup ──────────────────────────────────────────────────────────────
    @property
    def vendors(self) -> list[Vendor]:
        return list(self._vendors.values())

    def vendor(self, vendor_id: str) -> Vendor | None:
        return self._vendors.get(vendor_id)

    def all_products(self) -> list[Sku]:
        out: list[Sku] = []
        for v in self._vendors.values():
            out.extend(v.products)
        return out

    def product(self, sku_id: str) -> Sku | None:
        for v in self._vendors.values():
            for sku in v.products:
                if sku.id == sku_id:
                    return sku
        return None

    def all_incentives(self) -> list[Incentive]:
        out: list[Incentive] = []
        for v in self._vendors.values():
            out.extend(v.incentives)
        return out

    def vendor_name(self, vendor_id: str) -> str:
        v = self._vendors.get(vendor_id)
        return v.name if v else vendor_id

    def __len__(self) -> int:
        return len(self._vendors)
