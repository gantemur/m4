import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_web_bundle_and_locales_are_deterministic_and_complete():
    completed = subprocess.run(["python3", "scripts/build_web_data.py"], cwd=ROOT, env={**__import__("os").environ, "PYTHONPATH": "src"}, check=True, capture_output=True, text=True)
    assert "Built web bundle" in completed.stdout
    subprocess.run(["python3", "scripts/validate_public_alpha.py"], cwd=ROOT, check=True)
    bundle = json.loads((ROOT / "web/data/public-alpha-v1.json").read_text())
    assert bundle["data_version"] == "m4-quarterly-v4" and bundle["quarters"]
    mn, en = json.loads((ROOT / "web/locales/mn.json").read_text()), json.loads((ROOT / "web/locales/en.json").read_text())
    mn_extra, en_extra = json.loads((ROOT / "web/locales/mn-phase6a.json").read_text()), json.loads((ROOT / "web/locales/en-phase6a.json").read_text())
    mn_discoverability, en_discoverability = json.loads((ROOT / "web/locales/mn-phase6b.json").read_text()), json.loads((ROOT / "web/locales/en-phase6b.json").read_text())
    def keys(d, prefix=""):
        return {f"{prefix}.{k}" if prefix else k for k,v in d.items() for _ in [0]} | {x for k,v in d.items() if isinstance(v,dict) for x in keys(v, f"{prefix}.{k}" if prefix else k)}
    assert keys(mn) == keys(en)
    assert keys(mn_extra) == keys(en_extra)
    assert keys(mn_discoverability) == keys(en_discoverability)

def test_browser_parity_and_static_assets():
    if shutil.which("node") is None:
        return
    subprocess.run(["node", "web/tests/parity.mjs"], cwd=ROOT, check=True)
    subprocess.run(["node", "--check", "web/js/app.js"], cwd=ROOT, check=True)
    index = (ROOT / "web/index.html").read_text()
    selector_css = (ROOT / "web/css/discoverability.css").read_text()
    app = (ROOT / "web/js/app.js").read_text()
    assert "../docs/" not in index
    assert 'id="copyLink"' in index and 'data-i18n="lab.copyLink"' in index
    assert ".language button{color:#155c58}" in selector_css
    assert "aria-pressed=true]{color:#153d3c}" in selector_css
    assert 'async function copyScenarioLink(){render();const href=window.location.href' in app
    assert (ROOT / "web/methodology.html").is_file()

def test_reviewed_mrpam_record_is_complete_and_eligible_for_synthetic_qa():
    review = json.loads((ROOT / "data/metadata/mrpam-price-review-v0.json").read_text())
    row = review["records"][0]
    assert row["review_status"] == "REVIEWED"
    assert row["applicable_royalty_month"] == "2026-08"
    assert row["price_observation_month"] == "2026-07"
    assert row["price_usd_per_tonne"] == 77.33
    assert len(row["source_checksum_sha256"]) == 64
