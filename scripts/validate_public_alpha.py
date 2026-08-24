"""Fail closed before publishing the static M4 alpha."""
from __future__ import annotations
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main() -> None:
    review = json.loads((ROOT / "data/metadata/mrpam-price-review-v0.json").read_text())
    seen = set()
    for row in review["records"]:
        key = (row.get("applicable_royalty_month"), row.get("mrpam_product_id"))
        if key in seen: raise SystemExit(f"Duplicate MRPAM public key: {key}")
        seen.add(key)
        required = ("review_status", "units", "source_url", "source_checksum_sha256", "retrieval_date", "price_usd_per_tonne")
        if any(not row.get(field) for field in required): raise SystemExit(f"Incomplete MRPAM provenance: {row.get('record_id')}")
        if row["review_status"] != "REVIEWED": raise SystemExit(f"Unreviewed record in reviewed ledger: {row.get('record_id')}")
        if row["units"] != "USD/tonne": raise SystemExit(f"Unexpected MRPAM units: {row['units']}")
    rule = json.loads((ROOT / "data/metadata/project-fiscal-rules/ett-coal-royalty-v0.json").read_text())
    if not review.get("legal_checked_at") or not review.get("legal_check_sources"): raise SystemExit("Missing legal-currentness check")
    if not any(r["rule_version"] == "general_export_reference_2019" and r["effective_to"] is None for r in rule["legal_regimes"]): raise SystemExit("Missing current general royalty regime")
    public = ROOT / "web"
    forbidden = ("/Users/", "gantumur", "data/raw/", "BEGIN PRIVATE", "api_key", "secret")
    for path in public.rglob("*"):
        if not path.is_file(): continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if any(token.lower() in text.lower() for token in forbidden): raise SystemExit(f"Unsafe public content: {path}")
    print("Public-alpha review, legal, and publication-safety checks passed.")

if __name__ == "__main__": main()
