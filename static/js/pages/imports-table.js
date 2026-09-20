// Read-only import history table — Tabulator in fully remote mode.
// Data comes from POST /api/imports/table.
(function () {
  var container = document.getElementById("imports-table");
  if (!container) return;

  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  function nullSafe(value) {
    return value === null || value === undefined ? "--" : value;
  }

  new Tabulator(container, {
    ajaxURL: "/api/imports/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No imports yet",
    pagination: true,
    paginationMode: "remote",
    paginationSize: 25,
    paginationSizeSelector: [25, 50, 100],
    paginationCounter: "rows",
    sortMode: "remote",
    filterMode: "remote",
    initialSort: [{ column: "imported_at", dir: "desc" }],
    columns: [
      {
        title: "Institution",
        field: "institution",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Search...",
      },
      {
        title: "Filename",
        field: "filename",
        sorter: "string",
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Search...",
        formatter: function (cell) {
          return nullSafe(cell.getValue());
        },
      },
      {
        title: "Imported At",
        field: "imported_at",
        sorter: "string",
        width: 180,
      },
      {
        title: "Rows",
        field: "row_count",
        sorter: "number",
        hozAlign: "right",
        width: 100,
        formatter: function (cell) {
          return nullSafe(cell.getValue());
        },
      },
    ],
  });
})();
