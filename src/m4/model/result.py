"""Browser-serializable result records with direct/linked decomposition."""
from __future__ import annotations
from dataclasses import dataclass, field

NOT_DETERMINED = "NOT_DETERMINED_UNDER_CURRENT_CLOSURE"

@dataclass
class Result:
    baseline: dict
    scenario: dict
    closure: str
    units: dict[str, str | None] = field(default_factory=dict)
    direct: dict = field(default_factory=dict)
    linked: dict = field(default_factory=dict)
    trace: list[dict] = field(default_factory=list)
    assumptions_used: list[dict] = field(default_factory=list)
    undetermined: dict = field(default_factory=dict)

    def comparison(self, quarter: str, column: str) -> dict:
        if column in self.undetermined.get(quarter, set()):
            return {"status": NOT_DETERMINED, "baseline_value": self.baseline[quarter].get(column),
                    "scenario_value": None, "absolute_change": None, "percent_change": None,
                    "direct_change": None, "linked_change": None, "unit": self.units.get(column),
                    "source_baseline_period": quarter, "closure": self.closure,
                    "assumptions_used": self.assumptions_used}
        base, scenario = self.baseline[quarter].get(column), self.scenario[quarter].get(column)
        absolute = None if base is None or scenario is None else scenario - base
        return {"status": "DETERMINED", "baseline_value": base, "scenario_value": scenario,
                "absolute_change": absolute, "percent_change": None if absolute is None or base == 0 else 100 * absolute / base,
                "absolute_deviation": absolute, "percentage_deviation": None if absolute is None or base == 0 else 100 * absolute / base,
                "direct_change": self.direct.get(quarter, {}).get(column, 0.0),
                "linked_change": self.linked.get(quarter, {}).get(column, 0.0), "unit": self.units.get(column),
                "source_baseline_period": quarter, "closure": self.closure,
                "assumptions_used": self.assumptions_used}

    def fiscal_balance(self, quarter: str) -> float | None:
        row = self.scenario[quarter]; revenue, spending = row.get("government_revenue_mnt_million"), row.get("government_expenditure_mnt_million")
        return None if revenue is None or spending is None else revenue - spending

    def to_dict(self) -> dict:
        return {"closure": self.closure, "assumptions_used": self.assumptions_used,
                "trace": self.trace, "quarters": {q: {column: self.comparison(q, column)
                for column in sorted(set(self.baseline[q]) | set(self.scenario[q]))} for q in self.scenario}}
