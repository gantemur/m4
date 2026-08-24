"""Pure, tested transformations used by the Phase 1A historical pipeline."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable, Mapping


def monthly_flow_to_quarterly(rows: Iterable[Mapping[str, object]], date_key: str, value_key: str) -> dict[str, float]:
    """Sum monthly flows by ``YYYY-Qn``; missing/non-numeric values are rejected."""
    result: defaultdict[str, float] = defaultdict(float)
    for row in rows:
        period = str(row[date_key])
        year, month = (int(part) for part in period.split("-"))
        value = row[value_key]
        if value is None:
            continue
        result[f"{year}-Q{(month - 1) // 3 + 1}"] += float(value)
    return dict(result)


def cumulative_monthly_to_flow(rows: Iterable[Mapping[str, object]], date_key: str, value_key: str) -> list[dict[str, object]]:
    """De-cumulate within calendar years, with January as the first observation."""
    ordered = sorted(rows, key=lambda row: str(row[date_key]))
    previous: dict[int, float] = {}
    result: list[dict[str, object]] = []
    for row in ordered:
        period = str(row[date_key])
        year, month = (int(part) for part in period.split("-"))
        cumulative = row[value_key]
        if cumulative is None:
            flow = None
        else:
            current = float(cumulative)
            flow = current if month == 1 or year not in previous else current - previous[year]
            previous[year] = current
        result.append({**row, value_key: flow})
    return result


def monthly_average_to_quarterly(rows: Iterable[Mapping[str, object]], date_key: str, value_key: str) -> dict[str, float]:
    """Average available monthly observations within each calendar quarter."""
    grouped: defaultdict[str, list[float]] = defaultdict(list)
    for row in rows:
        period = str(row[date_key])
        year, month = (int(part) for part in period.split("-"))
        value = row[value_key]
        if value is not None:
            grouped[f"{year}-Q{(month - 1) // 3 + 1}"].append(float(value))
    return {quarter: sum(values) / len(values) for quarter, values in grouped.items()}


def monthly_stock_to_quarter_end(rows: Iterable[Mapping[str, object]], date_key: str, value_key: str) -> dict[str, float]:
    """Take the last available monthly observation in each quarter."""
    ordered = sorted(rows, key=lambda row: str(row[date_key]))
    result: dict[str, float] = {}
    for row in ordered:
        period = str(row[date_key])
        year, month = (int(part) for part in period.split("-"))
        if row[value_key] is not None:
            result[f"{year}-Q{(month - 1) // 3 + 1}"] = float(row[value_key])
    return result


def implied_unit_value(value: float | None, quantity: float | None, quantity_scale: float = 1.0) -> float | None:
    """Compute a value/quantity unit value only when both definitions are present."""
    if value is None or quantity is None or float(quantity) == 0:
        return None
    return float(value) / (float(quantity) * quantity_scale)


def calculate_residual(total: float | None, components: Iterable[float | None]) -> float | None:
    """Calculate a residual only when total and every component are present."""
    if total is None:
        return None
    values = list(components)
    if any(value is None for value in values):
        return None
    return float(total) - sum(float(value) for value in values)


def quarter_sort_key(quarter: str) -> tuple[int, int]:
    year, q = quarter.split("-Q")
    return int(year), int(q)
