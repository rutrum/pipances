// SQL importer list — Tabulator over window.__IMPORTERS__ and delete.
//
// Tabulator runs in client mode over window.__IMPORTERS__, which the page route
// embeds. Delete is a JSON call to /api/importers; the list is updated in place
// with no page reload. The builder is a separate page and script. No htmx.
(function () {
  "use strict";

  var container = document.getElementById("importers-table");
  if (!container) return;

  var table = null;

  // === DOM helpers ===

  function importers() {
    return window.__IMPORTERS__ || [];
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
        formatter: function (cell) {
          var id = cell.getRow().getData().id;
          return (
            '<a href="/data/importers/' +
            id +
            '/edit" class="btn btn-ghost btn-xs">Edit</a>' +
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
    if (target.getAttribute("data-action") === "delete") {
      deleteImporter(row);
    }
  });

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
})();
