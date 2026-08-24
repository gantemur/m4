import json
from pathlib import Path

import pytest

from m4.data.nso import NsoError, parse_jsonstat2


def test_parse_jsonstat2_returns_ordered_tidy_records():
    fixture = Path(__file__).parent / "fixtures" / "nso_jsonstat2.json"
    records = parse_jsonstat2(json.loads(fixture.read_text()))
    assert len(records) == 4
    assert records[0]["sector"] == "GDP"
    assert records[1]["time"] == "2025-II"
    assert records[3]["value"] == 30


def test_parse_rejects_malformed_dense_values():
    with pytest.raises(NsoError, match="Expected 2 observations"):
        parse_jsonstat2(
            {"id": ["x"], "size": [2], "dimension": {"x": {"category": {"index": {"a": 0, "b": 1}, "label": {}}}}, "value": [1]}
        )
