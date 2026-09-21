// Inbox Tabulator — a second inbox implementation built on Tabulator.
//
// Phase 3: read-only remote table, inline editing, per-row approve, and the
// top-level commit flow. Range clipboard and the edit modal arrive later.
// Data comes from POST /api/inbox/table; edits and approval PATCH
// /api/inbox/transactions/{id}; commit uses /api/inbox/commit*.
(function () {
  "use strict";

  var root = document.getElementById("inbox-tabulator-root");
  var container = document.getElementById("inbox-tabulator");
  if (!root || !container) return;

  var editors = window.PipancesEditors;
  var pageSize = parseInt(root.dataset.pageSize, 10) || 25;
  var pageSizeOptions = JSON.parse(root.dataset.pageSizeOptions || "[25,50,100]");
  var markedCount = parseInt(root.dataset.markedCount, 10) || 0;

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

  function actionsFormatter(cell) {
    var rowData = cell.getRow().getData();
    if (rowData.marked_for_approval) {
      return (
        '<button type="button" data-action="approve" ' +
        'class="btn btn-success btn-xs">Approved</button>'
      );
    }
    if (rowData.can_approve) {
      return (
        '<button type="button" data-action="approve" ' +
        'class="btn btn-outline btn-xs">Approve</button>'
      );
    }
    return '<button type="button" class="btn btn-ghost btn-xs" disabled>Approve</button>';
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

  // row.update only re-renders cells bound to changed fields, but the actions
  // cell depends on marked_for_approval. Reformat the row after updating.
  function refreshRow(row, data) {
    return row.update(data).then(function () {
      row.reformat();
      return row;
    });
  }

  function renderBadge(count) {
    var el = document.getElementById("inbox-badge");
    if (!el) return;
    el.innerHTML =
      count > 0
        ? '<span class="badge badge-sm badge-primary">' + count + "</span>"
        : "";
  }

  function renderMarkedCount() {
    var badge = document.getElementById("commit-count-badge");
    if (!badge) return;
    badge.textContent = markedCount;
    badge.classList.toggle("hidden", markedCount <= 0);
  }

  function toggleApprove(row) {
    var data = row.getData();
    var next = !data.marked_for_approval;
    if (next && !data.can_approve) {
      editors.showToast(
        "Description and external account are required to approve.",
        "error"
      );
      return;
    }

    var previous = !!data.marked_for_approval;
    row.update({ marked_for_approval: next }).then(function () {
      row.reformat();
    });
    markedCount += next ? 1 : -1;
    renderMarkedCount();

    fetch("/api/inbox/transactions/" + data.id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ marked_for_approval: next }),
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(
            function (body) {
              throw new Error(body.detail || "Update failed");
            },
            function () {
              throw new Error("Update failed");
            }
          );
        }
        return response.json();
      })
      .then(function (updated) {
        refreshRow(row, updated);
      })
      .catch(function (error) {
        row.update({ marked_for_approval: previous }).then(function () {
          row.reformat();
        });
        markedCount += previous ? 1 : -1;
        renderMarkedCount();
        editors.showToast(error.message || "Could not update approval", "error");
      });
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
      {
        title: "",
        field: "_actions",
        width: 120,
        hozAlign: "center",
        headerSort: false,
        clipboard: false,
        formatter: actionsFormatter,
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
    var row = cell.getRow();
    editors
      .saveCell(cell, {
        url: "/api/inbox/transactions/" + row.getData().id,
        field: bodyField,
      })
      .then(function () {
        // The actions cell depends on can_approve, which row.update does not
        // associate with any column, so re-render the row to enable Approve.
        row.reformat();
      });
  });

  table.on("cellClick", function (event, cell) {
    if (cell.getField() !== "_actions") return;
    var button = event.target.closest("[data-action='approve']");
    if (!button) return;
    toggleApprove(cell.getRow());
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

  // === Commit dialog ===

  var commitDialog = document.getElementById("commit-dialog");
  var commitBtn = document.getElementById("commit-btn");
  var commitConfirmBtn = document.getElementById("commit-confirm-btn");
  var commitCancelBtn = document.getElementById("commit-cancel-btn");

  function renderDialogList(sectionId, listId, items) {
    var section = document.getElementById(sectionId);
    var list = document.getElementById(listId);
    list.innerHTML = "";
    items.forEach(function (item) {
      var li = document.createElement("li");
      li.textContent = item;
      list.appendChild(li);
    });
    section.classList.toggle("hidden", items.length === 0);
  }

  if (commitBtn && commitDialog) {
    commitBtn.addEventListener("click", function () {
      fetch("/api/inbox/commit-summary")
        .then(function (response) {
          return response.json();
        })
        .then(function (summary) {
          if (!summary.count) {
            editors.showToast(
              "Nothing to commit -- no transactions are approved.",
              "warning"
            );
            return;
          }
          document.getElementById("commit-dialog-count").textContent =
            summary.count;
          document.getElementById("commit-dialog-noun").textContent =
            summary.count === 1 ? "transaction" : "transactions";
          renderDialogList(
            "commit-dialog-categories",
            "commit-dialog-categories-list",
            summary.new_categories
          );
          renderDialogList(
            "commit-dialog-externals",
            "commit-dialog-externals-list",
            summary.new_externals
          );
          document
            .getElementById("commit-dialog-none")
            .classList.toggle(
              "hidden",
              summary.new_categories.length > 0 ||
                summary.new_externals.length > 0
            );
          commitDialog.showModal();
        })
        .catch(function () {
          editors.showToast("Could not load commit summary", "error");
        });
    });
  }

  if (commitCancelBtn) {
    commitCancelBtn.addEventListener("click", function () {
      if (commitDialog) commitDialog.close();
    });
  }

  if (commitConfirmBtn) {
    commitConfirmBtn.addEventListener("click", function () {
      commitConfirmBtn.disabled = true;
      fetch("/api/inbox/commit", { method: "POST" })
        .then(function (response) {
          return response.json();
        })
        .then(function (result) {
          if (commitDialog) commitDialog.close();
          markedCount = 0;
          renderMarkedCount();
          renderBadge(result.remaining);
          editors.showToast(
            "Committed " +
              result.committed +
              (result.committed === 1 ? " transaction." : " transactions."),
            "success"
          );
          table.setData();
        })
        .catch(function () {
          editors.showToast("Commit failed", "error");
        })
        .finally(function () {
          commitConfirmBtn.disabled = false;
        });
    });
  }

  renderMarkedCount();

  // Exposed for later phases (clipboard) on the same page.
  window.PipancesInboxTable = table;
})();
