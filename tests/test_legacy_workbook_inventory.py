import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from inspect_legacy_workbook import inventory


def test_inventory_reports_formula_and_external_style_reference(tmp_path: Path):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Control panel"
    sheet["A1"] = 2
    sheet["A2"] = "=A1*0.5"
    sheet.sheet_state = "visible"
    path = tmp_path / "fixture.xlsx"
    workbook.save(path)

    result = inventory(path)

    assert result["sheet_count"] == 1
    assert result["sheet_inventory"][0]["counts"]["formula"] == 1
    assert result["sheet_inventory"][0]["counts"]["formula_with_numeric_literal"] == 1
    assert result["sha256"]
