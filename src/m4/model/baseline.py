"""Observed baseline and accounting identities for the frozen v0 engine."""
from __future__ import annotations
import csv
from dataclasses import dataclass
from pathlib import Path

COMMODITIES = ("coal", "copper_concentrate", "gold", "iron_ore")
UNITS = {
    "exports_usd_million": "USD million", "imports_usd_million": "USD million",
    "trade_balance_usd_million": "USD million", "government_revenue_mnt_million": "million MNT",
    "government_expenditure_mnt_million": "million MNT", "mnt_per_usd_quarterly_average": "MNT/USD",
    "gdp_nominal_total": "million MNT", "industry_gva_nominal_mnt_million": "million MNT",
    "other_industry_gva_nominal_mnt_million": "million MNT",
    "taxes_less_subsidies_nominal_mnt_million": "million MNT",
}


@dataclass
class Baseline:
    rows: dict[str, dict[str, float | None]]

    @classmethod
    def load(cls, path: Path | str) -> "Baseline":
        rows = {}
        with Path(path).open(encoding="utf-8", newline="") as source:
            for row in csv.DictReader(source):
                quarter = row["quarter"]
                rows[quarter] = {key: None if value in {"", "None"} else float(value)
                                 for key, value in row.items() if key not in {"quarter", "quarter.1"}}
        return cls(rows)

    def unit(self, column: str) -> str | None:
        if column in UNITS:
            return UNITS[column]
        if column.endswith("_export_value_usd_thousand"):
            return "USD thousand"
        if column.endswith("_production_thousand_t") or column.endswith("_export_quantity_thousand_t"):
            return "thousand tonnes"
        if column.endswith("_production_kg"):
            return "kg"
        if column.endswith("_export_quantity_t"):
            return "tonnes"
        if column.startswith("gdp_real2015_"):
            return "million MNT, 2015 prices"
        return None

    def commodity_export_usd_million(self, quarter: str, commodity: str) -> float | None:
        value = self.rows[quarter].get(f"{commodity}_export_value_usd_thousand")
        return None if value is None else value / 1000.0

    def mining_export_usd_million(self, quarter: str) -> float:
        return sum(self.commodity_export_usd_million(quarter, commodity) or 0.0 for commodity in COMMODITIES)

    def commodity_export_price_usd_per_native_quantity(self, quarter: str, commodity: str) -> float | None:
        """Implied price in USD per the stored native quantity unit (never imputed)."""
        row = self.rows[quarter]
        quantity = row.get(f"{commodity}_export_quantity_thousand_t")
        if quantity is None:
            quantity = row.get(f"{commodity}_export_quantity_t")
        value = row.get(f"{commodity}_export_value_usd_thousand")
        return None if quantity in (None, 0) or value is None else 1000.0 * value / quantity

    def commodity_export_value_from_price_quantity_usd_thousand(self, quarter: str, commodity: str) -> float | None:
        row = self.rows[quarter]
        quantity = row.get(f"{commodity}_export_quantity_thousand_t")
        if quantity is None:
            quantity = row.get(f"{commodity}_export_quantity_t")
        price = self.commodity_export_price_usd_per_native_quantity(quarter, commodity)
        return None if quantity is None or price is None else price * quantity / 1000.0

    def residual_merchandise_exports_usd_million(self, quarter: str) -> float | None:
        total = self.rows[quarter].get("exports_usd_million")
        return None if total is None else total - self.mining_export_usd_million(quarter)

    def replay_checks(self) -> dict[str, list[str]]:
        failures = {"gdp_identity_failures": [], "commodity_export_identity_failures": [],
                    "residual_export_identity_failures": [], "trade_balance_identity_failures": [],
                    "fiscal_balance_computable_failures": []}
        for quarter, row in self.rows.items():
            parts = [row.get("gdp_nominal_mining"), row.get("gdp_nominal_agriculture"),
                     row.get("gdp_nominal_construction"), row.get("other_industry_gva_nominal_mnt_million"),
                     row.get("taxes_less_subsidies_nominal_mnt_million")]
            total = row.get("gdp_nominal_total")
            if total is not None and all(value is not None for value in parts) and abs(total - sum(parts)) > .31:
                failures["gdp_identity_failures"].append(quarter)
            for commodity in COMMODITIES:
                value = row.get(f"{commodity}_export_value_usd_thousand")
                quantity = row.get(f"{commodity}_export_quantity_thousand_t")
                if quantity is None:
                    quantity = row.get(f"{commodity}_export_quantity_t")
                reconstructed = self.commodity_export_value_from_price_quantity_usd_thousand(quarter, commodity)
                if value is not None and reconstructed is not None and abs(value - reconstructed) > 1e-6:
                    failures["commodity_export_identity_failures"].append(f"{quarter}:{commodity}")
            exports = row.get("exports_usd_million")
            residual = self.residual_merchandise_exports_usd_million(quarter)
            if exports is not None and residual is not None and abs(exports - (self.mining_export_usd_million(quarter) + residual)) > 1e-9:
                failures["residual_export_identity_failures"].append(quarter)
            imports, trade = row.get("imports_usd_million"), row.get("trade_balance_usd_million")
            if None not in (exports, imports, trade) and abs((exports - imports) - trade) > .25:
                failures["trade_balance_identity_failures"].append(quarter)
            revenue, spending = row.get("government_revenue_mnt_million"), row.get("government_expenditure_mnt_million")
            if (revenue is None) != (spending is None):
                failures["fiscal_balance_computable_failures"].append(quarter)
        return failures
