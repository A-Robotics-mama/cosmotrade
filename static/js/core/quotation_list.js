// static/js/core/quotation_list.js
import { showQuotationDetails } from "./quotation_viewer.js";

document.addEventListener('DOMContentLoaded', function () {
  // Автозаполнение клиента
  $("#customer").autocomplete({
    source: function (request, response) {
      $.get('/customers/autocomplete/', { term: request.term }, response)
        .fail(function (xhr) {
          console.error("Autocomplete error:", xhr.status, xhr.responseText);
        });
    },
    select: function (event, ui) {
      $("#customer").val(ui.item.label);
      $("#customer_hidden").val(ui.item.value);
      return false;
    }
  }).autocomplete("instance")._renderItem = function (ul, item) {
    return $("<li>").append("<div>" + item.label + "</div>").appendTo(ul);
  };

  // POST формы (удаление / оплата)
  $("form[method='post']").on('submit', function (e) {
    e.preventDefault();
    const form = $(this);
    const url = form.attr('action');
    $.ajax({
      type: 'POST',
      url: url,
      data: form.serialize(),
      success: function (response) {
        if (response.error) {
          alert("❌ " + response.error);
        } else {
          alert("✅ " + (response.success || "Action completed"));
          location.reload();
        }
      },
      error: function (xhr) {
        alert("❌ Ошибка: " + (xhr.responseJSON?.error || xhr.responseText));
      }
    });
  });

  // Обработчик клика по "Details" в выпадающем меню
  $('.dropdown-item').on('click', function(e) {
    e.preventDefault();
    const quotationNumber = $(this).data('quotation');
    if (quotationNumber && quotationNumber.trim() !== '') {
      showQuotationDetails(quotationNumber);
    } else {
      console.error("Quotation number is invalid or undefined:", quotationNumber);
      alert("Invalid or undefined quotation number");
    }
  });
});