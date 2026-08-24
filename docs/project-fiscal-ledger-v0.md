# Project fiscal ledger v0

Phase 5A is an institutional evidence audit. It does not activate project fiscal propagation, estimate `lambda_revenue`, forecast profit, or create a public UI. The machine-readable source registry is [`project-fiscal-sources.yml`](../data/metadata/project-fiscal-sources.yml) and inert rule records are in [`data/metadata/project-fiscal-rules/`](../data/metadata/project-fiscal-rules/).

## Taxonomy and evidence statuses

The ledger keeps the following flows separate: mineral royalty/АМНАТ (*ашигт малтмалын нөөц ашигласны төлбөр*); corporate income tax/ААНОАТ (*аж ахуйн нэгжийн орлогын албан татвар*); state dividends/төрийн ногдол ашиг; customs, VAT and other taxes; licence, land, water and environmental payments; project-specific payments; financing flows (shareholder loans, interest, equity funding and debt repayment); and non-fiscal domestic flows (wages, procurement and investment). “Government take” is not a model variable.

Each record uses one of `EXACT_STATUTORY_RULE`, `EXACT_CONTRACTUAL_RULE`, `COMPANY_REPORTED_ACTUAL`, `GOVERNMENT_REPORTED_ACTUAL`, `DERIVED_ACCOUNTING`, `USER_ASSUMPTION_REQUIRED`, or `UNRESOLVED`. A source can establish a tax *rate* while leaving liability `NOT_CURRENTLY_COMPUTABLE` because its tax base is unavailable.

## ETT — Erdenes Tavan Tolgoi

ETT is the first candidate for an institutional royalty module. The current Minerals Law states a 5% base mineral royalty for the relevant non-gold minerals and adds a coal product/benchmark-price schedule: raw coal adds 0–5 percentage points across listed price bands and processed coal adds 0–3 points. It requires royalty calculation from sales assessment and government-published commodity-exchange prices for exported products. The law also makes the payment/reporting timing explicit. This is an exact statutory schedule, but it is not yet executable: ETT’s product classification, sales assessment, statutory reference-price series, and effective-date mapping must be supplied. Source: [Minerals Law, Articles 47.10–47.18](https://legalinfo.mn/mn/edtl/16532346138581).

Corporate income tax is not a percentage of sales. The statutory annual tax base is taxable income after deductions and permitted carried losses; the general schedule is 10% through MNT 6bn taxable income and 25% marginally above that threshold. Mining license holders calculate/report by licence. Public sales and net profit do not provide deductible costs, tax depreciation, financing treatment, licence-level returns, or confirmed losses, so ETT CIT is **not currently computable**. Sources: [CIT Law Articles 18–20 and 26](https://legalinfo.mn/mn/detail?lawId=14407).

ETT’s official [annual-report archive](https://www.ett.mn/report) covers 2019–2025 and is the primary collection point for production, sales, export, revenue, profit, and declared-dividend fields. The Phase 5A table below records only values safely identified as aggregate payments; it deliberately does not relabel them as royalty or CIT.

| year | reported aggregate ETT extractive-sector payments, MNT million | fiscal-flow detail | evidence | reconciliation status |
|---|---:|---|---|---|
| 2019 | 710,227 | not separated in this ledger | EITI top-taxpayer table | reported actual only |
| 2020 | 468,569 | not separated | EITI | reported actual only |
| 2021 | 294,949 | not separated | EITI | reported actual only |
| 2022 | 1,052,562.8 | not separated | EITI | reported actual only |
| 2023 | 2,854,882 | not separated | EITI | reported actual only |
| 2024 | 3,376,453.1 | not separated | EITI | reported actual only |
| 2025 | not extracted | official report archive is available; no interpolation | ETT | unresolved |

The 2019–2024 aggregate values are from the [2024 EITI reconciliation report](https://api.eiti.org/sites/default/files/SICA_EITI_Final%20report_20251201%20ENG.pdf). They cannot validate a royalty formula without royalty-only payments, product-price inputs, and payment-period alignment. Dividends are **reported actual only** until the shareholder-resolution and recipient data are collected; ownership is not a mechanical annual payout rate. ETT’s ownership structure and any special fiscal arrangement remain `UNRESOLVED` in this audit rather than being inferred from secondary descriptions.

## Oyu Tolgoi

Mongolia holds 34% through Erdenes Oyu Tolgoi LLC according to OT’s current disclosure. The signed 2009 Investment Agreement establishes a stabilized tax framework; the agreement defines stabilization as preserving the rate and basis during its term unless law lowers them. The exact currently operative rule set still needs clause-by-clause mapping against amendments and disputes. Sources: [2009 IA](https://admin.ot.mn/wp-content/uploads/ot/content/about_us/IA/Oyu_Tolgoi_IA_EN.pdf) and [OT’s 2026 disclosure](https://www.ot.mn/en/news/2026-%D0%BE%D0%BD%D1%8B-%D0%BD%D1%8D%D0%B3%D0%B4%D2%AF%D0%B3%D1%8D%D1%8D%D1%80-%D1%83%D0%BB%D0%B8%D1%80%D0%BB%D1%8B%D0%BD-%D1%82%D0%B0%D0%B0%D0%BB%D0%B0%D0%BD).

An issuer technical report describes 5% gross-sales royalty rates for copper, gold, and silver; 25% CIT; an eight-year loss-carry-forward limitation; a 10% investment tax credit with stated limits; and several withholding/VAT terms. It is useful evidence, not sufficient to activate a module while agreement amendments, tax disputes, sales-royalty calculation, tax credits, deductions, and timing remain unverified. Source: [OT technical report, Table 19-5](https://www.sec.gov/Archives/edgar/data/863064/000162828023004989/exhibits-963otsxk1300trs.htm).

State equity does not equal contemporaneous 34% of annual profits or cash. Public 2022 disclosure reports that USD 2.4bn of Government Debt was waived, while existing shareholder loans/debt had priority before dividends and future distributions remained subject to profit, reserves, and financing conditions. This is a financing/carry-account matter, not tax revenue or an automatic dividend. Source: [2022 agreements disclosure](https://www.sec.gov/Archives/edgar/data/1158041/000119312522063123/d272981dex991.htm). OT reports MNT 14.4tn in aggregate taxes, royalties and other payments since 2010, but this is an aggregate company claim, not a royalty/CIT reconciliation. [OT statement](https://www.ot.mn/en/news/oyu-tolgoi-llc-statement-on-the-tax-act).

## Badrakh Energy / Zuuvch Ovoo

Badrakh is a fiscal-design comparator, not a current macro driver. The published 2025 Investment Agreement provides for conversion of the Government’s stated 34% common-share position into non-dilutable 10% state-owned preferred shares, with a 10:90 government/investor ratio, and states that Government has no equity or debt financing obligation. It also refers to dividend conditions. The agreement must be used—not promotional summaries—for provision-level implementation. Source: [2025 Investment Agreement](https://badrakhenergy.com/wp-content/uploads/2026/05/Investment-Agreement_2025.01.17.pdf).

The reported “more than 51% direct benefits” is not an annual fiscal-receipts formula. It combines taxes, royalties, and dividends over an agreement-defined project cash-flow concept, so it is **not currently computable** without the precise definition, price/reference-price terms, production, costs, and timing. Royalty, transfer-pricing/arm’s-length treatment, and special-payment clauses remain `UNRESOLVED` pending clause extraction and the applicable Nuclear Energy/mineral-law mapping. No production forecast is created.

## Comparison

| feature | ETT | OT | Badrakh |
|---|---|---|---|
| state relationship | state-owned structure requires primary ownership confirmation | 34% via Erdenes Oyu Tolgoi LLC | 10% non-dilutable preferred shares; 90% investor stated in agreement |
| state financing burden | unresolved in this audit | financing/carry-account history materially affects dividends | agreement states no state equity/debt financing obligation |
| royalty readiness | statutory coal schedule; additional inputs needed | reported terms, but agreement/amendment verification needed | unresolved |
| CIT readiness | rate known, tax base unavailable | reported rate/credits, tax base unavailable | unresolved |
| dividends | declaration/ownership evidence needed | debt, reserves and payout priority preclude simple ownership multiplication | contractual preferred-share conditions require full cash-flow inputs |
| macro status | material coal producer | material copper-gold producer | institutionally informative; zero historical production in M4 |

## What can be implemented safely in Phase 5B

- **Implement:** inert royalty input validation and a generic piecewise schedule evaluator only after a project record supplies sourced product, reference-price, sales-base, threshold, and effective-date inputs.
- **Implement only with user input:** ETT coal royalty calculation for a stated product/sales/reference-price path; no defaults.
- **Reported-actuals display only:** EITI/company aggregate payments and declared dividends until stream-level evidence is reconciled.
- **Defer:** ETT/OT CIT liabilities, all automatic dividends, OT financing/carry-account simulation, Badrakh royalty/direct-benefit calculation, and any generic mining-export-to-revenue link.

## Phase 5B update — ETT exported-coal AMNAT

The narrow exported-coal evaluator is now available behind explicit inputs only. It uses the dated legal record, returns a separately labelled `mineral_royalty_amnat` receipt, and never invokes generic `lambda_revenue`. The temporary 2025 MSE valuation provision is recorded but not automated and is not selected in 2026. See [`ett-royalty-module-v0.md`](ett-royalty-module-v0.md).

## Future project-fiscal chain

`physical production → sales/export quantity → realised/reference price → project revenue → statutory/contractual streams → receipts by type → government revenue accounting`.

Each arrow must be evidenced. Wages, procurement, and investment remain non-fiscal domestic flows and cannot be booked as government receipts.
