// SQL importer builder — list, CRUD, and DuckDB preview.
//
// Tabulator runs in client mode over window.__IMPORTERS__, which the page route
// embeds. Every mutation and preview is a JSON or FormData call to
// /api/importers; the list is updated in place with no page reload. No htmx.
(function () {
  "use strict";

  var container = document.getElementById("importers-table");
  if (!container) return;

  var modal = document.getElementById("importer-modal");
  var modalTitle = document.getElementById("importer-modal-title");
  var nameInput = document.getElementById("importer-name");
  var sqlInput = document.getElementById("importer-sql");
  var fileInput = document.getElementById("importer-file");
  var runButton = document.getElementById("importer-run");
  var saveButton = document.getElementById("importer-save");
  var closeButton = document.getElementById("importer-close");
  var newButton = document.getElementById("importer-new");
  var errorBox = document.getElementById("importer-error");
  var summaryBox = document.getElementById("importer-summary");
  var rawSchemaBox = document.getElementById("importer-raw-schema");
  var previewBox = document.getElementById("importer-preview");

  var editingId = null;
  var sampleFile = null;
  // Message from the most recent Run, kept so Save can warn about a draft.
  var lastRunError = null;
  var table = null;

  // === DOM helpers ===

  function importers() {
    return window.__IMPORTERS__ || [];
  }

  function clearNode(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function makeEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = text;
    return el;
  }

  function showToast(message, type) {
    var toastContainer = document.getElementById("toast-container");
    if (!toastContainer) return;
    var alert = makeEl("div", "alert alert-" + (type || "error"));
    alert.appendChild(makeEl("span", null, message));
    toastContainer.appendChild(alert);
    if (typeof window.autoToast === "function") window.autoToast(alert);
  }

  function showError(message) {
    clearNode(errorBox);
    var alert = makeEl("div", "alert alert-error alert-sm");
    alert.appendChild(makeEl("span", null, message));
    errorBox.appendChild(alert);
  }

  function clearError() {
    clearNode(errorBox);
  }

  function setBusy(busy) {
    if (runButton) runButton.disabled = busy;
    if (saveButton) saveButton.disabled = busy;
  }

  function readJson(response) {
    return response
      .json()
      .catch(function () {
        return {};
      })
      .then(function (body) {
        if (!response.ok) {
          var detail =
            body && body.detail
              ? body.detail
              : "Request failed (" + response.status + ")";
          throw new Error(detail);
        }
        return body;
      });
  }

  // === List ===

  function sortImporters() {
    window.__IMPORTERS__.sort(function (a, b) {
      return a.name.localeCompare(b.name);
    });
  }

  function upsert(item) {
    var list = importers();
    var replaced = false;
    for (var i = 0; i < list.length; i++) {
      if (list[i].id === item.id) {
        list[i] = item;
        replaced = true;
        break;
      }
    }
    if (!replaced) list.push(item);
    sortImporters();
  }

  function rebuild() {
    table.setData(importers().slice());
  }

  function formatUpdated(value) {
    if (!value) return "—";
    var parsed = new Date(value);
    if (isNaN(parsed.getTime())) return value;
    return parsed.toLocaleString();
  }

  table = new Tabulator(container, {
    data: importers().slice(),
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No importers yet",
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
        headerFilterParams: {
          elementAttributes: { class: "input input-xs" },
        },
        headerFilterPlaceholder: "Search...",
      },
      {
        title: "Updated",
        field: "updated_at",
        sorter: "string",
        width: 200,
        formatter: function (cell) {
          return formatUpdated(cell.getValue());
        },
      },
      {
        title: "",
        field: "_actions",
        width: 150,
        hozAlign: "right",
        headerSort: false,
        download: false,
        formatter: function () {
          return (
            '<button type="button" class="btn btn-ghost btn-xs" data-action="edit">Edit</button>' +
            '<button type="button" class="btn btn-ghost btn-xs text-error" data-action="delete">Delete</button>'
          );
        },
      },
    ],
  });

  table.on("renderComplete", function () {
    if (window.lucide) window.lucide.createIcons();
  });

  table.on("cellClick", function (event, cell) {
    if (cell.getField() !== "_actions") return;
    var target = event.target.closest("[data-action]");
    if (!target) return;
    var row = cell.getRow().getData();
    if (target.getAttribute("data-action") === "edit") {
      openEdit(row);
    } else {
      deleteImporter(row);
    }
  });

  // === Modal ===

  function resetPreview() {
    clearError();
    clearNode(summaryBox);
    clearNode(rawSchemaBox);
    clearNode(previewBox);
  }

  function openNew() {
    editingId = null;
    sampleFile = null;
    lastRunError = null;
    if (modalTitle) modalTitle.textContent = "New Importer";
    nameInput.value = "";
    sqlInput.value = "";
    fileInput.value = "";
    resetPreview();
    modal.showModal();
  }

  function openEdit(row) {
    editingId = row.id;
    // Samples are never persisted (decision 8): clearing forces a re-pick.
    sampleFile = null;
    lastRunError = null;
    if (modalTitle) modalTitle.textContent = "Edit Importer";
    nameInput.value = row.name;
    sqlInput.value = row.sql;
    fileInput.value = "";
    resetPreview();
    summaryBox.textContent = "Pick a sample CSV before running.";
    modal.showModal();
  }

  function renderRawSchema(columns) {
    if (!columns || !columns.length) return;
    var schemaTable = makeEl("table", "table table-sm table-zebra");
    var thead = makeEl("thead");
    var headRow = makeEl("tr");
    headRow.appendChild(makeEl("th", null, "Raw column"));
    headRow.appendChild(makeEl("th", null, "Sniffed type"));
    thead.appendChild(headRow);
    schemaTable.appendChild(thead);

    var tbody = makeEl("tbody");
    columns.forEach(function (col) {
      var row = makeEl("tr");
      row.appendChild(makeEl("td", "font-mono text-xs", col.name));
      row.appendChild(makeEl("td", "text-xs", col.type));
      tbody.appendChild(row);
    });
    schemaTable.appendChild(tbody);
    rawSchemaBox.appendChild(schemaTable);
  }

  function formatAmount(cents) {
    if (cents === null || cents === undefined) return "—";
    return (cents / 100).toFixed(2);
  }

  function renderRows(rows) {
    if (!rows.length) {
      previewBox.appendChild(
        makeEl("div", "text-sm text-base-content/60", "No rows returned.")
      );
      return;
    }

    var previewTable = makeEl("table", "table table-zebra table-sm");
    var thead = makeEl("thead");
    var headRow = makeEl("tr");
    ["Date", "Amount", "Description"].forEach(function (title) {
      headRow.appendChild(makeEl("th", null, title));
    });
    thead.appendChild(headRow);
    previewTable.appendChild(thead);

    var tbody = makeEl("tbody");
    rows.forEach(function (row) {
      var tr = makeEl("tr");
      tr.appendChild(makeEl("td", null, row.date));
      tr.appendChild(makeEl("td", "text-right font-mono", formatAmount(row.amount_cents)));
      tr.appendChild(makeEl("td", null, row.description));
      tbody.appendChild(tr);
    });
    previewTable.appendChild(tbody);
    previewBox.appendChild(previewTable);
  }

  function renderPreview(payload) {
    clearError();
    clearNode(summaryBox);
    clearNode(rawSchemaBox);
    clearNode(previewBox);

    if (payload.error) {
      lastRunError = payload.error.stage + ": " + payload.error.message;
      showError(lastRunError);
      return;
    }

    lastRunError = null;
    renderRawSchema(payload.raw_columns);
    renderRows(payload.rows || []);

    var total = payload.total_rows || 0;
    var summary = total + (total === 1 ? " row validated" : " rows validated");
    if (payload.truncated) summary += " — showing first " + (payload.rows || []).length;
    summaryBox.textContent = summary;
  }

  function run() {
    clearError();
    if (!sampleFile) {
      lastRunError = "Pick a sample CSV before running.";
      showError(lastRunError);
      return;
    }
    if (!sqlInput.value.trim()) {
      lastRunError = "Write a SQL SELECT before running.";
      showError(lastRunError);
      return;
    }

    var form = new FormData();
    form.append("file", sampleFile, sampleFile.name);
    form.append("sql", sqlInput.value);

    setBusy(true);
    fetch("/api/importers/preview", { method: "POST", body: form })
      .then(readJson)
      .then(function (payload) {
        renderPreview(payload);
      })
      .catch(function (error) {
        lastRunError = error.message;
        showError(error.message);
      })
      .finally(function () {
        setBusy(false);
      });
  }

  function save() {
    clearError();
    var name = nameInput.value.trim();
    if (!name) {
      showError("Name is required.");
      return;
    }

    var creating = editingId === null;
    var url = creating ? "/api/importers" : "/api/importers/" + editingId;
    setBusy(true);
    fetch(url, {
      method: creating ? "POST" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: name, sql: sqlInput.value }),
    })
      .then(readJson)
      .then(function (item) {
        upsert(item);
        rebuild();
        modal.close();
        if (lastRunError) {
          showToast(
            "Saved as draft — the last Run errored. " + lastRunError,
            "warning"
          );
        } else {
          showToast("Importer saved.", "success");
        }
      })
      .catch(function (error) {
        // Surfaces the 409 duplicate-name detail from the API.
        showError(error.message);
      })
      .finally(function () {
        setBusy(false);
      });
  }

  function deleteImporter(row) {
    fetch("/api/importers/" + row.id, { method: "DELETE" })
      .then(function (response) {
        if (!response.ok) return readJson(response);
        return null;
      })
      .then(function () {
        window.__IMPORTERS__ = importers().filter(function (item) {
          return item.id !== row.id;
        });
        rebuild();
        showToast("Importer deleted.", "success");
      })
      .catch(function (error) {
        showToast(error.message, "error");
      });
  }

  // === Wiring ===

  if (newButton) newButton.addEventListener("click", openNew);
  if (closeButton) {
    closeButton.addEventListener("click", function () {
      modal.close();
    });
  }
  if (runButton) runButton.addEventListener("click", run);
  if (saveButton) saveButton.addEventListener("click", save);
  if (fileInput) {
    fileInput.addEventListener("change", function () {
      sampleFile =
        fileInput.files && fileInput.files.length ? fileInput.files[0] : null;
    });
  }
})();
