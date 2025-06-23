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
  const completeBtn = $("#complete-quotation-btn");

  if (quotationTable.length === 0) {
    console.error("Table element not found, continuing without table initialization");
  } else if (quotationTableBody.length === 0) {
    console.warn("tbody not found, creating new one");
    quotationTableBody = $("<tbody>").appendTo(quotationTable);
  }
  console.log("Table element:", quotationTable.length, "Body element:", quotationTableBody.length);

  const productInput = $("#product_input");
  const customerInput = $("#customer_input");
  console.log("Product input exists:", productInput.length, "Customer input exists:", customerInput.length);

  $("#sell_price, #trade_margin, #trade_discount, #agent_commission_rate, #vat_rate, #qty")
    .on("input", calculatePricing);

  $("#add-item-btn").on("click", function(event) {
    event.preventDefault();

    if (!productInput.val()) {
      alert("Пожалуйста, заполните поле продукта.");
      return;
    }

    $.post(window.urls.addToQuotation, saleForm.serialize(), function(response) {
      console.log("Server response:", JSON.stringify(response, null, 2));
      if (response.error) {
        alert("❌ " + response.error);
        return;
      }

      if (quotationTable.length > 0) {
        quotationTableBody.empty();
        console.log("Table body cleared, length:", quotationTableBody.length);

        if (response.quotation_sales && response.quotation_sales.length > 0) {
          let rows = '';
          response.quotation_sales.forEach(sale => {
            console.log("Processing sale:", JSON.stringify(sale, null, 2));
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
            console.log("Row appended for sale:", sale.product__product_name);
          });

          if (quotationTableBody[0]) {
            quotationTableBody[0].innerHTML = rows;
            console.log("Table body HTML set:", quotationTableBody[0].innerHTML);
          } else {
            console.error("quotationTableBody[0] is undefined, appending tbody");
            quotationTableBody = $("<tbody>").html(rows).appendTo(quotationTable);
          }

          quotationTableFoot.html(`
            <tr>
              <td colspan="5" class="text-end fw-bold">Total Amount:</td>
              <td>${parseFloat(response.total_amount || 0).toFixed(2)} €</td>
              <td></td>
            </tr>
          `);

          if (response.quotation_number) {
            quotationHeader.text("Quotation #" + response.quotation_number.replace("QUOTATION-", ""));
            $("#quotation_number").val(response.quotation_number);

            if (window.urls.completeQuotationBase) {
              const completeUrl = `${window.urls.completeQuotationBase.replace(/\/$/, '')}/${response.quotation_number}/complete/`;
              if (completeBtn.length === 0) {
                $('<button type="button" id="complete-quotation-btn" class="btn btn-success"><i class="fas fa-check-circle me-1"></i> Complete Quotation</button>')
                  .appendTo(saleForm.find(".mt-4.d-flex"))
                  .data("url", completeUrl)
                  .prop("disabled", false)
                  .removeClass("disabled-button")
                  .on("click", function(event) {
                    event.preventDefault();
                    const url = $(this).data("url");
                    if (!url) return;
                    $.post(url, saleForm.serialize(), function(response) {
                      console.log("Complete response:", response);
                      if (response.error) {
                        alert("❌ " + response.error);
                        return;
                      }
                      alert("✅ Котировка завершена!");
                      window.location.href = "/reports/quotations/";
                    }).fail(function(xhr) {
                      console.error("Complete error:", xhr.responseText);
                      alert("❌ Ошибка завершения котировки: " + (xhr.responseJSON?.error || xhr.responseText));
                    });
                  });
              } else {
                completeBtn.data("url", completeUrl).prop("disabled", false).removeClass("disabled-button");
              }
            }
          }

          // Очистка полей формы, кроме клиента
          $("#product_input").val("");
          $("#product_id").val("");
          $("#invoice_input").val("").prop("disabled", true);
          $("#import_id").val("");
          $("#invoice").val("");
          $("#sell_price").val("");
          $("#qty").val("1");
          $("#vat_rate").val("5");
          $("#trade_margin").val("1.0");
          $("#crude_price").val("");
          $("#trade_discount").val("0");
          $("#discount_amount").val("");
          $("#agent_commission_rate").val("0");
          $("#commission_amount").val("");
          $("#final_sell_price_without_vat").val("");
          $("#vat_amount").val("");
          $("#customer_price").val("");
          $("#profit").val("");
          $("#total_amount").val("");
        } else {
          console.warn("No quotation_sales in response or length is 0");
          quotationTableBody.append('<tr><td colspan="7" class="text-center text-muted">No items added to this quotation yet.</td></tr>');
        }
      } else {
        console.error("Table not found, cannot update");
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
      console.log("Complete response:", response);
      if (response.error) {
        alert("❌ " + response.error);
        return;
      }
      alert("✅ Котировка завершена!");
      window.location.href = "/reports/quotations/";
    }).fail(function(xhr) {
      console.error("Complete error:", xhr.responseText);
      alert("❌ Ошибка завершения котировки: " + (xhr.responseJSON?.error || xhr.responseText));
    });
  });

  if (productInput.length) {
    console.log("Initializing product autocomplete");
    initProductAutocomplete({
      inputId: "#product_input",
      hiddenId: "#product_id",
      invoiceInputId: "#invoice_input",
      importId: "#import_id",
      invoiceDisplayId: "#invoice",
      onPriceUpdate: calculatePricing,
      urls: window.urls
    });
    console.log("Product autocomplete initialized");
    $(productInput).on("autocompleteopen", function() {
      console.log("Product autocomplete opened");
    }).on("autocompleteselect", function(event, ui) {
      console.log("Product selected:", ui.item.label);
    });
  } else {
    console.error("Product input not found");
  }

  if (customerInput.length && !customerInput.prop("disabled")) {
    console.log("Initializing customer autocomplete");
    initCustomerAutocomplete({ inputId: "#customer_input", hiddenId: "#customer_id" });
    console.log("Customer autocomplete initialized");
    $(customerInput).on("autocompleteopen", function() {
      console.log("Customer autocomplete opened");
    }).on("autocompleteselect", function(event, ui) {
      console.log("Customer selected:", ui.item.label);
    });
  } else {
    console.warn("Customer input not found or disabled");
  }
}

export default initInvoicePage;