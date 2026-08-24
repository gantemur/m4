"""Snapshot comparison and validation helpers."""

from __future__ import annotations

from collections import Counter
from typing import Iterable, Mapping


def detect_revisions(
    old_rows: Iterable[Mapping[str, object]],
    new_rows: Iterable[Mapping[str, object]],
    key_fields: tuple[str, ...] = ("period", "series_id"),
    value_field: str = "value",
) -> list[dict[str, object]]:
    """Return changed, added, and removed keyed observations without overwriting either version."""
    old = {tuple(str(row.get(key)) for key in key_fields): row.get(value_field) for row in old_rows}
    new = {tuple(str(row.get(key)) for key in key_fields): row.get(value_field) for row in new_rows}
    changes: list[dict[str, object]] = []
    for key in sorted(set(old) | set(new)):
        if key not in old:
            changes.append({"key": key, "change": "added", "old_value": None, "new_value": new[key]})
        elif key not in new:
            changes.append({"key": key, "change": "removed", "old_value": old[key], "new_value": None})
        elif old[key] != new[key]:
            changes.append({"key": key, "change": "revised", "old_value": old[key], "new_value": new[key]})
    return changes


def duplicate_keys(rows: Iterable[Mapping[str, object]], key_fields: tuple[str, ...]) -> list[tuple[str, ...]]:
    keys = [tuple(str(row.get(key)) for key in key_fields) for row in rows]
    return [key for key, count in Counter(keys).items() if count > 1]


def is_non_decreasing(values: Iterable[str]) -> bool:
    values = list(values)
    return values == sorted(values)
