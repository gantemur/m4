import "./royalty-input.mjs";
import assert from "node:assert/strict";
import {readdir,readFile} from "node:fs/promises";
import {evaluateRoyalty,runScenario} from "../js/engine.js";
import {decodeScenario,encodeScenario} from "../js/url-state.js";
import {labelVariable,publicStatus,traceEndpoint,VARIABLE_LABEL_KEYS} from "../js/display.js";
const path=new URL("../../tests/fixtures/model-parity/",import.meta.url);
function same(actual, expected, label="root") { if (typeof expected === "number") return assert.ok(Math.abs(actual-expected) <= 1e-8 * Math.max(1,Math.abs(expected)), `${label}: ${actual} != ${expected}`); if (expected === null || typeof expected !== "object") return assert.equal(actual,expected,label); assert.deepEqual(Object.keys(actual).sort(),Object.keys(expected).sort(),label); for (const key of Object.keys(expected)) same(actual[key],expected[key],`${label}.${key}`); }
const files=await readdir(path); for(const name of files.filter(x=>x.endsWith(".json")&&x!=="royalty.json")){const f=JSON.parse(await readFile(new URL(name,path)));const actual=runScenario(f.baseline,{closure:f.closure,shocks:f.shocks,links:f.links},f.units);same({closure:actual.closure,assumptions_used:actual.assumptions_used,trace:actual.trace,quarters:actual.quarters},f.expected,`model parity: ${name}`)}
const rules=JSON.parse(await readFile(new URL("../data/ett-coal-royalty-v0.json",import.meta.url)));for(const c of JSON.parse(await readFile(new URL("royalty.json",path)))){const actual=evaluateRoyalty(c.input,rules);if(c.expected_status)assert.equal(actual.status,c.expected_status);else {for(const k of ["status","rule_version","assessed_sales_value_usd","assessed_sales_value_mnt","base_royalty_mnt","additional_royalty_mnt","total_royalty_mnt","total_royalty_million_mnt","base_rate_percent","additional_rate_percent","total_rate_percent"])assert.deepEqual(actual[k],c.expected[k],`royalty ${k}`)}}
const shared={quarter:"2026-Q2",values:{coal_export_quantity_thousand_t:-30},lambda:null,phi:null};assert.deepEqual(decodeScenario(encodeScenario(shared)),shared,"URL scenario round trip");
for (const [label, value] of [
  ["invalid Base64URL character", "%%%"],
  ["impossible Base64URL length", "A"],
  ["invalid UTF-8 payload", "_w"],
  ["invalid JSON payload", "ew"],
  ["empty shared state", ""],
]) assert.equal(decodeScenario(value),null,`Malformed URL scenario: ${label}`);
const unicodeShared={...shared,name:"Монголын эдийн засаг — нүүрс 🏔️"};
const unicodeEncoded=encodeScenario(unicodeShared);
assert.match(unicodeEncoded,/^[A-Za-z0-9_-]+$/,"Unicode scenario uses unpadded Base64URL");
assert.deepEqual(decodeScenario(unicodeEncoded),unicodeShared,"Unicode URL scenario round trip");
const labels={"variables.coalExportQuantity":"Coal export quantity","variables.coalExportValue":"Coal export value","variables.copperExportValue":"Copper-concentrate export value","variables.totalMerchandiseExports":"Total merchandise exports","variables.tradeBalance":"Trade balance","variables.unspecifiedOutcome":"Other outcome"}; const translate=key=>labels[key]||key;
assert.equal(labelVariable(translate,"coal_export_value_usd_thousand"),"Coal export value");assert.equal(labelVariable(translate,"copper_concentrate_export_value_usd_thousand"),"Copper-concentrate export value");assert.equal(labelVariable(translate,"exports_usd_million"),"Total merchandise exports");assert.equal(labelVariable(translate,"trade_balance_usd_million"),"Trade balance");
for(const code of Object.keys(VARIABLE_LABEL_KEYS)){assert.ok(!labelVariable(translate,code).includes("_"),`internal code leaked: ${code}`)}
assert.ok(!traceEndpoint(translate,"shock:coal_export_quantity_thousand_t",{shocks:[{column:"coal_export_quantity_thousand_t",multiplier:.7}]}).includes("coal_export_quantity"));
const coalScenario={shocks:[{column:"coal_export_quantity_thousand_t",multiplier:.7}]};assert.equal(publicStatus({column:"coal_export_value_usd_thousand",status:"DETERMINED",absolute_change:-1,direct_change:-1,linked_change:0},coalScenario),"ACCOUNTING_IDENTITY");assert.equal(publicStatus({column:"gdp_real2015_mining",status:"DETERMINED",absolute_change:0,direct_change:0,linked_change:0},coalScenario),"HELD_AT_BASELINE");
console.log("Browser model and royalty parity fixtures passed.");
