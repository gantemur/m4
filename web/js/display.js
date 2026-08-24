export const VARIABLE_LABEL_KEYS = Object.freeze({
  coal_export_quantity_thousand_t: "variables.coalExportQuantity",
  coal_export_value_usd_thousand: "variables.coalExportValue",
  coal_export_price: "variables.coalExportPrice",
  copper_concentrate_export_quantity_thousand_t: "variables.copperExportQuantity",
  copper_concentrate_export_value_usd_thousand: "variables.copperExportValue",
  copper_concentrate_export_price: "variables.copperExportPrice",
  gold_export_value_usd_thousand: "variables.goldExportValue",
  iron_ore_export_value_usd_thousand: "variables.ironOreExportValue",
  exports_usd_million: "variables.totalMerchandiseExports",
  imports_usd_million: "variables.imports",
  trade_balance_usd_million: "variables.tradeBalance",
  mnt_per_usd_quarterly_average: "variables.mntPerUsd",
  government_revenue_mnt_million: "variables.governmentRevenue",
  government_expenditure_mnt_million: "variables.governmentExpenditure",
  gdp_real2015_mining: "variables.miningRealOutput",
  gdp_real2015_agriculture: "variables.agricultureRealOutput",
  gdp_real2015_construction: "variables.constructionRealOutput",
  mining_real_output: "variables.miningRealOutput",
  agriculture_real_output: "variables.agricultureRealOutput",
  construction_real_output: "variables.constructionRealOutput",
  other_industry_real_output: "variables.otherIndustryRealOutput",
  taxes_less_subsidies: "variables.taxesLessSubsidies",
  residual_export: "variables.residualMerchandiseExports",
  gdp_real2015_total: "variables.realGdpTotal",
});

export function labelVariable(t, code) {
  return VARIABLE_LABEL_KEYS[code] ? t(VARIABLE_LABEL_KEYS[code]) : t("variables.unspecifiedOutcome");
}

export function traceEndpoint(t, value, definition) {
  if (value.startsWith("shock:")) {
    const code = value.slice(6);
    const shock = definition.shocks.find(item => item.column === code);
    return shock ? `${labelVariable(t, code)} ${new Intl.NumberFormat().format((shock.multiplier - 1) * 100)}%` : labelVariable(t, code);
  }
  const formulas = {
    "modeled commodity exports + observed residual merchandise exports": "trace.commodityExportsPlusResidual",
    "exports_usd_million - imports_usd_million": "trace.exportsMinusImports",
    "mining_export_income_mnt_million": "trace.miningExportIncome",
    "government_revenue_mnt_million": "variables.governmentRevenue",
    "Y_M + Y_A + Y_C + Y_O + T": "trace.nominalGdpIdentity",
  };
  return formulas[value] ? t(formulas[value]) : labelVariable(t, value);
}

export function publicStatus(row, definition) {
  if (row.status !== "DETERMINED") return row.status;
  if (!row.absolute_change) return "HELD_AT_BASELINE";
  const directlyShocked = definition.shocks.some(shock => {
    const target = shock.column.endsWith("_export_price")
      ? `${shock.column.replace(/_export_price$/, "")}_export_value_usd_thousand`
      : shock.column;
    return target === row.column;
  });
  if (directlyShocked) return "USER_ASSUMPTION";
  return row.linked_change ? "USER_ASSUMPTION" : "ACCOUNTING_IDENTITY";
}
