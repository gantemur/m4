# M4 v0 closures

All v0 closures use observed historical paths as the baseline. FX is exogenous in every current closure; a future endogenous-FX module is an interface reservation only.

| closure | government spending | FX | use |
|---|---|---|---|
| `historical-default` | observed path; no automatic response | observed or user-shocked exogenous path | primary historical counterfactual |
| `fixed-government-spending` | held to baseline | observed exogenous path | isolates fiscal-spending response |
| `user-specified-fiscal-response` | responds only through user-supplied `phi_R` | observed exogenous path | explicit policy assumption |
| `user-specified-fx` | chosen as above | supplied exogenous FX path | tests FX assumptions without causal FX equation |

Every result records its closure, baseline value, scenario value, direct and linked changes, assumptions, and explainability trace. No closure installs a historical regression coefficient.
