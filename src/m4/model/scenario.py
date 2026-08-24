"""Accounting scenarios with opt-in assumptions, never fitted propagation."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Mapping
from .baseline import Baseline, COMMODITIES
from .closures import Closure
from .result import Result

REAL_OUTPUT = {"mining_real_output": "gdp_real2015_mining", "agriculture_real_output": "gdp_real2015_agriculture",
               "construction_real_output": "gdp_real2015_construction", "other_industry_real_output": None}
NOMINAL_GVA = {"mining_gva": "gdp_nominal_mining", "agriculture_gva": "gdp_nominal_agriculture",
               "construction_gva": "gdp_nominal_construction", "other_industry_gva": "other_industry_gva_nominal_mnt_million",
               "taxes_less_subsidies": "taxes_less_subsidies_nominal_mnt_million"}

@dataclass(frozen=True)
class Shock:
    """A multiplicative path. `quarters`, range, permanent date, and custom path are supported."""
    column: str
    multiplier: float = 1.0
    quarters: tuple[str, ...] = ()
    start: str | None = None
    end: str | None = None
    custom_path: Mapping[str, float] = field(default_factory=dict)

    def multipliers(self, available: list[str]) -> dict[str, float]:
        if self.custom_path: return dict(self.custom_path)
        if self.quarters: return {quarter: self.multiplier for quarter in self.quarters}
        if self.start:
            return {quarter: self.multiplier for quarter in available if quarter >= self.start and (self.end is None or quarter <= self.end)}
        return {}

@dataclass(frozen=True)
class AssumptionLinks:
    """Optional parameters; `None` means disabled, not zero."""
    lambda_revenue: float | None = None  # MNT revenue / MNT mining export-income change
    phi_revenue_to_expenditure: float | None = None  # MNT expenditure / MNT revenue change
    production_to_mining_output: Mapping[str, float] = field(default_factory=dict)  # real-output elasticity
    project_fiscal_receipts_mnt_million: Mapping[str, float] = field(default_factory=dict)

@dataclass(frozen=True)
class ProjectContribution:
    """Extension contract for a future project module; zeros have no macro effect."""
    project_id: str
    quarter: str
    commodity: str
    production_quantity: float = 0.0
    export_value_usd_thousand: float = 0.0
    fiscal_receipts_mnt_million: float = 0.0
    fiscal_receipts: Mapping[str, float] = field(default_factory=dict)
    domestic_wages_mnt_million: float = 0.0
    domestic_procurement_mnt_million: float = 0.0
    investment_mnt_million: float = 0.0

@dataclass
class Scenario:
    closure: Closure = Closure.HISTORICAL_DEFAULT
    shocks: list[Shock] = field(default_factory=list)
    links: AssumptionLinks = field(default_factory=AssumptionLinks)
    # Backward-compatible spelling; it is still an explicit policy parameter.
    fiscal_response_phi: float | None = None
    project_contributions: list[ProjectContribution] = field(default_factory=list)

    def run(self, baseline: Baseline) -> Result:
        scenario = {quarter: dict(row) for quarter, row in baseline.rows.items()}
        direct, linked, trace, undetermined = {}, {}, [], {}
        def change(bucket, quarter, column, delta):
            bucket.setdefault(quarter, {})[column] = bucket.setdefault(quarter, {}).get(column, 0.0) + delta
        def apply(quarter, column, multiplier, bucket, arrow_type, reason):
            old = scenario[quarter].get(column)
            if old is None: return False
            new = old * multiplier; scenario[quarter][column] = new; change(bucket, quarter, column, new-old)
            trace.append({"quarter": quarter, "from": reason, "to": column, "type": arrow_type,
                          "baseline": old, "scenario": new, "change": new-old})
            return True
        available = sorted(scenario)
        export_changed = set(); production_shocks = []
        for project in self.project_contributions:
            if project.quarter not in scenario: continue
            column = f"{project.commodity}_export_value_usd_thousand"
            if project.export_value_usd_thousand and scenario[project.quarter].get(column) is not None:
                scenario[project.quarter][column] += project.export_value_usd_thousand
                change(direct, project.quarter, column, project.export_value_usd_thousand); export_changed.add(project.quarter)
                trace.append({"quarter":project.quarter,"from":project.project_id,"to":column,"type":"institutional","change":project.export_value_usd_thousand})
            receipt = project.fiscal_receipts_mnt_million + sum(project.fiscal_receipts.values())
            if receipt and scenario[project.quarter].get("government_revenue_mnt_million") is not None:
                scenario[project.quarter]["government_revenue_mnt_million"] += receipt
                change(linked, project.quarter, "government_revenue_mnt_million", receipt)
                trace.append({"quarter":project.quarter,"from":project.project_id,"to":"government_revenue_mnt_million","type":"institutional","stream_types":sorted(project.fiscal_receipts),"change":receipt})
        for shock in self.shocks:
            if shock.column == "residual_export":
                for quarter, multiplier in shock.multipliers(available).items():
                    residual = baseline.residual_merchandise_exports_usd_million(quarter) if quarter in scenario else None
                    if residual is None: continue
                    old = scenario[quarter].get("exports_usd_million")
                    modeled = sum((scenario[quarter].get(f"{c}_export_value_usd_thousand") or 0) / 1000 for c in COMMODITIES)
                    new = modeled + residual * multiplier
                    if old is not None:
                        scenario[quarter]["exports_usd_million"] = new; change(direct, quarter, "exports_usd_million", new-old)
                        trace.append({"quarter":quarter,"from":"shock:residual_export","to":"exports_usd_million","type":"identity","change":new-old})
                        imports=scenario[quarter].get("imports_usd_million")
                        if imports is not None: scenario[quarter]["trade_balance_usd_million"] = new-imports; change(direct, quarter, "trade_balance_usd_million", new-imports-(baseline.rows[quarter].get("trade_balance_usd_million") or 0))
                continue
            target = REAL_OUTPUT.get(shock.column, NOMINAL_GVA.get(shock.column, shock.column))
            for quarter, multiplier in shock.multipliers(available).items():
                if quarter not in scenario: continue
                if target is None:
                    undetermined.setdefault(quarter, set()).add("gdp_real2015_total")
                    continue
                if shock.column.endswith("_export_price"):
                    commodity = shock.column.removesuffix("_export_price")
                    target = f"{commodity}_export_value_usd_thousand"
                if apply(quarter, target, multiplier, direct, "identity", f"shock:{shock.column}"):
                    if target.endswith("_export_quantity_thousand_t") or target.endswith("_export_quantity_t"):
                        commodity = target.removesuffix("_export_quantity_thousand_t").removesuffix("_export_quantity_t")
                        apply(quarter, f"{commodity}_export_value_usd_thousand", multiplier, direct, "identity", target)
                        export_changed.add(quarter)
                    elif target.endswith("_export_value_usd_thousand"):
                        export_changed.add(quarter)
                    elif target.endswith("_production_thousand_t") or target.endswith("_production_kg"):
                        production_shocks.append((quarter, target, multiplier))
                    elif target == "imports_usd_million":
                        exports=scenario[quarter].get("exports_usd_million")
                        if exports is not None:
                            old_tb=scenario[quarter].get("trade_balance_usd_million"); new_tb=exports-scenario[quarter][target]; scenario[quarter]["trade_balance_usd_million"]=new_tb
                            change(direct, quarter, "trade_balance_usd_million", new_tb-(old_tb or 0))
                            trace.append({"quarter":quarter,"from":"exports_usd_million - imports_usd_million","to":"trade_balance_usd_million","type":"identity","change":new_tb-(old_tb or 0)})
                if target in NOMINAL_GVA.values(): self._reaggregate_nominal_gdp(scenario, baseline, quarter, direct, trace)
                # Chain-linked components are non-additive; do not synthesize a real GDP total.
                if target in REAL_OUTPUT.values(): undetermined.setdefault(quarter, set()).add("gdp_real2015_total")
        for quarter in export_changed:
            self._reaggregate_exports(scenario, baseline, quarter, direct, trace)
            undetermined.setdefault(quarter, set()).update({"gdp_real2015_mining", "government_revenue_mnt_million",
                "government_expenditure_mnt_million", "gdp_real2015_construction"})
        # Explicit production-to-mining calibration; no default mapping exists.
        for quarter, column, multiplier in production_shocks:
            commodity = column.removesuffix("_production_thousand_t").removesuffix("_production_kg")
            elasticity = self.links.production_to_mining_output.get(commodity)
            mining = "gdp_real2015_mining"
            if elasticity is not None and scenario[quarter].get(mining) is not None:
                delta = baseline.rows[quarter][mining] * elasticity * (multiplier - 1)
                scenario[quarter][mining] += delta; change(linked, quarter, mining, delta)
                trace.append({"quarter": quarter, "from": column, "to": mining, "type": "calibrated_assumption",
                              "parameter": "production_to_mining_output", "change": delta})
                undetermined.get(quarter, set()).discard(mining)
            else: undetermined.setdefault(quarter, set()).add(mining)
        # Optional fiscal link converts USD million x MNT/USD into million MNT exactly.
        for quarter in export_changed:
            delta_usd_million = sum(((scenario[quarter].get(f"{c}_export_value_usd_thousand") or 0) -
                                     (baseline.rows[quarter].get(f"{c}_export_value_usd_thousand") or 0)) / 1000
                                    for c in COMMODITIES)
            if self.links.lambda_revenue is not None and baseline.rows[quarter].get("mnt_per_usd_quarterly_average") is not None:
                delta_income_mnt = delta_usd_million * baseline.rows[quarter]["mnt_per_usd_quarterly_average"]
                revenue = "government_revenue_mnt_million"
                if scenario[quarter].get(revenue) is not None:
                    delta = self.links.lambda_revenue * delta_income_mnt; scenario[quarter][revenue] += delta; change(linked, quarter, revenue, delta)
                    trace.append({"quarter": quarter, "from": "mining_export_income_mnt_million", "to": revenue,
                                  "type": "user_assumption", "parameter": "lambda_revenue", "change": delta})
                    undetermined.get(quarter, set()).discard(revenue)
        for quarter, receipt in self.links.project_fiscal_receipts_mnt_million.items():
            if quarter in scenario and scenario[quarter].get("government_revenue_mnt_million") is not None:
                scenario[quarter]["government_revenue_mnt_million"] += receipt; change(linked, quarter, "government_revenue_mnt_million", receipt)
                trace.append({"quarter": quarter, "from": "project_fiscal_receipts", "to": "government_revenue_mnt_million", "type": "institutional", "change": receipt})
        phi = self.links.phi_revenue_to_expenditure if self.links.phi_revenue_to_expenditure is not None else self.fiscal_response_phi
        if self.closure != Closure.FIXED_GOVERNMENT_SPENDING and phi is not None:
            for quarter, changes in linked.items():
                delta_revenue = changes.get("government_revenue_mnt_million", 0.0)
                spending = "government_expenditure_mnt_million"
                if delta_revenue and scenario[quarter].get(spending) is not None:
                    delta = phi * delta_revenue; scenario[quarter][spending] += delta; change(linked, quarter, spending, delta)
                    trace.append({"quarter": quarter, "from": "government_revenue_mnt_million", "to": spending,
                                  "type": "user_assumption", "parameter": "phi_revenue_to_expenditure", "change": delta})
                    undetermined.get(quarter, set()).discard(spending)
        assumptions=[]
        if self.links.lambda_revenue is not None: assumptions.append({"parameter":"lambda_revenue","status":"user_assumption","value":self.links.lambda_revenue})
        if phi is not None: assumptions.append({"parameter":"phi_revenue_to_expenditure","status":"user_assumption","value":phi})
        if self.links.production_to_mining_output: assumptions.append({"parameter":"production_to_mining_output","status":"calibrated_assumption","value":dict(self.links.production_to_mining_output)})
        if self.project_contributions: assumptions.append({"parameter":"project_contributions","status":"institutional_interface","value":[p.project_id for p in self.project_contributions]})
        return Result(baseline.rows, scenario, self.closure.value, {c: baseline.unit(c) for r in scenario.values() for c in r}, direct, linked, trace, assumptions, undetermined)

    @staticmethod
    def _reaggregate_exports(scenario, baseline, quarter, direct, trace):
        modeled = sum((scenario[quarter].get(f"{c}_export_value_usd_thousand") or 0) / 1000 for c in COMMODITIES)
        residual = baseline.residual_merchandise_exports_usd_million(quarter)
        if residual is not None:
            old = scenario[quarter].get("exports_usd_million"); new = modeled + residual
            if old is not None:
                scenario[quarter]["exports_usd_million"] = new; direct.setdefault(quarter, {})["exports_usd_million"] = direct.setdefault(quarter, {}).get("exports_usd_million", 0) + new-old
                trace.append({"quarter":quarter,"from":"modeled commodity exports + observed residual merchandise exports","to":"exports_usd_million","type":"identity","change":new-old})
                imports = scenario[quarter].get("imports_usd_million")
                if imports is not None:
                    old_tb=scenario[quarter].get("trade_balance_usd_million"); new_tb=new-imports; scenario[quarter]["trade_balance_usd_million"]=new_tb
                    direct[quarter]["trade_balance_usd_million"] = direct[quarter].get("trade_balance_usd_million",0)+(new_tb-(old_tb or 0))
                    trace.append({"quarter":quarter,"from":"exports_usd_million - imports_usd_million","to":"trade_balance_usd_million","type":"identity","change":new_tb-(old_tb or 0)})

    @staticmethod
    def _reaggregate_nominal_gdp(scenario, baseline, quarter, direct, trace):
        fields=["gdp_nominal_mining","gdp_nominal_agriculture","gdp_nominal_construction","other_industry_gva_nominal_mnt_million","taxes_less_subsidies_nominal_mnt_million"]
        if all(scenario[quarter].get(field) is not None for field in fields) and scenario[quarter].get("gdp_nominal_total") is not None:
            new=sum(scenario[quarter][field] for field in fields); old=scenario[quarter]["gdp_nominal_total"]; scenario[quarter]["gdp_nominal_total"]=new
            direct.setdefault(quarter,{})["gdp_nominal_total"] = direct.setdefault(quarter,{}).get("gdp_nominal_total",0)+new-old
            trace.append({"quarter":quarter,"from":"Y_M + Y_A + Y_C + Y_O + T","to":"gdp_nominal_total","type":"identity","change":new-old})
