# M4 v0 engine

The engine is a non-UI Python API in `m4.model`. Load the corrected immutable v4 panel, construct `Shock` records, optionally supply `AssumptionLinks`, and call `Scenario.run`. `Result.to_dict()` produces browser-friendly JSON containing scenario definition effects, comparisons, assumptions, and a machine-readable trace.

```python
from m4.model import AssumptionLinks, Baseline, Closure, Scenario, Shock

base = Baseline.load("data/processed/m4-quarterly-v4.csv")
scenario = Scenario(
    Closure.USER_SPECIFIED_FISCAL_RESPONSE,
    [Shock("coal_export_quantity_thousand_t", multiplier=0.70, quarters=("2023-Q1",))],
    AssumptionLinks(lambda_revenue=0.10, phi_revenue_to_expenditure=0.50),
)
result = scenario.run(base)
```

The coal quantity shock trace includes `coal export quantity → coal export value → exports → trade balance` as `identity` arrows. With the optional links it additionally records mining-export income to revenue and revenue to expenditure as `user_assumption` arrows. Without a link, downstream outcomes such as mining real output and fiscal revenue are returned as `NOT_DETERMINED_UNDER_CURRENT_CLOSURE`, never as zero.

Direct changes are primitive shocks and their accounting consequences. Linked changes are effects of an enabled assumption. The result metadata carries both separately, units, baseline period, closure, and assumptions used.
