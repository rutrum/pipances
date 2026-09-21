// Inbox Tabulator — a second inbox implementation built on Tabulator.
//
// Phase 2: read-only remote table plus inline editing of description,
// category, and external account. Approve/commit, range clipboard and the
// edit modal are added in later phases. Data comes from POST /api/inbox/table;
// edits PATCH /api/inbox/transactions/{id}.
(function () {
  "use strict";

  var root = document.getElementById("inbox-tabulator-root");
  var container = document.getElementById("inbox-tabulator");
  if (!root || !container) return;

  var editors = window.PipancesEditors;
  var pageSize = parseInt(root.dataset.pageSize, 10) || 25;
  var pageSizeOptions = JSON.parse(root.dataset.pageSizeOptions || "[25,50,100]");

  // Column field -> request body field. Range clear-cells can fire for any
  // column, so anything not listed here is treated as read-only.
  var EDITABLE_FIELDS = {
    description: "description",
    "category.name": "category_id",
    "external_account.name": "external_id",
  };

  // Populated asynchronously; Tabulator reads editorParams at edit time so
  // pushing into the same array is enough.
  var categoryOptions = [];
  var externalOptions = [];

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  // Small confidence dot shown next to ML-suggested values.
  function mlDot(rowData, key) {
    var ml = rowData.ml_confidence;
    var confidence = ml && ml[key];
    if (confidence == null) return "";
    var pct = Math.round(confidence * 100);
    return (
      '<span class="status status-info flex-shrink-0" ' +
      'title="ML suggested (' +
      pct +
      "% confidence)" +
      '"></span>'
    );
  }

  function valueFormatter(options) {
    return function (cell) {
      var rowData = cell.getRow().getData();
      var value = cell.getValue();
      var dot = options.mlKey ? mlDot(rowData, options.mlKey) : "";
      var body = value
        ? escapeHtml(value)
        : '<span class="italic text-base-content/40">' +
          options.emptyLabel +
          "</span>";
      return '<div class="flex items-center gap-1">' + dot + body + "</div>";
    };
  }

  function amountFormatter(cell) {
    var value = cell.getValue() || 0;
    var cls = value < 0 ? "text-error" : "text-success";
    var sign = value < 0 ? "-" : "";
    return (
      '<span class="font-mono ' +
      cls +
      '">' +
      sign +
      "$" +
      Math.abs(value).toFixed(2) +
      "</span>"
    );
  }

  function categoryFormatter(cell) {
    var rowData = cell.getRow().getData();
    var value = cell.getValue();
    var dot = mlDot(rowData, "category");
    var body = value
      ? escapeHtml(value)
      : '<span class="italic text-base-content/40">no category</span>';
    var badge = "";
    if (rowData.split_count > 0) {
      badge =
        '<span class="badge badge-ghost badge-sm">' +
        rowData.split_count +
        (rowData.split_count === 1 ? " split" : " splits") +
        "</span>";
    }
    return '<div class="flex items-center gap-1">' + dot + body + badge + "</div>";
  }

  // Clear-cells applies to every cell in a range, including read-only columns.
  // Restore those instead of letting them blank out locally.
  var restoringReadonly = false;
  function restoreReadonlyCell(cell) {
    if (restoringReadonly) return;
    restoringReadonly = true;
    try {
      cell.setValue(cell.getOldValue());
    } finally {
      restoringReadonly = false;
    }
  }

  var table = new Tabulator(container, {
    ajaxURL: "/api/inbox/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    height: "70vh",
    layout: "fitColumns",
    index: "id",
    selectableRows: false,
    placeholder: "All cleaned up! No pending transactions.",
    pagination: true,
    paginationMode: "remote",
    paginationSize: pageSize,
    paginationSizeSelector: pageSizeOptions,
    paginationCounter: "rows",
    sortMode: "remote",
    initialSort: [{ column: "date", dir: "asc" }],
    editTriggerEvent: "dblclick",
    selectableRange: 1,
    selectableRangeColumns: false,
    selectableRangeRows: false,
    selectableRangeClearCells: true,
    selectableRangeClearCellsValue: "",
    columns: [
      {
        title: "Date",
        field: "date",
        sorter: "string",
        width: 115,
      },
      {
        title: "Account",
        field: "internal_account.name",
        sorter: "string",
        width: 160,
      },
      {
        title: "Amount",
        field: "amount",
        sorter: "number",
        hozAlign: "right",
        width: 120,
        formatter: amountFormatter,
      },
      {
        title: "Raw Description",
        field: "raw_description",
        sorter: "string",
        width: 220,
        tooltip: true,
      },
      {
        title: "Description",
        field: "description",
        sorter: "string",
        minWidth: 180,
        editor: "input",
        editorParams: {
          elementAttributes: { class: "input input-sm w-full" },
        },
        formatter: valueFormatter({
          mlKey: "description",
          emptyLabel: "no description",
        }),
      },
      {
        title: "Category",
        field: "category.name",
        sorter: "string",
        minWidth: 160,
        editor: editors.tomSelect,
        editorParams: { values: categoryOptions, create: true },
        formatter: categoryFormatter,
      },
      {
        title: "External",
        field: "external_account.name",
        sorter: "string",
        minWidth: 160,
        editor: editors.tomSelect,
        editorParams: { values: externalOptions, create: true },
        formatter: valueFormatter({
          mlKey: "external",
          emptyLabel: "no external account",
        }),
      },
    ],
    rowFormatter: function (row) {
      row
        .getElement()
        .classList.toggle("txn-approved", !!row.getData().marked_for_approval);
    },
  });

  table.on("cellEdited", function (cell) {
    var bodyField = EDITABLE_FIELDS[cell.getField()];
    if (!bodyField) {
      restoreReadonlyCell(cell);
      return;
    }
    editors.saveCell(cell, {
      url: "/api/inbox/transactions/" + cell.getRow().getData().id,
      field: bodyField,
    });
  });

  table.on("renderComplete", function () {
    if (window.lucide) window.lucide.createIcons();
  });

  function loadOptions(url, target) {
    fetch(url)
      .then(function (response) {
        return response.json();
      })
      .then(function (items) {
        items.forEach(function (item) {
          target.push({ value: item.name, text: item.name });
        });
      })
      .catch(function () {
        editors.showToast("Could not load options", "error");
      });
  }

  loadOptions("/api/categories", categoryOptions);
  loadOptions("/api/external-accounts", externalOptions);

  // Exposed for later phases (approve, clipboard) on the same page.
  window.PipancesInboxTable = table;
})();
