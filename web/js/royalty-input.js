// Form values must be present, finite decimal numbers; absence is never zero.
export function formNumber(value) {
  if (typeof value !== "string" || !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:e[+-]?\d+)?$/i.test(value.trim())) return null;
  const number=Number(value);
  return Number.isFinite(number) ? number : null;
}

export function officialPriceRecord(records, id) {
  return typeof id === "string" && id !== ""
    ? records.find(record=>record.record_id===id && record.review_status==="REVIEWED") || null
    : null;
}

export function royaltyFormInput(data, record=null) {
  const quantity=formNumber(data.get("quantity")), fx=formNumber(data.get("fx"));
  const month=data.get("month"), product=data.get("product_class");
  const price=record ? record.price_usd_per_tonne : formNumber(data.get("price"));
  if (record && (month!==record.applicable_royalty_month || product!==record.coal_processing_class)) return null;
  if (![quantity,price,fx].every(Number.isFinite) || quantity<0 || price<0 || fx<=0 || !Number.isFinite(quantity*price*fx)) return null;
  return {transaction_month:month,quantity_tonnes:quantity,product_class:product,price_usd_per_tonne:price,mnt_per_usd:fx,sale_type:"exported",product_mapping_status:"EXACT"};
}
