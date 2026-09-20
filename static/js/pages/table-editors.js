// Shared Tabulator cell editors and edit-lifecycle helpers.
//
// This is deliberately protocol plumbing only: each table still declares its
// own columns, endpoints, and which fields are editable. Load this before a
// table script that needs it.
(function () {
  "use strict";

  function showToast(message, type) {
    var container = document.getElementById("toast-container");
    if (!container) return;
    var alert = document.createElement("div");
    alert.className = "alert alert-" + (type || "error");
    var span = document.createElement("span");
    span.textContent = message;
    alert.appendChild(span);
    container.appendChild(alert);
    if (typeof window.autoToast === "function") window.autoToast(alert);
  }

  // Tabulator editor backed by Tom Select.
  //
  // editorParams:
  //   values: [{value, text}, ...]   static options
  //   create: bool                   allow creating new values (future use)
  //   valueField / labelField / searchField: option shape overrides
  function tomSelect(cell, onRendered, success, cancel, editorParams) {
    var params = editorParams || {};
    var done = false;
    var ts = null;
    var select = document.createElement("select");
    var initial = cell.getValue();

    function commit(value) {
      if (done) return;
      done = true;
      if (ts) ts.destroy();
      success(value);
    }

    function revert() {
      if (done) return;
      done = true;
      if (ts) ts.destroy();
      cancel();
    }

    onRendered(function () {
      var settings = {
        valueField: params.valueField || "value",
        labelField: params.labelField || "text",
        searchField: params.searchField || "text",
        create: params.create || false,
        maxOptions: params.maxOptions || 200,
        options: params.values || [],
        items: initial ? [initial] : [],
        placeholder: params.placeholder || "",
        dropdownParent: "body",
      };
      // Short enums don't need an inline search box, and Tom Select's input
      // has a wide min-width that wraps the control in narrow table cells.
      if (params.searchable === false) settings.controlInput = null;

      ts = new TomSelect(select, settings);
      ts.wrapper.style.width = "100%";

      ts.on("change", function (value) {
        commit(value);
      });
      // Focus loss without a value change means the user abandoned the edit.
      ts.on("blur", function () {
        revert();
      });
      ts.wrapper.addEventListener("keydown", function (event) {
        if (event.key === "Escape") {
          event.preventDefault();
          event.stopPropagation();
          revert();
        }
      });

      ts.focus();
    });

    return select;
  }

  // Tabulator editor using a native <input type="date">.
  function dateInput(cell, onRendered, success, cancel) {
    var done = false;
    var input = document.createElement("input");
    input.type = "date";
    input.className = "input input-sm w-full";
    input.value = cell.getValue() || "";

    function commit() {
      if (done) return;
      done = true;
      success(input.value || null);
    }

    function revert() {
      if (done) return;
      done = true;
      cancel();
    }

    input.addEventListener("blur", commit);
    input.addEventListener("keydown", function (event) {
      if (event.key === "Enter") commit();
      else if (event.key === "Escape") revert();
    });

    onRendered(function () {
      input.focus();
    });

    return input;
  }

  // Persist a cell edit, then reconcile the row with the server response.
  // On failure, revert the cell and surface the server's detail message.
  //
  // options: { url, method, field, body, successMessage }
  function saveCell(cell, options) {
    var row = cell.getRow();
    var method = options.method || "PATCH";
    var body = options.body;
    if (body === undefined) {
      body = {};
      body[options.field] = cell.getValue();
    }

    return fetch(options.url, {
      method: method,
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(
            function (data) {
              throw new Error(data.detail || "Update failed");
            },
            function () {
              throw new Error("Update failed");
            }
          );
        }
        return response.json();
      })
      .then(function (data) {
        row.update(data);
        if (options.successMessage) showToast(options.successMessage, "success");
      })
      .catch(function (error) {
        cell.restoreOldValue();
        showToast(error.message || "Update failed", "error");
      });
  }

  window.PipancesEditors = {
    tomSelect: tomSelect,
    dateInput: dateInput,
    saveCell: saveCell,
    showToast: showToast,
  };
})();
