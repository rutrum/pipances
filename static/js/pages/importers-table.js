// Importers table — Tabulator in client mode.
// The list is small and filesystem-backed, so it is loaded once from
// GET /api/importers and sorted/filtered/paginated in the browser.
(function () {
  var container = document.getElementById("importers-table");
  if (!container) return;

  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  new Tabulator(container, {
    ajaxURL: "/api/importers",
    ajaxConfig: "GET",
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No importers available",
    pagination: true,
    paginationSize: 25,
    paginationSizeSelector: [25, 50, 100],
    paginationCounter: "rows",
    initialSort: [{ column: "name", dir: "asc" }],
    columns: [
      {
        title: "Name",
        field: "name",
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
      },
    ],
  });
})();
