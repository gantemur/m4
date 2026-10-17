import assert from "node:assert/strict";
import {readFile} from "node:fs/promises";
import {formNumber,officialPriceRecord,royaltyFormInput} from "../js/royalty-input.js";
import {evaluateRoyalty} from "../js/engine.js";

for(const value of [null,undefined,""," ","NaN","Infinity","-Infinity","1e999","0x10","12x",{},true]) assert.equal(formNumber(value),null,`Invalid numeric input: ${String(value)}`);
for(const [value,expected] of [["0",0],["77.33",77.33],[" 100 ",100],["1e3",1000],[".5",.5]]) assert.equal(formNumber(value),expected);
const records=JSON.parse(await readFile(new URL("../data/mrpam-reviewed-coal-prices-v0.json",import.meta.url))).records;
const record=records[0], rules=JSON.parse(await readFile(new URL("../data/ett-coal-royalty-v0.json",import.meta.url)));
for(const id of ["",null,undefined,"0","unknown"]) assert.equal(officialPriceRecord(records,id),null);
assert.equal(officialPriceRecord(records,record.record_id),record);
assert.equal(officialPriceRecord([{...record,review_status:"PARSED_UNREVIEWED"}],record.record_id),null);
const values={month:record.applicable_royalty_month,product_class:record.coal_processing_class,quantity:"1000",price:"100",fx:"3500"};
const data=overrides=>new Map(Object.entries({...values,...overrides}));
const official=royaltyFormInput(data({price:null}),record);
assert.equal(official.price_usd_per_tonne,77.33,"Selected record is authoritative even if a protected control is absent");
assert.equal(evaluateRoyalty(official,rules).assessed_sales_value_mnt,270655000);
assert.equal(evaluateRoyalty(official,rules).total_royalty_mnt,21652400);
assert.equal(royaltyFormInput(data({})).price_usd_per_tonne,100,"Manual path uses the actual form price");
for(const field of ["quantity","price","fx"]){
  for(const value of [null,undefined,""," ","invalid","NaN","Infinity","1e999","-1"]){
    assert.equal(royaltyFormInput(data({[field]:value})),null,`${field} must reject ${String(value)}`);
  }
}
assert.equal(royaltyFormInput(data({fx:"0"})),null);
assert.equal(royaltyFormInput(data({quantity:"1e308",price:"1e308"})),null,"Overflow cannot produce a determined amount");
assert.equal(royaltyFormInput(data({quantity:"0"})).quantity_tonnes,0,"Explicit zero quantity retains existing semantics");
assert.equal(royaltyFormInput(data({price:"0"})).price_usd_per_tonne,0,"Explicit zero price retains existing semantics");
assert.equal(royaltyFormInput(data({month:"2026-09"}),record),null,"A selected record cannot silently follow a changed month");
assert.equal(royaltyFormInput(data({product_class:"processed_coal"}),record),null);
console.log("Royalty form input normalization passed.");
