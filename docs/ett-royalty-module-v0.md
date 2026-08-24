# ETT coal royalty / AMNAT module v0

This is the sole Phase 5B institutional module. It calculates a single **exported ETT coal product/month** only when a caller provides quantity, statutory processing class, official reference price, MNT/USD, and provenance. It does not calculate CIT, dividends, domestic coal royalty, total ETT AMNAT, government spending, GDP, FX, or any forecast.

## Current legal regime at 2026-08-24

The applicable implemented regime is the general exported-mineral rule: the sales assessment for coal exported or shipped for export is based on the designated government price-source information; the current 2019 regulation states that notice prices are used for exports in the preceding month. The valuation regulation separately requires the published coal market-price sources or a qualifying contract-value process. No processing, transport, refining, or other operating costs are deducted from the assessment value under the general regulation. Sources: [Resolution 465/2019](https://legalinfo.mn/mn/detail?lawId=210505) and [Resolution 342/2019 coal valuation rule](https://legalinfo.mn/mn/detail?lawId=210089).

Article 47.17 provides a 5% base royalty for exported coal plus an additional rate determined by processing class and USD/tonne market-price bracket. The module reads the schedules from [`ett-coal-royalty-v0.json`](../data/metadata/project-fiscal-rules/ett-coal-royalty-v0.json), not from hidden code. Exact threshold values are assigned to the lower “up to” bracket; this documented implementation convention must yield to a future authoritative clarification. Source: [Minerals Law](https://legalinfo.mn/mn/edtl/16532346138581).

| class | additional rate schedule, percentage points |
|---|---|
| raw coal | ≤25: 0; ≤50: 1; ≤75: 2; ≤100: 3; ≤125: 4; >125: 5 |
| processed coal | ≤100: 0; ≤130: 1; ≤160: 1.5; ≤190: 2; ≤210: 2.5; >210: 3 |
| final product | ≤160: 0; ≤190: 0.5; ≤210: 1; ≤240: 1.5; ≤270: 2; >270: 2.5 |

Domestic coal is deliberately rejected with `NOT_DETERMINED_UNDER_CURRENT_CLOSURE`. The law distinguishes domestic coal; this exported-only module does not assume that the export schedule applies to domestic sales.

## Legal-regime timeline

| period | valuation rule | module status |
|---|---|---|
| 2019-Q3 onward | Resolution 342 governs foreign-market coal sales assessment, subject to source/contract conditions | historical legal context |
| 2019-12-25 onward | Resolution 465 general calculation/reporting regime | general exported-reference evaluator |
| 2025-08-20 to 2025-12-31 | Resolution 55 temporary MSE provision for exporters meeting the one-quarter condition | recorded, `USER_INPUT_REQUIRED`; not automated |
| 2026 onward | temporary clauses expired; no post-2025 extension/replacement was located in this Legalinfo audit | general exported-reference rule only |

Resolution 55 says that if at least one quarter of the relevant export product was traded on the Mining Products Exchange, MSE pricing could be used for all exports of that product—but expressly only through 2025-12-31. Product matching, test-period/denominator, price selection/weighting, and currency semantics are not complete enough to automate. [Resolution 55/2025](https://legalinfo.mn/mn/detail?lawId=17432738537662)

## Reference-price acquisition and product crosswalk

MRPAM’s monthly notices provide coal type, quality requirements, USD/tonne price, publication date, and observation-month timing. The notice itself says a month’s published price is based on the preceding month’s average. The module provides `download_mrpam_notice()` to retain the raw response under a caller-selected raw directory and return its SHA-256, and `parse_mrpam_notice_html()` to return matching table rows for review; it does not guess a price from unstructured text. Example notice: [March 2026 MRPAM notice](https://mrpam.gov.mn/news/international-market-price-information-for-exported-mineral-products-59).

The MSE’s ETT `1/3 coking coal` advertisement includes quality fields. It maps to the statutory **raw coal** class only as `RULE_BASED` when volatile matter is >28–37% and caking index >65, matching the MRPAM row. Missing quality fields produce `AMBIGUOUS`; all other labels are `UNMAPPED` until audited. [MSE ETT product notice](https://mse.mn/uploads/auction_schedules/en-ETT-25-54-1-3-CO.pdf)

## API and accounting

`RoyaltyInput` requires tonnes, USD/tonne `ReferencePrice`, and MNT/USD. The evaluator calculates:

`V_assess_USD = tonnes × USD/tonne`

`V_assess_MNT = V_assess_USD × MNT/USD`

`AMNAT = V_assess_MNT × (5% + additional rate)`

It returns separate assessment value, base royalty, additional royalty, total rate, total MNT and million-MNT liability, legal-regime/source IDs, assumptions, and institutional trace. A determined result exposes only `{"mineral_royalty_amnat": million_MNT}` through `fiscal_receipts()` / `to_project_contribution()`; adding that contribution to a scenario is an explicit caller action. There is no default propagation.

## Historical pilot and validation

No valid historical ETT pilot is published in this release. The inspected MSE records are auction advertisements (not proof of realised sale/settlement), while a transaction-month-complete pairing of ETT quantity, customs/statutory processing class, applicable MRPAM notice, MNT/USD, and valuation method was not recovered. Creating a calculation from total ETT volume, opening bid, or a notice from another month would be false precision.

Likewise, no royalty-only ETT historical payment was found in the audited sources. EITI aggregate company payments are not AMNAT and are not used for calibration or reconciliation.
