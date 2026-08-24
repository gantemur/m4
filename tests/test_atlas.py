import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
from build_atlas import annual_full_sum, annual_sum, yoy


def test_annual_full_sum_excludes_partial_vintage_year():
    rows = [
        {"quarter": "2020-Q1", "x": "1"},
        {"quarter": "2020-Q2", "x": "2"},
        {"quarter": "2020-Q3", "x": "3"},
        {"quarter": "2020-Q4", "x": "4"},
        {"quarter": "2021-Q1", "x": "5"},
    ]
    assert annual_sum(rows, "x") == {"2020": 10.0, "2021": 5.0}
    assert annual_full_sum(rows, "x") == {"2020": 10.0}


def test_yoy_is_within_vintage_and_not_a_level_link():
    assert abs(yoy({"2020": 100.0, "2021": 110.0})["2021"] - 10.0) < 1e-9
