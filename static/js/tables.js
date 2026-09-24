// Shared factory for the read-only transactions table — Tabulator in fully
// remote mode. Sorting, filtering and pagination are handled by
// POST /api/transactions/table; callers only supply the AJAX params and any
// initial header-filter seed.
window.PipancesTables = window.PipancesTables || {};

window.PipancesTables.transactions = function (container, options) {
  options = options || {};

  // Give Tabulator's built-in header filter inputs real daisyUI `input` styling.
  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  return new Tabulator(container, {
    ajaxURL: options.ajaxURL || "/api/transactions/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    ajaxParams: options.ajaxParams || function () {
      return {};
    },
    initialHeaderFilter: options.initialHeaderFilter || [],
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No transactions found",
    pagination: true,
    paginationMode: "remote",
    paginationSize: 25,
    paginationSizeSelector: [25, 50, 100],
    paginationCounter: "rows",
    sortMode: "remote",
    filterMode: "remote",
    initialSort: [{ column: "date", dir: "desc" }],
    columns: [
      {
        title: "Date",
        field: "date",
        sorter: "string",
        width: 130,
      },
      {
        title: "Amount",
        field: "amount",
        sorter: "number",
        hozAlign: "right",
        width: 130,
        formatter: "money",
        formatterParams: { precision: 2, symbol: "$" },
      },
      {
        title: "Description",
        field: "description",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Search...",
      },
      {
        title: "Category",
        field: "category.name",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Filter...",
      },
      {
        title: "External",
        field: "external_account.name",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Filter...",
      },
      {
        title: "Internal",
        field: "internal_account.name",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Filter...",
      },
    ],
  });
};
