// static/js/core/calculator.js
export function calculatePricing() {
  const getNumber = (id) => {
    const val = $(id).val() || '0';
    const num = Number(val);
    return isNaN(num) ? 0 : num;
  };

  const stock = getNumber("#sell_price");
  const margin = getNumber("#trade_margin");
  const discount = getNumber("#trade_discount");
  const commission = getNumber("#agent_commission_rate");
  const vat = getNumber("#vat_rate");
  const qty = getNumber("#qty");

  const crude = stock * margin;
  const discountAmt = crude * (discount / 100);
  const priceAfterDiscount = crude - discountAmt;
  const commissionAmt = priceAfterDiscount * (commission / 100);
  const finalNoVat = priceAfterDiscount - commissionAmt;
  const totalNoVat = finalNoVat * qty; // Multiply by quantity for total w/o VAT
  const vatAmount = totalNoVat * (vat / 100); // VAT on total w/o VAT
  const total = totalNoVat + vatAmount; // Total including VAT
  const profit = (finalNoVat - stock) * qty; // Profit calculation

  const format = (v) => (isFinite(v) && !isNaN(v)) ? v.toFixed(2) : '0.00';

  $("#crude_price").val(format(crude));
  $("#discount_amount").val(format(discountAmt));
  $("#commission_amount").val(format(commissionAmt));
  $("#final_sell_price_without_vat").val(format(finalNoVat));
  $("#vat_amount").val(format(vatAmount));
  $("#customer_price").val(format(total));
  $("#profit").val(format(profit));
  $("#total_amount").val(format(total));
}