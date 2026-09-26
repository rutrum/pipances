// SQL importer builder — create/edit page with staged UX and DuckDB preview.
//
// The page route embeds window.__IMPORTER__ (an importer object in edit mode,
// null in create mode). Picking a sample immediately previews `SELECT * FROM
// raw`, then reveals the SQL editor. SQL edits re-run after a debounce; Run
// forces an immediate run. The result grid stays visible on parse/query errors
// (marked stale); on a SQL error the result grid is replaced while a warning
// shows. Save validates first, then persists (draft save allowed) and navigates
// back to the list with a toast. No htmx (locked decision 12).
(function () {
  "use strict";

  var sqlInput = document.getElementById("importer-sql");
  if (!sqlInput) return;

  var importer = window.__IMPORTER__ || null;
  var nameInput = document.getElementById("importer-name");
  var fileInput = document.getElementById("importer-file");
  var runButton = document.getElementById("importer-run");
  var saveButton = document.getElementById("importer-save");
  var editor = document.getElementById("importer-editor");
  var errorBox = document.getElementById("importer-error");
  var summaryBox = document.getElementById("importer-summary");
  var rawSchemaBox = document.getElementById("importer-raw-schema");
  var previewBox = document.getElementById("importer-preview");

  var editingId = importer ? importer.id : null;
  var sampleFile = null;
  var editorRevealed = false;
  var hasGrid = false;
  // Message from the most recent Run, kept so Save can warn about a draft.
  var lastRunError = null;
  var debounceTimer = null;
  var requestToken = 0;

  // Name is always visible. SQL is prefilled in edit mode so a draft save
  // without a fresh sample never wipes the stored query.
  if (importer) {
    nameInput.value = importer.name;
    sqlInput.value = importer.sql;
  }

  // === DOM helpers ===

  function clearNode(node) {
    while (node.firstChild) node.removeChild(node.firstChild);
  }

  function makeEl(tag, className, text) {
    var el = document.createElement(tag);
    if (className) el.className = className;
    if (text !== undefined && text !== null) el.textContent = text;
    return el;
  }

  function showError(message, type) {
    clearNode(errorBox);
    var variant = type === "warning" ? "alert-warning" : "alert-error";
    var alert = makeEl("div", "alert " + variant + " alert-sm");
    alert.appendChild(makeEl("span", null, message));
    errorBox.appendChild(alert);
  }

  function clearError() {
    clearNode(errorBox);
  }

  function markStale(stale) {
    if (stale) {
      previewBox.classList.add("border-2", "border-warning", "rounded");
    } else {
      previewBox.classList.remove("border-2", "border-warning", "rounded");
    }
  }

  function setBusy(busy) {
    runButton.disabled = busy;
    saveButton.disabled = busy;
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

  // === Rendering ===

  function renderRawSchema(columns) {
    clearNode(rawSchemaBox);
    if (!columns || !columns.length) return;
    var table = makeEl("table", "table table-sm table-zebra");
    var thead = makeEl("thead");
    var headRow = makeEl("tr");
    headRow.appendChild(makeEl("th", null, "Raw column"));
    headRow.appendChild(makeEl("th", null, "Sniffed type"));
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = makeEl("tbody");
    columns.forEach(function (col) {
      var row = makeEl("tr");
      row.appendChild(makeEl("td", "font-mono text-xs", col.name));
      row.appendChild(makeEl("td", "text-xs", col.type));
      tbody.appendChild(row);
    });
    table.appendChild(tbody);
    rawSchemaBox.appendChild(table);
  }

  function renderResultGrid(columns, rows) {
    clearNode(previewBox);
    if (!columns || !columns.length) return;

    var table = makeEl("table", "table table-zebra table-sm");
    var thead = makeEl("thead");
    var headRow = makeEl("tr");
    columns.forEach(function (col) {
      headRow.appendChild(makeEl("th", "font-mono text-xs", col.name));
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    var tbody = makeEl("tbody");
    if (!rows.length) {
      var empty = makeEl("tr");
      var cell = makeEl("td", "text-sm text-base-content/60", "No rows returned.");
      cell.colSpan = columns.length;
      empty.appendChild(cell);
      tbody.appendChild(empty);
    } else {
      rows.forEach(function (rowValues) {
        var tr = makeEl("tr");
        rowValues.forEach(function (value) {
          tr.appendChild(
            makeEl(
              "td",
              "font-mono text-xs",
              value === null || value === undefined ? "—" : String(value)
            )
          );
        });
        tbody.appendChild(tr);
      });
    }
    table.appendChild(tbody);
    previewBox.appendChild(table);
  }

  function renderPreview(payload) {
    clearError();

    var resultColumns = payload.result_columns || [];
    var resultRows = payload.result_rows || [];
    var executed = resultColumns.length > 0;

    if (executed) {
      renderResultGrid(resultColumns, resultRows);
      hasGrid = true;
      markStale(false);
    }

    if (payload.raw_columns && payload.raw_columns.length) {
      renderRawSchema(payload.raw_columns);
    }

    if (payload.error) {
      lastRunError = payload.error.stage + ": " + payload.error.message;
      clearNode(summaryBox);
      if (payload.error.stage === "validate") {
        // The query ran; the grid above is fresh. Soft warning only.
        showError(lastRunError, "warning");
      } else {
        // parse/query: no grid for this run. Keep the last good one, tint it.
        if (hasGrid) markStale(true);
        showError(lastRunError, "error");
      }
      return;
    }

    lastRunError = null;
    markStale(false);
    var total = payload.total_rows || 0;
    var summary = total + (total === 1 ? " row validated" : " rows validated");
    if (payload.truncated) summary += " — showing first " + resultRows.length;
    summaryBox.textContent = summary;
  }

  // === Preview requests ===

  function previewSql(sql) {
    var form = new FormData();
    form.append("file", sampleFile, sampleFile.name);
    form.append("sql", sql);

    var token = ++requestToken;
    setBusy(true);
    return fetch("/api/importers/preview", { method: "POST", body: form })
      .then(readJson)
      .then(function (payload) {
        if (token !== requestToken) return false;
        renderPreview(payload);
        return true;
      })
      .catch(function (error) {
        if (token !== requestToken) return false;
        lastRunError = error.message;
        showError(error.message, "error");
        return false;
      })
      .finally(function () {
        if (token === requestToken) setBusy(false);
      });
  }

  function run() {
    if (!sampleFile) {
      lastRunError = "Pick a sample CSV before running.";
      showError(lastRunError, "error");
      return Promise.resolve(false);
    }
    if (!sqlInput.value.trim()) {
      lastRunError = "Write a SQL SELECT before running.";
      showError(lastRunError, "error");
      return Promise.resolve(false);
    }
    return previewSql(sqlInput.value);
  }

  function scheduleRun() {
    if (!sampleFile) return;
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(run, 500);
  }

  // === Sample selection (staged reveal) ===

  function onSampleSelected() {
    sampleFile =
      fileInput.files && fileInput.files.length ? fileInput.files[0] : null;
    if (!sampleFile) {
      editor.hidden = true;
      editorRevealed = false;
      return;
    }

    if (!editorRevealed) {
      // Show the raw shape first, then reveal the editor.
      previewSql("SELECT * FROM raw").then(function () {
        editor.hidden = false;
        editorRevealed = true;
        if (importer) {
          // SQL is already prefilled from the stored importer: preview it.
          run();
        } else {
          sqlInput.value = "SELECT * FROM raw";
        }
      });
      return;
    }

    run();
  }

  // === Save ===

  function persist() {
    var creating = editingId === null;
    var url = creating ? "/api/importers" : "/api/importers/" + editingId;
    setBusy(true);
    fetch(url, {
      method: creating ? "POST" : "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ name: nameInput.value.trim(), sql: sqlInput.value }),
    })
      .then(readJson)
      .then(function () {
        var toast = lastRunError ? "importer_draft" : "importer_saved";
        window.location.href = "/data/importers?toast=" + toast;
      })
      .catch(function (error) {
        // Surfaces the 409 duplicate-name detail from the API.
        showError(error.message, "error");
        setBusy(false);
      });
  }

  function save() {
    clearError();
    if (!nameInput.value.trim()) {
      showError("Name is required.", "error");
      return;
    }
    clearTimeout(debounceTimer);
    if (sampleFile) {
      run().then(persist);
    } else {
      // No sample means the SQL could not be validated: a draft save.
      lastRunError = "No sample CSV chosen; saved as a draft.";
      persist();
    }
  }

  // === Wiring ===

  runButton.addEventListener("click", function () {
    clearTimeout(debounceTimer);
    run();
  });
  saveButton.addEventListener("click", save);
  fileInput.addEventListener("change", onSampleSelected);
  sqlInput.addEventListener("input", scheduleRun);
})();
