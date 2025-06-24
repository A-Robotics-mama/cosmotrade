// static/js/pages/sale_invoice.js
import { calculatePricing } from "../core/calculator.js";
import { initProductAutocomplete } from "../autocomplete/product_autocomplete.js";
import { initCustomerAutocomplete } from "../autocomplete/customer_autocomplete.js";

export function initInvoicePage() {
  console.log("📄 sale_invoice.js initialized");

  const saleForm = $("#sale-form");
  const quotationHeader = $("#quotation-header");
  const quotationTable = $("table.table, table.table-bordered");
  let quotationTableBody = quotationTable.find("tbody");
  const quotationTableFoot = quotationTable.find("tfoot");
  let completeBtn = $("#complete-quotation-btn");
  let completeBtnWrapper = $("#complete-quotation-wrapper");

  if (quotationTable.length === 0) {
    console.error("Table element not found, continuing without table initialization");
  } else if (quotationTableBody.length === 0) {
    console.warn("tbody not found, creating new one");
    quotationTableBody = $("<tbody>").appendTo(quotationTable);
  }

  const productInput = $("#product_input");
  const customerInput = $("#customer_input");

  $("#sell_price, #trade_margin, #trade_discount, #agent_commission_rate, #vat_rate, #qty")
    .on("input", calculatePricing);

  $("#add-item-btn").on("click", function(event) {
    event.preventDefault();

    if (!productInput.val()) {
      alert("Пожалуйста, заполните поле продукта.");
      return;
    }

    $.post(window.urls.addToQuotation, saleForm.serialize(), function(response) {
      if (response.error) {
        alert("❌ " + response.error);
        return;
      }

      if (quotationTable.length > 0) {
        quotationTableBody.empty();

        if (response.quotation_sales && response.quotation_sales.length > 0) {
          let rows = '';
          response.quotation_sales.forEach(sale => {
            rows += `
              <tr>
                <td>${sale.product__product_name || 'Unknown Product'}</td>
                <td>${sale.qty || 0}</td>
                <td>${parseFloat(sale.sell_price || 0).toFixed(2)}</td>
                <td>${parseFloat(sale.vat_rate || 0).toFixed(0)}</td>
                <td>${parseFloat(sale.sale_vat || 0).toFixed(2)}</td>
                <td>${parseFloat(sale.total_with_vat || 0).toFixed(2)}</td>
                <td>
                  <form method="post">
                    <input type="hidden" name="sale_id" value="${sale.id || ''}">
                    <button type="submit" class="btn btn-danger btn-sm">Delete</button>
                  </form>
                </td>
              </tr>
            `;
          });

          quotationTableBody.html(rows);

          quotationTableFoot.html(`
            <tr>
              <td colspan="5" class="text-end fw-bold">Total Amount:</td>
              <td>${parseFloat(response.total_amount || 0).toFixed(2)} €</td>
              <td></td>
            </tr>
          `);

          // Update quotation number and header
          if (response.quotation_number && response.quotation_number !== 'new') {
            quotationHeader.text("Quotation #" + response.quotation_number.replace("QUOTATION-", ""));
            $("#quotation_number").val(response.quotation_number);

            const completeUrl = `${window.urls.completeQuotationBase.replace(/\/$/, '')}/${response.quotation_number}/complete/`;

            if (completeBtn.length === 0) {
              completeBtn = $('<button type="button" id="complete-quotation-btn" class="btn btn-success ms-2"><i class="fas fa-check-circle me-1"></i> Complete Quotation</button>')
                .appendTo(completeBtnWrapper)
                .data("url", completeUrl)
                .prop("disabled", false)
                .removeClass("disabled-button")
                .on("click", function(event) {
                  event.preventDefault();
                  const url = $(this).data("url");
                  if (!url) return;
                  $.post(url, saleForm.serialize(), function(response) {
                    if (response.error) {
                      alert("❌ " + response.error);
                      return;
                    }
                    alert("✅ Котировка завершена!");
                    window.location.href = "/reports/quotations/";
                  }).fail(function(xhr) {
                    alert("❌ Ошибка завершения котировки: " + (xhr.responseJSON?.error || xhr.responseText));
                  });
                });
            } else {
              completeBtn.data("url", completeUrl).prop("disabled", false).removeClass("disabled-button");
            }
          }

          $("#product_input, #product_id, #invoice_input, #import_id, #invoice, #sell_price, #crude_price, #trade_discount, #discount_amount, #agent_commission_rate, #commission_amount, #final_sell_price_without_vat, #vat_amount, #customer_price, #profit, #total_amount").val("");
          $("#qty").val("1");
          $("#vat_rate").val("5");
          $("#invoice_input").prop("disabled", true);
        } else {
          quotationTableBody.append('<tr><td colspan="7" class="text-center text-muted">No items added to this quotation yet.</td></tr>');
        }
      }

      calculatePricing();
    }).fail(function(xhr) {
      alert("❌ Ошибка AJAX: " + (xhr.responseJSON?.error || xhr.responseText));
    });
  });

  completeBtn.on("click", function(event) {
    event.preventDefault();
    const url = $(this).data("url");
    if (!url) return;

    $.post(url, saleForm.serialize(), function(response) {
      if (response.error) {
        alert("❌ " + response.error);
        return;
      }
      alert("✅ Котировка завершена!");
      window.location.href = "/reports/quotations/";
    }).fail(function(xhr) {
      alert("❌ Ошибка завершения котировки: " + (xhr.responseJSON?.error || xhr.responseText));
    });
  });

  if (productInput.length) {
    initProductAutocomplete({
      inputId: "#product_input",
      hiddenId: "#product_id",
      invoiceInputId: "#invoice_input",
      importId: "#import_id",
      invoiceDisplayId: "#invoice",
      onPriceUpdate: calculatePricing,
      urls: window.urls
    });
  }

  if (customerInput.length && !customerInput.prop("disabled")) {
    initCustomerAutocomplete({ inputId: "#customer_input", hiddenId: "#customer_id" });
  }
}

export default initInvoicePage;