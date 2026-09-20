// Categories table — Tabulator in fully remote mode with inline name editing.
// Data comes from POST /api/categories/table; edits PATCH /api/categories/{id}.
(function () {
  var container = document.getElementById("categories-table");
  if (!container) return;

  var editors = window.PipancesEditors;
  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };

  var table = new Tabulator(container, {
    ajaxURL: "/api/categories/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No categories yet",
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
        editor: "input",
        editorParams: {
          elementAttributes: { class: "input input-sm w-full" },
        },
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Search...",
        cellEdited: function (cell) {
          editors.saveCell(cell, {
            url: "/api/categories/" + cell.getRow().getData().id,
            field: "name",
          });
        },
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
            'href="/explore?category=' +
            encodeURIComponent(name) +
            '"><i data-lucide="compass" class="w-4 h-4"></i></a>'
          );
        },
      },
    ],
  });

  table.on("renderComplete", function () {
    if (window.lucide) window.lucide.createIcons();
  });
})();
