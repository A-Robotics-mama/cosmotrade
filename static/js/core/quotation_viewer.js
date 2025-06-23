// static/js/core/quotation_viewer.js
export function showQuotationDetails(quotationNumber) {
  console.log("📦 Получение деталей котировки:", quotationNumber);
  $.get(`/reports/quotation/details/${encodeURIComponent(quotationNumber)}/`, function (data) {
    if (data.error) {
      alert(data.error);
      return;
    }

    let html = '<ul>';
    data.items.forEach(item => {
      html += `<li><strong>${item["product__product_name"]}</strong>: Qty ${item.qty}, Total €${parseFloat(item.total_with_vat).toFixed(2)}</li>`;
    });
    html += `<li class="mt-2"><strong>Total Amount:</strong> €${parseFloat(data.total_amount).toFixed(2)}</li></ul>`;

    $('#quotationDetailsBody').html(html);
    $('#quotationDetailsModal').modal('show');
  }).fail(function (xhr) {
    console.error("Ошибка запроса котировки:", xhr.status, xhr.responseText);
    alert('Ошибка загрузки деталей котировки: ' + xhr.responseText);
  });
}