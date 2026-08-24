"""Pure helpers for Bank of Mongolia date/step-series conventions."""
from __future__ import annotations

from datetime import date
from typing import Iterable, Mapping


def parse_bom_date(value: str) -> date:
    """Parse the BoM ISO date used by its JSON endpoints."""
    return date.fromisoformat(value[:10])


def step_policy_rate(changes: Iterable[Mapping[str, object]], periods: Iterable[str]) -> dict[str, float]:
    """Apply effective-date policy-rate changes without inventing pre-history."""
    ordered = sorted(((parse_bom_date(str(row["effective_date"])), float(row["rate"])) for row in changes), key=lambda item: item[0])
    result: dict[str, float] = {}
    for period in periods:
        point = parse_bom_date(period)
        applicable = [rate for effective, rate in ordered if effective <= point]
        if applicable:
            result[period] = applicable[-1]
    return result
