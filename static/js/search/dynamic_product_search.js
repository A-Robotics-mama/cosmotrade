// static/js/search/dynamic_product_search.js

import { initDynamicSearchBase } from "./dynamic_search_base.js";

export function initProductSearch({ inputId, tableId, url }) {
  initDynamicSearchBase({
    inputId,
    tableId,
    url,
    searchParam: "name" // для продуктов используется параметр 'name'
  });
}
