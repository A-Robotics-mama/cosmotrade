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
  // Изменено: добавлен расчет НДС для одной единицы вместо НДС для общего количества
  // Было: const totalNoVat = finalNoVat * qty; const vatAmount = totalNoVat * (vat / 100);
  const vatPerUnit = finalNoVat * (vat / 100); // НДС для одной единицы
  // Изменено: Customer Price теперь рассчитывается как цена без НДС + НДС для одной единицы
  // Было: const total = (finalNoVat + vatAmount);
  const customerPrice = finalNoVat + vatPerUnit; // Цена для клиента за единицу
  // Изменено: Total Amount теперь рассчитывается как customerPrice * qty
  // Было: использование неправильного total
  const totalAmount = customerPrice * qty; // Общая сумма с НДС для всех единиц
  const profit = (finalNoVat - stock) * qty;

  const format = (v) => (isFinite(v) && !isNaN(v)) ? v.toFixed(2) : '0.00';

  $("#crude_price").val(format(crude));
  $("#discount_amount").val(format(discountAmt));
  $("#commission_amount").val(format(commissionAmt));
  $("#final_sell_price_without_vat").val(format(finalNoVat));
  // Изменено: vat_amount теперь отображает НДС для одной единицы
  // Было: $("#vat_amount").val(format(vatAmount));
  $("#vat_amount").val(format(vatPerUnit));
  // Изменено: customer_price теперь отображает цену за единицу с НДС
  // Было: $("#customer_price").val(format(total));
  $("#customer_price").val(format(customerPrice));
  $("#profit").val(format(profit));
  // Изменено: total_amount теперь отображает общую сумму для всех единиц
  // Было: $("#total_amount").val(format(total));
  $("#total_amount").val(format(totalAmount));
}