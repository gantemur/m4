"""Small, explicit client for NSO's PxWeb API v1."""

from __future__ import annotations

import json
from datetime import date
from itertools import product
from pathlib import Path
from typing import Any, Iterable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class NsoError(RuntimeError):
    """Raised when an NSO request or response cannot be used safely."""


class NsoClient:
    """Query a PxWeb table while preserving the exact raw API response."""

    def __init__(self, base_url: str = "https://data.1212.mn/api/v1/en/NSO", timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def table_url(self, table_path: str) -> str:
        return f"{self.base_url}/{table_path.lstrip('/')}"

    def metadata(self, table_path: str) -> dict[str, Any]:
        return self._request(self.table_url(table_path), method="GET")

    @staticmethod
    def dimension(metadata: dict[str, Any], dimension_code: str) -> dict[str, Any]:
        """Return a dimension definition, failing if the schema changed."""
        for variable in metadata.get("variables", []):
            if variable.get("code") == dimension_code:
                return variable
        raise NsoError(f"Unknown metadata dimension: {dimension_code}")

    @classmethod
    def codes_for_labels(
        cls, metadata: dict[str, Any], dimension_code: str, expected_labels: list[str]
    ) -> dict[str, str]:
        """Resolve exact semantic labels to source codes.

        Labels are normalized only for surrounding whitespace. Missing or
        duplicate labels fail loudly instead of silently falling back to code
        positions.
        """
        variable = cls.dimension(metadata, dimension_code)
        labels = {str(label).strip(): str(code) for code, label in zip(variable["values"], variable["valueTexts"])}
        missing = [label for label in expected_labels if label not in labels]
        if missing:
            raise NsoError(
                f"Expected labels changed for {dimension_code}: missing {missing}; "
                f"available={sorted(labels)}"
            )
        return {label: labels[label] for label in expected_labels}

    @classmethod
    def selection_by_labels(
        cls, metadata: dict[str, Any], dimension_code: str, expected_labels: list[str]
    ) -> list[str]:
        return list(cls.codes_for_labels(metadata, dimension_code, expected_labels).values())

    def observations(
        self,
        table_path: str,
        selections: dict[str, Iterable[str]],
        raw_directory: Path | str | None = None,
    ) -> list[dict[str, Any]]:
        """Return selected observations as tidy records; optionally preserve the raw response."""
        response = self.query_dataset(table_path, selections, raw_directory=raw_directory)
        return parse_jsonstat2(response)

    def query_dataset(
        self,
        table_path: str,
        selections: dict[str, Iterable[str]],
        raw_directory: Path | str | None = None,
    ) -> dict[str, Any]:
        """Return the raw JSON-stat2 dataset and optionally preserve it verbatim."""
        metadata = self.metadata(table_path)
        known_codes = {variable.get("code") for variable in metadata.get("variables", [])}
        unknown = set(selections) - known_codes
        if unknown:
            raise NsoError(f"Unknown table dimension(s): {sorted(unknown)}")
        payload = {
            "query": [
                {"code": code, "selection": {"filter": "item", "values": list(values)}}
                for code, values in selections.items()
            ],
            "response": {"format": "json-stat2"},
        }
        response = self._request(self.table_url(table_path), method="POST", payload=payload)
        if raw_directory is not None:
            destination = Path(raw_directory)
            destination.mkdir(parents=True, exist_ok=True)
            safe_name = table_path.replace("/", "_").replace(".px", "")
            (destination / f"{safe_name}_{date.today().isoformat()}.json").write_text(
                json.dumps(response, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        return response

    def _request(
        self, url: str, method: str, payload: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        try:
            with urlopen(request, timeout=self.timeout) as response:
                parsed = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise NsoError(f"NSO {method} request failed for {url}: {exc}") from exc
        if not isinstance(parsed, dict):
            raise NsoError("NSO response is not a JSON object")
        if "error" in parsed:
            raise NsoError(f"NSO API reported an error: {parsed['error']}")
        return parsed


def parse_jsonstat2(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a rectangular JSON-stat2 dataset into ordered tidy records."""
    dimensions = dataset.get("id")
    sizes = dataset.get("size")
    definition = dataset.get("dimension")
    values = dataset.get("value")
    if not isinstance(dimensions, list) or not isinstance(sizes, list) or not isinstance(definition, dict):
        raise NsoError("Response is missing JSON-stat2 dimensions")
    if len(dimensions) != len(sizes) or not all(isinstance(size, int) and size >= 0 for size in sizes):
        raise NsoError("Response has invalid JSON-stat2 dimension sizes")
    if not isinstance(values, list):
        raise NsoError("Response has no dense JSON-stat2 value array")
    expected = 1
    labels: list[list[tuple[str, str]]] = []
    for code, size in zip(dimensions, sizes):
        expected *= size
        category = definition.get(code, {}).get("category", {})
        index = category.get("index", {})
        label = category.get("label", {})
        if not isinstance(index, dict) or not isinstance(label, dict):
            raise NsoError(f"Dimension {code!r} has no category index/labels")
        ordered = sorted(index.items(), key=lambda item: item[1])
        if len(ordered) != size:
            raise NsoError(f"Dimension {code!r} size does not match its categories")
        labels.append([(key, str(label.get(key, key))) for key, _ in ordered])
    if len(values) != expected:
        raise NsoError(f"Expected {expected} observations, received {len(values)}")
    records: list[dict[str, Any]] = []
    for coordinates, value in zip(product(*labels), values):
        record = {f"{code}_id": key for code, (key, _) in zip(dimensions, coordinates)}
        record.update({code: label for code, (_, label) in zip(dimensions, coordinates)})
        record["value"] = value
        records.append(record)
    return records
