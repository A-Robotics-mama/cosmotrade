// static/js/search/dynamic_search_base.js
export function initDynamicSearchBase({ inputId, tableId, url, searchParam = 'name' }) {
  const input = $(inputId);
  const table = $(tableId);

  function performSearch() {
    const searchValue = input.val();
    const data = {};
    data[searchParam] = searchValue;

    $.ajax({
      url: url,
      type: 'GET',
      data: data,
      success: function (response) {
        table.html(response.html);
      },
      error: function () {
        table.html('<p class="text-center text-muted">Ошибка загрузки данных.</p>');
      }
    });
  }

  let typingTimer;
  const typingDelay = 300;

  input.on('input', function () {
    clearTimeout(typingTimer);
    typingTimer = setTimeout(performSearch, typingDelay);
  });

  input.on('keypress', function (e) {
    if (e.which === 13) {
      e.preventDefault();
      clearTimeout(typingTimer);
      performSearch();
    }
  });
}


// static/js/search/dynamic_customer_search.js
import { initDynamicSearchBase } from "./dynamic_search_base.js";

export function initCustomerSearch({ inputId = "#customer_search", tableId = "#customer_table", url = "/customers/search/" }) {
  initDynamicSearchBase({
    inputId,
    tableId,
    url,
    searchParam: "query"
  });
}


// static/js/search/dynamic_product_search.js
import { initDynamicSearchBase } from "./dynamic_search_base.js";

export function initProductSearch({ inputId = "#product_search", tableId = "#product_table", url = "/products/search/" }) {
  initDynamicSearchBase({
    inputId,
    tableId,
    url,
    searchParam: "name"
  });
}
