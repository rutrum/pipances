// Data/Tab Transactions — Tabulator in fully remote mode.
// Sorting, filtering and pagination are handled by POST /api/transactions/table.
// The only imperative code here is wiring the page-level date-range control.
(function () {
  var root = document.getElementById("tab-transactions");
  var container = document.getElementById("tab-transactions-table");
  if (!root || !container) return;

  var dateFrom = root.dataset.dateFrom || "";
  var dateTo = root.dataset.dateTo || "";

  // Give Tabulator's built-in header filter inputs real daisyUI `input` styling.
  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  function activatePreset(key) {
    root.querySelectorAll(".date-preset-btn").forEach(function (btn) {
      btn.classList.toggle("btn-active", btn.dataset.preset === key);
    });
    var customRange = document.getElementById("tab-custom-range");
    if (customRange) customRange.classList.toggle("hidden", key !== "custom");
  }

  var table = new Tabulator(container, {
    ajaxURL: "/api/transactions/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    ajaxParams: function () {
      return { date_from: dateFrom, date_to: dateTo };
    },
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

  // Reload without stacking requests: setPage(1) fires the remote request when
  // coming from another page, setData() covers the already-on-page-1 case.
  function reload() {
    if (table.getPage() === 1) {
      table.setData();
    } else {
      table.setPage(1);
    }
  }

  root.querySelectorAll(".date-preset-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.dataset.preset;
      if (key === "custom") {
        activatePreset("custom");
        return;
      }
      dateFrom = btn.dataset.dateFrom || "";
      dateTo = btn.dataset.dateTo || "";
      activatePreset(key);
      reload();
    });
  });

  var applyBtn = document.getElementById("tab-apply-custom");
  if (applyBtn) {
    applyBtn.addEventListener("click", function () {
      dateFrom = document.getElementById("tab-date-from").value || "";
      dateTo = document.getElementById("tab-date-to").value || "";
      activatePreset("custom");
      reload();
    });
  }
})();
