# M4 conceptual notes (v0)

This is a design note, not a fitted model. No coefficients are assigned here.

\[
GDP = Y_M + Y_A + Y_C + Y_O + T
\]

```text
commodity price/quantity
    ↓
mineral export revenue
    ↓
+------------------+------------------+------------------+
| fiscal revenue   | foreign exchange | domestic linkage |
+------------------+------------------+------------------+
        ↓                  ↓                   ↓
government spending   reserves/MNT       wages/procurement
        ↓                  ↓                   ↓
construction/core    imports/inflation    domestic demand
```

The model may later use a **domestic capture ratio** to describe the share of a mining shock that enters domestic income, fiscal receipts or demand. Its accounting definition is unresolved: wages, domestic procurement, taxes, dividends, imports, financing flows and retained earnings overlap unless the boundary and consolidation rules are specified. It is not a v0 propagation parameter.

Construction is kept as a provisional separate sector because it may respond differently to public capital spending, mine development, credit and import-intensive investment. It remains a hypothesis to test, not a structural assumption. `Y_O` is the reconciled other-industry GVA component; it is not the older broad “N/core” category.
