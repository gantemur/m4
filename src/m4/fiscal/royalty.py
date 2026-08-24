"""Auditable ETT coal AMNAT evaluator; it has no automatic macro propagation."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any
from urllib.request import urlopen
from html.parser import HTMLParser

NOT_DETERMINED = "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"
ROOT = Path(__file__).resolve().parents[3]
RULES_PATH = ROOT / "data/metadata/project-fiscal-rules/ett-coal-royalty-v0.json"


@dataclass(frozen=True)
class ReferencePrice:
    price_usd_per_tonne: float | None
    price_month: str
    publication_date: str
    source_url: str
    source_id: str = "mrpam_export_prices"
    product_label: str | None = None
    timing_note: str = "notice price may be based on the preceding month's average"


@dataclass(frozen=True)
class MseCoalMapping:
    mse_product_label: str
    statutory_product_class: str | None
    status: str  # EXACT, RULE_BASED, AMBIGUOUS, UNMAPPED
    source_id: str = "mse_ett_1_3_coking_2025"
    rationale: str = ""


@dataclass(frozen=True)
class RoyaltyInput:
    transaction_month: str
    quantity_tonnes: float | None
    product_class: str | None
    reference_price: ReferencePrice | None
    mnt_per_usd: float | None
    sale_type: str = "exported"
    valuation_regime: str | None = None
    product_mapping_status: str = "EXACT"
    project_id: str = "erdenes_tavan_tolgoi"


@dataclass
class RoyaltyResult:
    status: str
    rule_version: str | None = None
    assessed_sales_value_usd: float | None = None
    assessed_sales_value_mnt: float | None = None
    base_royalty_mnt: float | None = None
    additional_royalty_mnt: float | None = None
    total_royalty_mnt: float | None = None
    total_royalty_million_mnt: float | None = None
    base_rate_percent: float | None = None
    additional_rate_percent: float | None = None
    total_rate_percent: float | None = None
    source_ids: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    trace: list[dict[str, Any]] = field(default_factory=list)
    reason: str | None = None

    def fiscal_receipts(self) -> dict[str, float]:
        """Only a determined result can become an institutional project receipt."""
        return {} if self.status != "DETERMINED" or self.total_royalty_million_mnt is None else {
            "mineral_royalty_amnat": self.total_royalty_million_mnt
        }

    def to_project_contribution(self, quarter: str):
        """Explicit integration adapter; callers decide whether to add it to a scenario."""
        from m4.model import ProjectContribution
        return ProjectContribution("erdenes_tavan_tolgoi", quarter, "coal", fiscal_receipts=self.fiscal_receipts())


def _rules() -> dict:
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _date(month: str) -> date:
    return date.fromisoformat(month if len(month) == 10 else f"{month}-01")


def _select_regime(month: str, requested: str | None) -> dict | None:
    when = _date(month)
    candidates = []
    for regime in _rules()["legal_regimes"]:
        start = _date(regime["effective_from"])
        end = _date(regime["effective_to"]) if regime["effective_to"] else None
        if start <= when and (end is None or when <= end): candidates.append(regime)
    if requested:
        return next((r for r in candidates if r["rule_version"] == requested), None)
    # The temporary regime is intentionally not selected automatically.
    return next((r for r in candidates if r["rule_version"] == "general_export_reference_2019"), None)


def _additional_rate(product_class: str, price: float) -> float:
    classes = _rules()["product_classes"]
    if product_class not in classes:
        raise ValueError(f"Unknown statutory coal product class: {product_class}")
    for upper, rate in classes[product_class]["additional_rate_schedule_percent"]:
        if upper is None or price <= float(upper): return float(rate)
    raise AssertionError("Schedule must have an open-ended final bracket")


def evaluate_royalty(input: RoyaltyInput) -> RoyaltyResult:
    """Evaluate one exported coal product/month using a supplied official reference price."""
    if input.sale_type != "exported":
        return RoyaltyResult(NOT_DETERMINED, reason="Exported-coal-only module; domestic valuation is not automated.")
    if input.product_mapping_status not in {"EXACT", "RULE_BASED"}:
        return RoyaltyResult(NOT_DETERMINED, reason="Product mapping is ambiguous or unmapped.")
    if input.product_class is None:
        return RoyaltyResult(NOT_DETERMINED, reason="Missing statutory processing class.")
    # Reject unknown classes explicitly even if another required input is missing.
    _additional_rate(input.product_class, 0.0)
    regime = _select_regime(input.transaction_month, input.valuation_regime)
    if regime is None:
        return RoyaltyResult(NOT_DETERMINED, reason="No sourced legal regime for transaction month.")
    if regime["implementation_status"] != "COMPUTABLE_GIVEN_ADDITIONAL_USER_INPUT":
        return RoyaltyResult(NOT_DETERMINED, rule_version=regime["rule_version"], source_ids=regime["source_ids"],
                             reason="Selected legal regime is not automated; required valuation semantics remain unresolved.")
    price = input.reference_price.price_usd_per_tonne if input.reference_price else None
    if input.quantity_tonnes is None or input.quantity_tonnes < 0 or price is None or price < 0 or input.mnt_per_usd is None or input.mnt_per_usd <= 0:
        return RoyaltyResult(NOT_DETERMINED, rule_version=regime["rule_version"], source_ids=regime["source_ids"],
                             reason="Quantity, reference price, and positive MNT/USD are required.")
    additional = _additional_rate(input.product_class, price)
    base = float(regime["base_rate_percent"])
    assessed_usd = input.quantity_tonnes * price
    assessed_mnt = assessed_usd * input.mnt_per_usd
    base_mnt, additional_mnt = assessed_mnt * base / 100, assessed_mnt * additional / 100
    sources = [*regime["source_ids"], input.reference_price.source_id]
    trace = [
        {"from": "ETT coal quantity", "to": "statutory sales-assessment value", "type": "institutional",
         "quantity_tonnes": input.quantity_tonnes, "reference_price_usd_per_tonne": price,
         "mnt_per_usd": input.mnt_per_usd, "source_ids": sources},
        {"from": "sales-assessment value", "to": "base royalty", "type": "institutional",
         "rate_percent": base, "source_ids": ["minerals_law_current_mn"]},
        {"from": "sales-assessment value", "to": "additional royalty", "type": "institutional",
         "rate_percent": additional, "product_class": input.product_class, "source_ids": ["minerals_law_current_mn"]},
        {"from": "base royalty + additional royalty", "to": "ETT AMNAT", "type": "institutional",
         "source_ids": sources},
    ]
    return RoyaltyResult("DETERMINED", regime["rule_version"], assessed_usd, assessed_mnt, base_mnt, additional_mnt,
                         base_mnt + additional_mnt, (base_mnt + additional_mnt) / 1_000_000, base, additional,
                         base + additional, sources, [input.reference_price.timing_note], trace)


def map_mse_ett_coal_product(label: str, *, volatile_daf: float | None = None, caking_index: float | None = None) -> MseCoalMapping:
    """Controlled mapping; similar wording alone is never sufficient."""
    normal = " ".join(label.lower().split())
    if normal == "1/3 coking coal" and volatile_daf is not None and 28 < volatile_daf <= 37 and caking_index is not None and caking_index > 65:
        return MseCoalMapping(label, "raw_coal", "RULE_BASED", rationale="MSE quality fields match MRPAM 1/3 coking coal row under raw-coal requirements.")
    if normal == "1/3 coking coal":
        return MseCoalMapping(label, None, "AMBIGUOUS", rationale="Required quality fields for the MRPAM classification are missing.")
    return MseCoalMapping(label, None, "UNMAPPED", rationale="No audited crosswalk entry.")


class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.rows=[]; self.row=[]; self.cell=[]; self.in_cell=False
    def handle_starttag(self, tag, attrs):
        if tag == "tr": self.row=[]
        if tag in {"td", "th"}: self.cell=[]; self.in_cell=True
    def handle_data(self, data):
        if self.in_cell: self.cell.append(data)
    def handle_endtag(self, tag):
        if tag in {"td", "th"}: self.row.append(" ".join("".join(self.cell).split())); self.in_cell=False
        if tag == "tr" and self.row: self.rows.append(self.row)


def download_mrpam_notice(url: str, raw_directory: Path) -> tuple[Path, str]:
    """Download a caller-selected official notice verbatim and return its SHA-256."""
    raw = urlopen(url, timeout=30).read()
    digest = hashlib.sha256(raw).hexdigest(); raw_directory.mkdir(parents=True, exist_ok=True)
    path = raw_directory / f"mrpam-notice-{digest[:16]}.html"; path.write_bytes(raw)
    path.with_suffix(".metadata.json").write_text(json.dumps({
        "institution": "Mineral Resources and Petroleum Authority of Mongolia", "source_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(), "sha256": digest,
        "raw_file": path.name, "native_frequency": "monthly", "units": "USD/tonne",
        "observation_status": "published reference-price notice",
    }, indent=2) + "\n", encoding="utf-8")
    return path, digest


def parse_mrpam_notice_html(html: str, product_label: str) -> list[list[str]]:
    """Return matching table rows for review; price extraction is never guessed."""
    parser = _TableParser(); parser.feed(html)
    needle = " ".join(product_label.lower().split())
    return [row for row in parser.rows if needle in " ".join(row).lower()]


def evaluate_ett_coal_royalty(input: RoyaltyInput, mapping: MseCoalMapping | None = None) -> RoyaltyResult:
    """ETT wrapper; mapping is optional only when a statutory class is directly supplied."""
    if mapping is not None:
        input = RoyaltyInput(**{**input.__dict__, "product_class": mapping.statutory_product_class,
                                "product_mapping_status": mapping.status})
    return evaluate_royalty(input)
