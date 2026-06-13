"""Shared, vendor-agnostic data model for the software-commerce domain.

These plain dataclasses are the contract that every layer (registry, catalog,
configurator, optimizer, commerce) speaks. They are JSON-serialisable so vendors
can be registered dynamically from files or at runtime.

Design notes (industry-standard mapping):
  * ``category_code`` follows a UNSPSC-style numeric taxonomy.
  * ``currency`` is an ISO 4217 code.
  * Pricing supports the common SaaS shapes: per-seat, flat, usage, tiered.
  * ``Incentive`` models co-sell / MDF (Market Development Funds) / volume rebates.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class PricingModel(StrEnum):
    PER_SEAT = "per_seat"
    FLAT = "flat"
    USAGE = "usage"
    TIERED = "tiered"


class IncentiveType(StrEnum):
    VOLUME_REBATE = "volume_rebate"
    MDF = "mdf"  # Market Development Funds (marketing co-fund)
    CO_SELL = "co_sell"  # cross-vendor / partner co-sell discount
    PROMO = "promo"
    BUNDLE = "bundle"  # multi-product attach discount


@dataclass
class Capability:
    """A business capability a product can satisfy (the ontology vocabulary)."""

    id: str
    name: str
    category: str = "general"

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "category": self.category}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Capability:
        return cls(id=d["id"], name=d.get("name", d["id"]), category=d.get("category", "general"))


@dataclass
class Tier:
    """A volume pricing tier: up to ``max_seats`` at ``unit_price_monthly``."""

    max_seats: int
    unit_price_monthly: float

    def to_dict(self) -> dict[str, Any]:
        return {"max_seats": self.max_seats, "unit_price_monthly": self.unit_price_monthly}

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Tier:
        return cls(max_seats=int(d["max_seats"]), unit_price_monthly=float(d["unit_price_monthly"]))


@dataclass
class AddOn:
    """An optional configurable extra on a SKU (per-seat monthly add)."""

    id: str
    name: str
    unit_price_monthly: float = 0.0
    capabilities: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "unit_price_monthly": self.unit_price_monthly,
            "capabilities": list(self.capabilities),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> AddOn:
        return cls(
            id=d["id"],
            name=d.get("name", d["id"]),
            unit_price_monthly=float(d.get("unit_price_monthly", 0.0)),
            capabilities=list(d.get("capabilities", [])),
        )


@dataclass
class Sku:
    """A purchasable, configurable product/plan offered by a vendor."""

    id: str
    vendor_id: str
    name: str
    family: str = ""
    category_code: str = "43230000"  # UNSPSC: Software (default)
    pricing_model: PricingModel = PricingModel.PER_SEAT
    unit_price_monthly: float = 0.0  # per-seat monthly (PER_SEAT)
    flat_price_annual: float = 0.0  # FLAT
    usage_unit: str = ""  # e.g. "1k API calls" (USAGE)
    usage_price: float = 0.0  # price per usage unit (USAGE)
    tiers: list[Tier] = field(default_factory=list)  # TIERED
    min_seats: int = 1
    max_seats: int = 100000
    term_months: int = 12
    capabilities: list[str] = field(default_factory=list)
    add_ons: list[AddOn] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "name": self.name,
            "family": self.family,
            "category_code": self.category_code,
            "pricing_model": self.pricing_model.value,
            "unit_price_monthly": self.unit_price_monthly,
            "flat_price_annual": self.flat_price_annual,
            "usage_unit": self.usage_unit,
            "usage_price": self.usage_price,
            "tiers": [t.to_dict() for t in self.tiers],
            "min_seats": self.min_seats,
            "max_seats": self.max_seats,
            "term_months": self.term_months,
            "capabilities": list(self.capabilities),
            "add_ons": [a.to_dict() for a in self.add_ons],
            "keywords": list(self.keywords),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Sku:
        return cls(
            id=d["id"],
            vendor_id=d["vendor_id"],
            name=d["name"],
            family=d.get("family", ""),
            category_code=str(d.get("category_code", "43230000")),
            pricing_model=PricingModel(d.get("pricing_model", "per_seat")),
            unit_price_monthly=float(d.get("unit_price_monthly", 0.0)),
            flat_price_annual=float(d.get("flat_price_annual", 0.0)),
            usage_unit=d.get("usage_unit", ""),
            usage_price=float(d.get("usage_price", 0.0)),
            tiers=[Tier.from_dict(t) for t in d.get("tiers", [])],
            min_seats=int(d.get("min_seats", 1)),
            max_seats=int(d.get("max_seats", 100000)),
            term_months=int(d.get("term_months", 12)),
            capabilities=list(d.get("capabilities", [])),
            add_ons=[AddOn.from_dict(a) for a in d.get("add_ons", [])],
            keywords=list(d.get("keywords", [])),
        )

    def add_on(self, add_on_id: str) -> AddOn | None:
        for a in self.add_ons:
            if a.id == add_on_id:
                return a
        return None


@dataclass
class Incentive:
    """A marketing / co-sell / volume incentive a vendor offers."""

    id: str
    vendor_id: str
    type: IncentiveType
    description: str = ""
    discount_pct: float = 0.0  # fraction, e.g. 0.10 == 10%
    min_annual_usd: float = 0.0  # threshold to unlock
    min_seats: int = 0
    applies_to_categories: list[str] = field(default_factory=list)  # category codes
    requires_vendor_ids: list[str] = field(default_factory=list)  # for co-sell/bundle

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "type": self.type.value,
            "description": self.description,
            "discount_pct": self.discount_pct,
            "min_annual_usd": self.min_annual_usd,
            "min_seats": self.min_seats,
            "applies_to_categories": list(self.applies_to_categories),
            "requires_vendor_ids": list(self.requires_vendor_ids),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Incentive:
        return cls(
            id=d["id"],
            vendor_id=d["vendor_id"],
            type=IncentiveType(d.get("type", "promo")),
            description=d.get("description", ""),
            discount_pct=float(d.get("discount_pct", 0.0)),
            min_annual_usd=float(d.get("min_annual_usd", 0.0)),
            min_seats=int(d.get("min_seats", 0)),
            applies_to_categories=list(d.get("applies_to_categories", [])),
            requires_vendor_ids=list(d.get("requires_vendor_ids", [])),
        )


@dataclass
class Vendor:
    """A registered software company. ``is_real_brand`` flags illustrative public brands."""

    id: str
    name: str
    is_real_brand: bool = False
    disclaimer: str = ""
    products: list[Sku] = field(default_factory=list)
    incentives: list[Incentive] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "is_real_brand": self.is_real_brand,
            "disclaimer": self.disclaimer,
            "products": [p.to_dict() for p in self.products],
            "incentives": [i.to_dict() for i in self.incentives],
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Vendor:
        return cls(
            id=d["id"],
            name=d["name"],
            is_real_brand=bool(d.get("is_real_brand", False)),
            disclaimer=d.get("disclaimer", ""),
            products=[Sku.from_dict(p) for p in d.get("products", [])],
            incentives=[Incentive.from_dict(i) for i in d.get("incentives", [])],
        )


@dataclass
class BusinessNeed:
    """The buyer's intent the agent must solve."""

    description: str
    required_capabilities: list[str] = field(default_factory=list)
    seats: int = 1
    term_months: int = 12
    department: str = "General"
    budget_annual_usd: float = 0.0


@dataclass
class ConfiguredItem:
    """A configured SKU ready to price: seats + term + chosen add-ons."""

    sku_id: str
    vendor_id: str
    seats: int
    term_months: int
    add_on_ids: list[str] = field(default_factory=list)


@dataclass
class QuoteLine:
    """A priced line on a quote."""

    sku_id: str
    sku_name: str
    vendor_id: str
    vendor_name: str
    seats: int
    term_months: int
    add_on_ids: list[str]
    list_annual_usd: float
    capabilities: list[str] = field(default_factory=list)
    category_code: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "sku_id": self.sku_id,
            "sku_name": self.sku_name,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "seats": self.seats,
            "term_months": self.term_months,
            "add_on_ids": list(self.add_on_ids),
            "list_annual_usd": round(self.list_annual_usd, 2),
            "capabilities": list(self.capabilities),
            "category_code": self.category_code,
        }


@dataclass
class AppliedIncentive:
    incentive_id: str
    vendor_id: str
    type: str
    description: str
    savings_usd: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "incentive_id": self.incentive_id,
            "vendor_id": self.vendor_id,
            "type": self.type,
            "description": self.description,
            "savings_usd": round(self.savings_usd, 2),
        }


@dataclass
class Quote:
    """A complete, priced multi-vendor deal."""

    currency: str = "USD"
    lines: list[QuoteLine] = field(default_factory=list)
    incentives: list[AppliedIncentive] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def list_total_annual_usd(self) -> float:
        return round(sum(line.list_annual_usd for line in self.lines), 2)

    @property
    def total_incentive_usd(self) -> float:
        return round(sum(i.savings_usd for i in self.incentives), 2)

    @property
    def net_total_annual_usd(self) -> float:
        return round(self.list_total_annual_usd - self.total_incentive_usd, 2)

    def covered_capabilities(self) -> set[str]:
        out: set[str] = set()
        for line in self.lines:
            out.update(line.capabilities)
        return out

    def to_dict(self) -> dict[str, Any]:
        return {
            "currency": self.currency,
            "lines": [line.to_dict() for line in self.lines],
            "incentives": [i.to_dict() for i in self.incentives],
            "list_total_annual_usd": self.list_total_annual_usd,
            "total_incentive_usd": self.total_incentive_usd,
            "net_total_annual_usd": self.net_total_annual_usd,
            "notes": list(self.notes),
        }
