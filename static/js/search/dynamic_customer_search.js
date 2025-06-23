// static/js/search/dynamic_customer_search.js

import { initDynamicSearchBase } from "./dynamic_search_base.js";

export function initCustomerSearch({ inputId, tableId, url }) {
  initDynamicSearchBase({
    inputId,
    tableId,
    url,
    searchParam: "query" // для клиентов используется параметр 'query'
  });
}
