# M4 — Mongolia Mining-Macro Model

M4 is a small, transparent and eventually interactive model of Mongolia’s mining-centred economy. It will trace the important channels from mineral production and export revenue through fiscal policy, external balances, the exchange rate, construction and the wider non-mining economy. It is not a mining-only projection tool or a large CGE/DSGE model.

**Status: Public Alpha.** M4 is a transparent historical scenario engine, not an empirically estimated macro model or an unconditional forecasting system. Its browser-only alpha presents historical counterfactuals, keeps ETT AMNAT separate from national scenarios, and only exposes reviewed official reference-price rows.

**Live alpha:** [gantemur.github.io/m4](https://gantemur.github.io/m4/) · deployed 2026-08-24. The current limitations are deliberate: unsupported macro propagation is shown as not determined, and only independently reviewed MRPAM price rows are offered as official inputs.

## Layout

- `docs/`: scope, legacy audit, data dictionary and conceptual notes.
- `research/legacy/`: provenance pointers for third-party predecessor work; no unverified redistributions.
- `data/`: raw, intermediate, processed and metadata layers (raw responses are ignored by Git).
- `data/snapshots/`: compact immutable normalized source snapshots; `data/metadata/` contains source, series, project, and revision manifests.
- `src/m4/data/`: small reusable data clients.
- `scripts/`: explicit retrieval entry points.
- `tests/`: offline parser tests using a synthetic, representative JSON-stat2 fixture.
- `web/`: Mongolian-first static public alpha, browser engine, locales, generated compact bundle and parity test.

## Setup and checks

Use Python 3.9 or newer. From the repository root:

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
```

Ruff is optional if installed: `ruff check .`.

## Sample official retrieval

The following fetches NSO table metadata and a small quarterly GDP-by-industry extract, then saves the unmodified JSON API response under `data/raw/nso/` (which is intentionally not committed):

```bash
PYTHONPATH=src python3 scripts/retrieve_nso_gdp.py
```

It uses the NSO PxWeb table `DT_NSO_0500_004V1`. Network access is required. The client fails explicitly if NSO changes the response shape or a requested dimension is unknown.

## Phase 1A historical foundation

The live Phase 1A extractor queries the exact NSO tables documented in [`docs/data-dictionary-v1.md`](docs/data-dictionary-v1.md), writes a new timestamped snapshot directory on every run, and refuses to overwrite an existing snapshot:

```bash
PYTHONPATH=src python3 scripts/build_phase1a.py
PYTHONPATH=src python3 scripts/validate_phase1a.py
```

The corrected canonical panel is `data/processed/m4-quarterly-v1.csv`; the machine-readable provenance manifest is `data/metadata/series/m4-quarterly-v1.json`. `m4-quarterly-v0.csv` is retained but deprecated/invalid for analysis; see [`docs/historical-data-v1.md`](docs/historical-data-v1.md). Raw API responses remain local and ignored. Bank of Mongolia and international commodity benchmarks are explicitly deferred until stable official endpoints and definitions are confirmed.

Phase 1B atlas regeneration:

```bash
MPLCONFIGDIR=/tmp/m4-mpl MPLLOCALDIR=/tmp/m4-mpl PYTHONPATH=src python3 scripts/build_atlas.py
```

See [`docs/historical-atlas-v0.md`](docs/historical-atlas-v0.md), [`docs/missing-data-priorities-v0.md`](docs/missing-data-priorities-v0.md), and [`docs/structural-diagnostics-v0.md`](docs/structural-diagnostics-v0.md).

Phase 1C extended panel regeneration:

```bash
PYTHONPATH=src python3 scripts/build_phase1c.py
PYTHONPATH=src python3 scripts/validate_phase1c.py
```

This writes `data/processed/m4-quarterly-v2.csv` without overwriting v1. See [`docs/phase1c-data-dictionary-v0.md`](docs/phase1c-data-dictionary-v0.md) and [`docs/model-readiness-v0.md`](docs/model-readiness-v0.md).

## Reproducibility and provenance

Raw observations are never hand-edited. Each external series must have source, identifier, URL, retrieval date, units, frequency, observation convention and transformations documented. Missing data are not silently interpolated or substituted. See [`docs/data-dictionary-v2.md`](docs/data-dictionary-v2.md).

## Phase 6 public alpha

Build the small browser bundle and deterministic Python reference fixtures from the authoritative corrected panel:

```bash
PYTHONPATH=src python3 scripts/build_web_data.py
```

Then serve the repository root locally and open the displayed `web/` path:

```bash
python3 -m http.server 8000
```

The alpha uses relative asset paths and requires no backend, database, Python process, or Node process in production, so it is compatible with GitHub Pages project deployments. Browser semantics are checked against Python-generated fixtures with:

```bash
node web/tests/parity.mjs
```

The Scenario Lab supports only the frozen v0 accounting and explicitly enabled assumptions. The ETT calculator applies only the documented exported-coal AMNAT rule; it does not compute CIT, dividends, GDP, or national fiscal effects. Reviewed MRPAM rows are curated in `data/metadata/mrpam-price-review-v0.json`; the deployed alpha includes only their public subset. See [`docs/m4-v0-engine.md`](docs/m4-v0-engine.md) and [`docs/ett-royalty-module-v0.md`](docs/ett-royalty-module-v0.md).
