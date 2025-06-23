// static/js/autocomplete/product_autocomplete.js

export function initProductAutocomplete({
  inputId = "#product_input",
  hiddenId = "#product_id",
  invoiceInputId = "#invoice_input",
  importId = "#import_id",
  invoiceDisplayId = "#invoice",
  urls = window.urls,
  onPriceUpdate = null
} = {}) {
  $(inputId).autocomplete({
    source: function (request, response) {
      $.get(urls.productAutocomplete, { term: request.term }, response)
        .fail(() => alert("Ошибка загрузки списка продуктов."));
    },
    minLength: 1,
    select: function (event, ui) {
      $(inputId).val(ui.item.label);
      $(hiddenId).val(ui.item.id);

      $.get(urls.stockImportsForProduct, { product_id: ui.item.id }, function (data) {
        const invoices = data || [];

        if (invoices.length === 0) {
          $(invoiceInputId).val("").prop("disabled", true);
          return;
        }

        $(invoiceInputId).prop("disabled", false).autocomplete({
          source: invoices,
          minLength: 0,
          select: function (event, ui) {
            $(invoiceInputId).val(ui.item.label);
            $(importId).val(ui.item.value);
            if (invoiceDisplayId) {
              $(invoiceDisplayId).val(ui.item.label.split(" ")[1]);
            }

            $.get(urls.getStockPrice, {
              product_id: $(hiddenId).val(),
              import_id: $(importId).val()
            }, function (priceData) {
              if (!priceData.error) {
                $("#sell_price").val(parseFloat(priceData.stock_price).toFixed(2));
                if (typeof onPriceUpdate === "function") onPriceUpdate();
              } else {
                alert("Ошибка получения цены: " + priceData.error);
              }
            });

            return false;
          }
        });

        // 💡 автооткрытие списка + выбор первого
        setTimeout(() => {
          $(invoiceInputId).focus().trigger({ type: "keydown", keyCode: 40 });
          $(invoiceInputId).autocomplete("search", "");
        }, 100);
      });

      return false;
    }
  });
}
