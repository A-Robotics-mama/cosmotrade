// static/js/pages/sale_retail.js

import { initCustomerAutocomplete } from "../autocomplete/customer_autocomplete.js";
import { initProductAutocomplete } from "../autocomplete/product_autocomplete.js";

export function initRetailPage() {
  console.log("🛍️ retail-form module initialized");

  const urls = window.urls;

  initCustomerAutocomplete();

  initProductAutocomplete({
    onPriceUpdate: calculatePricing
  });

  $("#sell_price, #trade_margin, #trade_discount, #agent_commission_rate, #vat_rate, #qty").on("input", calculatePricing);

  function calculatePricing() {
    const stockPrice = Number($("#sell_price").val()) || 0;
    const tradeMargin = Number($("#trade_margin").val()) || 1;
    const tradeDiscount = Number($("#trade_discount").val()) || 0;
    const agentRate = Number($("#agent_commission_rate").val()) || 0;
    const vatRate = Number($("#vat_rate").val()) || 0;
    const qty = Number($("#qty").val()) || 1;

    const crude = stockPrice * tradeMargin;
    const discount = crude * (tradeDiscount / 100);
    const afterDiscount = crude - discount;
    const commission = afterDiscount * (agentRate / 100);
    const priceNoVat = afterDiscount - commission;
    const vat = priceNoVat * (vatRate / 100) * qty;
    const customerPrice = priceNoVat + vat;
    const profit = (priceNoVat - stockPrice) * qty;

    $("#crude_price").val(crude.toFixed(2));
    $("#discount_amount").val(discount.toFixed(2));
    $("#commission_amount").val(commission.toFixed(2));
    $("#final_sell_price_without_vat").val(priceNoVat.toFixed(2));
    $("#vat_amount").val(vat.toFixed(2));
    $("#customer_price").val(customerPrice.toFixed(2));
    $("#profit").val(profit.toFixed(2));
    $("#total_amount").val(customerPrice.toFixed(2));
  }
}
