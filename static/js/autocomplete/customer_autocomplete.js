// static/js/autocomplete/customer_autocomplete.js

export function initCustomerAutocomplete({ inputId = "#customer_input", hiddenId = "#customer_id" } = {}) {
  $(inputId).autocomplete({
    source: "/customers/autocomplete/",
    minLength: 1,
    select: function (event, ui) {
      $(hiddenId).val(ui.item.value);
      $(inputId).val(ui.item.label).prop("disabled", true);
      return false;
    }
  });
}
