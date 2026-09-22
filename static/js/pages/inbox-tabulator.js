// Inbox Tabulator — a second inbox implementation built on Tabulator.
//
// Phase 4: read-only remote table, inline editing, per-row approve, the
// top-level commit flow, and range clipboard paste. The edit modal arrives
// later. Data comes from POST /api/inbox/table; inline edits and approval
// PATCH /api/inbox/transactions/{id}; range paste PATCHes the batch endpoint;
// commit uses /api/inbox/commit*.
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

  // Build a nested update object from a flat Tabulator field path so that
  // row.updateData can diff it against the existing nested row data. Passing
  // a flat key straight through (as Tabulator's built-in range action does)
  // leaves a junk property on the row instead of updating the nested object.
  function nestedUpdate(field, value) {
    var parts = field.split(".");
    if (parts.length === 1) {
      var flat = {};
      flat[field] = value;
      return flat;
    }
    var root = {};
    var cursor = root;
    for (var i = 0; i < parts.length; i++) {
      if (i === parts.length - 1) cursor[parts[i]] = value;
      else cursor = cursor[parts[i]] = {};
    }
    return root;
  }

  function mergeUpdate(target, source) {
    Object.keys(source).forEach(function (key) {
      var value = source[key];
      if (value && typeof value === "object" && !Array.isArray(value)) {
        target[key] = mergeUpdate(target[key] || {}, value);
      } else {
        target[key] = value;
      }
    });
    return target;
  }

  // Custom clipboard paste action. Tabulator's built-in range action uses
  // row.updateData with flat field keys and never fires cellEdited, so it
  // cannot persist anything. This action mirrors the built-in range targeting
  // (active rows, start/end bounds, modulo cycling), filters to the editable
  // allowlist, applies the changes locally, then sends one all-or-nothing
  // batch PATCH and reconciles from the response.
  function rangePasteAction(parsedRows) {
    var table = this.table;
    var selectRange = table.modules.selectRange;
    var activeRange = selectRange && selectRange.activeRange;
    if (!activeRange || !parsedRows.length) return [];

    var bounds = activeRange.getBounds();
    var start = bounds.start;
    if (!start) return [];

    var allRows = table.rowManager.activeRows.slice();
    var startIndex = allRows.indexOf(start.row);
    if (startIndex < 0) return [];

    // A single-cell range expands downward to fit the pasted rows; a larger
    // range is filled by cycling the pasted rows with modulo.
    var singleCell = bounds.start === bounds.end;
    var rowCount = singleCell
      ? parsedRows.length
      : allRows.indexOf(bounds.end.row) - startIndex + 1;
    var targets = allRows.slice(startIndex, startIndex + rowCount);
    if (!targets.length) return [];

    var flatUpdates = [];
    var nestedUpdates = [];
    parsedRows.forEach(function (parsed) {
      var flat = {};
      var nested = {};
      Object.keys(parsed).forEach(function (field) {
        if (!Object.prototype.hasOwnProperty.call(EDITABLE_FIELDS, field)) return;
        var value = parsed[field];
        flat[field] = value;
        mergeUpdate(nested, nestedUpdate(field, value));
      });
      flatUpdates.push(flat);
      nestedUpdates.push(nested);
    });

    var hasEditable = flatUpdates.some(function (flat) {
      return Object.keys(flat).length > 0;
    });
    if (!hasEditable) {
      editors.showToast("Nothing in the pasted range is editable.", "warning");
      return [];
    }

    var batch = [];
    var seen = {};
    table.blockRedraw();
    try {
      targets.forEach(function (row, index) {
        var flat = flatUpdates[index % flatUpdates.length];
        if (!Object.keys(flat).length) return;
        var rowId = row.getData().id;
        row.updateData(nestedUpdates[index % nestedUpdates.length]);
        if (seen[rowId]) return;
        seen[rowId] = true;
        var body = { id: rowId };
        Object.keys(flat).forEach(function (field) {
          var value = flat[field];
          body[EDITABLE_FIELDS[field]] =
            value === undefined || value === null ? "" : value;
        });
        batch.push(body);
      });
    } finally {
      table.restoreRedraw();
    }

    if (!batch.length) return targets;

    fetch("/api/inbox/transactions/batch", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ updates: batch }),
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(
            function (body) {
              throw new Error(body.detail || "Paste failed");
            },
            function () {
              throw new Error("Paste failed");
            }
          );
        }
        return response.json();
      })
      .then(function (result) {
        var byId = {};
        table.getRows().forEach(function (row) {
          byId[row.getData().id] = row;
        });
        result.data.forEach(function (updated) {
          var row = byId[updated.id];
          if (row) refreshRow(row, updated);
        });
        editors.showToast(
          "Pasted " +
            batch.length +
            (batch.length === 1 ? " row." : " rows."),
          "success"
        );
      })
      .catch(function (error) {
        table.setData();
        editors.showToast(error.message || "Paste failed", "error");
      });

    return targets;
  }

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
    var edit = rowData.marked_for_approval
      ? ""
      : '<button type="button" data-action="edit" ' +
        'class="btn btn-ghost btn-xs">Edit</button>';
    var approve;
    if (rowData.marked_for_approval) {
      approve =
        '<button type="button" data-action="approve" ' +
        'class="btn btn-success btn-xs">Approved</button>';
    } else if (rowData.can_approve) {
      approve =
        '<button type="button" data-action="approve" ' +
        'class="btn btn-outline btn-xs">Approve</button>';
    } else {
      approve =
        '<button type="button" class="btn btn-ghost btn-xs" disabled>Approve</button>';
    }
    return (
      '<div class="flex items-center justify-center gap-1">' +
      edit +
      approve +
      "</div>"
    );
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
    clipboard: true,
    clipboardCopyStyled: false,
    clipboardCopyConfig: { columnHeaders: false, rowHeaders: false },
    clipboardCopyRowRange: "range",
    clipboardPasteParser: "range",
    clipboardPasteAction: rangePasteAction,
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
        cssClass: "txn-actions-cell",
        width: 170,
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
    var row = cell.getRow();
    if (event.target.closest("[data-action='edit']")) {
      if (window.PipancesInboxModal) {
        window.PipancesInboxModal.open(row.getData().id);
      }
      return;
    }
    var button = event.target.closest("[data-action='approve']");
    if (!button) return;
    toggleApprove(row);
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

  // === Retrain ===

  var retrainBtn = document.getElementById("retrain-btn");
  if (retrainBtn) {
    var retrainIdleHtml = retrainBtn.innerHTML;
    retrainBtn.addEventListener("click", function () {
      retrainBtn.disabled = true;
      retrainBtn.innerHTML =
        '<span class="loading loading-spinner loading-sm"></span> Retraining...';
      fetch("/api/inbox/retrain", { method: "POST" })
        .then(function (response) {
          if (!response.ok) {
            throw new Error("Retrain failed");
          }
          return response.json();
        })
        .then(function (result) {
          var count = result.updated_count || 0;
          editors.showToast(
            count
              ? "Retrained model and updated " +
                  count +
                  (count === 1 ? " suggestion." : " suggestions.")
              : "Retrained. No suggestions changed.",
            count ? "success" : "info"
          );
          // Re-fetch the current page in place so the refreshed suggestions
          // appear without losing the sort or pagination position.
          table.replaceData();
        })
        .catch(function () {
          editors.showToast("Retrain failed", "error");
        })
        .finally(function () {
          retrainBtn.disabled = false;
          retrainBtn.innerHTML = retrainIdleHtml;
          if (window.lucide) window.lucide.createIcons();
        });
    });
  }

  // Shared surface for the modal script (and tests).
  window.PipancesInboxTable = table;
  window.PipancesInbox = {
    table: table,
    refreshRowById: function (id, data) {
      var row = table.getRow(id);
      if (row) refreshRow(row, data);
    },
    adjustMarkedCount: function (delta) {
      markedCount += delta;
      renderMarkedCount();
    },
  };
})();
