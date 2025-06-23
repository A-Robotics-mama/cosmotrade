// static/js/main.js

import { initRetailPage } from "./pages/sale_retail.js";
import { initInvoicePage } from "./pages/sale_invoice.js";

const path = window.location.pathname;

if (path.includes("/sales/retail")) {
  initRetailPage();
} else if (path.includes("/sales/invoice")) {
  initInvoicePage();
}
