// Read-only external accounts table — Tabulator in fully remote mode.
// Data comes from POST /api/external-accounts/table.
(function () {
  var container = document.getElementById("external-accounts-table");
  if (!container) return;

  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  var table = new Tabulator(container, {
    ajaxURL: "/api/external-accounts/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No external accounts found",
    pagination: true,
    paginationMode: "remote",
    paginationSize: 25,
    paginationSizeSelector: [25, 50, 100],
    paginationCounter: "rows",
    sortMode: "remote",
    filterMode: "remote",
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
        title: "Transactions",
        field: "txn_count",
        sorter: "number",
        hozAlign: "right",
        width: 160,
      },
      {
        title: "",
        field: "_explore",
        width: 80,
        hozAlign: "center",
        headerSort: false,
        download: false,
        formatter: function (cell) {
          var name = cell.getRow().getData().name || "";
          return (
            '<a class="btn btn-ghost btn-xs" title="View in Explore" ' +
            'href="/explore?external=' +
            encodeURIComponent(name) +
            '"><i data-lucide="compass" class="w-4 h-4"></i></a>'
          );
        },
      },
    ],
  });

  // Tabulator renders rows after page load, so re-run lucide on each render.
  table.on("renderComplete", function () {
    if (window.lucide) window.lucide.createIcons();
  });
})();
