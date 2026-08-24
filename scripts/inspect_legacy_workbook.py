"""Create a deterministic, non-destructive inventory of an XLSX legacy model."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import zipfile
from xml.etree import ElementTree
from collections import Counter
from datetime import date
from pathlib import Path

import openpyxl


COEFFICIENT = re.compile(r"(?:^|[^A-Za-z])(?:0\.\d+|\d+\.\d+)(?:[^A-Za-z]|$)")
EXTERNAL_LINK = re.compile(r"\[[^\]]+\]")
SHEET_LINK = re.compile(r"(?:'[^']+'|[A-Za-z_][A-Za-z0-9_]*)!")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def classify_sheet(title: str) -> list[str]:
    lowered = title.lower()
    labels = {
        "control_or_scenario": ("control", "scenario", "shock"),
        "output": ("result", "output", "graph"),
        "historical_data": ("data", "history", "historical"),
        "parameters": ("param", "assumption", "calibr"),
        "mining_or_project": ("mine", "mineral", "oyu", "erdenet", "tavan", "gatsuurt"),
        "fiscal": ("fiscal", "budget", "tax", "debt"),
        "macro": ("macro", "econom", "nominal", "inflation", "exchange"),
    }
    return [name for name, words in labels.items() if any(word in lowered for word in words)]


def inventory(path: Path) -> dict:
    book = openpyxl.load_workbook(path, read_only=False, data_only=False, keep_links=True)
    sheets = []
    all_formulas: list[dict] = []
    direct_coefficient_formulas: list[dict] = []
    formula_totals: Counter[str] = Counter()
    for sheet in book.worksheets:
        counts: Counter[str] = Counter()
        samples: list[dict] = []
        for row in sheet.iter_rows():
            for cell in row:
                value = cell.value
                if isinstance(value, str) and value.startswith("="):
                    counts["formula"] += 1
                    formula_totals["formula"] += 1
                    if EXTERNAL_LINK.search(value):
                        counts["external_workbook_link"] += 1
                        formula_totals["external_workbook_link"] += 1
                    if SHEET_LINK.search(value):
                        counts["cross_sheet_link"] += 1
                        formula_totals["cross_sheet_link"] += 1
                    if COEFFICIENT.search(value):
                        counts["formula_with_numeric_literal"] += 1
                        formula_totals["formula_with_numeric_literal"] += 1
                        if len(direct_coefficient_formulas) < 200:
                            direct_coefficient_formulas.append(
                                {"sheet": sheet.title, "cell": cell.coordinate, "formula": value}
                            )
                    if len(samples) < 12:
                        samples.append({"cell": cell.coordinate, "formula": value})
                    if len(all_formulas) < 100:
                        all_formulas.append({"sheet": sheet.title, "cell": cell.coordinate, "formula": value})
                elif value is not None:
                    counts["nonempty_nonformula"] += 1
                    formula_totals["nonempty_nonformula"] += 1
                    if isinstance(value, (int, float)):
                        counts["numeric_constant"] += 1
                        formula_totals["numeric_constant"] += 1
        sheets.append(
            {
                "title": sheet.title,
                "state": sheet.sheet_state,
                "max_row": sheet.max_row,
                "max_column": sheet.max_column,
                "classified_as": classify_sheet(sheet.title),
                "counts": dict(counts),
                "formula_samples": samples,
            }
        )
    names = []
    for name, definition in book.defined_names.items():
        names.append({"name": name, "definition": str(definition.attr_text), "hidden": bool(definition.hidden)})
    with zipfile.ZipFile(path) as archive:
        external_parts = sorted(name for name in archive.namelist() if name.startswith("xl/externalLinks/"))
        relation_parts = [name for name in external_parts if name.endswith(".rels")]
        external_targets = []
        for relation in relation_parts:
            root = ElementTree.fromstring(archive.read(relation))
            external_targets.extend(
                item.attrib.get("Target") for item in root if item.attrib.get("Target") is not None
            )
    return {
        "inventory_format": "m4-legacy-workbook-inventory-v1",
        "generated_date": date.today().isoformat(),
        "source_file": path.name,
        "source_size_bytes": path.stat().st_size,
        "sha256": sha256(path),
        "sheet_count": len(sheets),
        "sheet_inventory": sheets,
        "defined_name_count": len(names),
        "defined_names": names,
        "workbook_formula_totals": dict(formula_totals),
        "formula_samples_global": all_formulas,
        "direct_coefficient_formula_samples": direct_coefficient_formulas,
        "external_link_parts": external_parts,
        "external_link_targets": sorted(set(external_targets)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.workbook)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {args.output} ({result['sheet_count']} sheets, {result['defined_name_count']} names).")


if __name__ == "__main__":
    main()
