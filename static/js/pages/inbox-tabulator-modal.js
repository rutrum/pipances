// Edit modal for the Tabulator inbox.
//
// The modal is independent of the original HTMX inbox modal. It is fetched
// into #edit-modal-container, its scalar fields PATCH the JSON endpoint and
// refresh the Tabulator row in place, and the splits section is reused as-is
// (it drives its own HTMX endpoints). On close the row is refetched so
// split_count and the split badge stay in sync.
(function () {
  "use strict";

  var CONTAINER_ID = "edit-modal-container";

  function table() {
    return window.PipancesInboxTable;
  }

  function inbox() {
    return window.PipancesInbox || {};
  }

  function showToast(message, type) {
    if (window.PipancesEditors) window.PipancesEditors.showToast(message, type);
  }

  // Refresh one Tabulator row from a server payload and reformat it so
  // non-column formatters (can_approve, split_count) update too.
  function refreshRow(id, data) {
    var api = inbox();
    if (typeof api.refreshRowById === "function") {
      api.refreshRowById(id, data);
      return;
    }
    var t = table();
    if (!t) return;
    var row = t.getRow(id);
    if (!row) return;
    row.update(data).then(function () {
      row.reformat();
    });
  }

  function patch(id, body) {
    return fetch("/api/inbox/transactions/" + id, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).then(function (response) {
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
    });
  }

  // Keep the modal's Approve button in step with edits made in the modal.
  function updateApproveButton(dialog, data) {
    var button = dialog.querySelector("[data-modal-approve]");
    if (!button) return;
    var marked = !!data.marked_for_approval;
    button.disabled = !marked && !data.can_approve;
    button.dataset.approveValue = marked ? "false" : "true";
    button.textContent = marked ? "Unapprove" : "Approve";
    button.classList.toggle("btn-warning", marked);
    button.classList.toggle("btn-primary", !marked);
  }

  // === Scalar comboboxes (JSON PATCH, not HTMX) ===

  function initJsonSelects(container) {
    container.querySelectorAll("select.ts-json-select").forEach(function (el) {
      if (el.tomselect) return;
      var modals = el.closest("[data-txn-id]");
      if (!modals) return;
      var id = parseInt(modals.dataset.txnId, 10);
      var field = el.dataset.field;
      var current = (el.querySelector("option[selected]") || {}).value || "";
      var values = JSON.parse(el.dataset.options || "[]").map(function (name) {
        return { value: name, text: name };
      });
      if (
        current &&
        !values.some(function (option) {
          return option.value === current;
        })
      ) {
        values.unshift({ value: current, text: current });
      }

      var committed = current;
      var ts = null;
      ts = new TomSelect(el, {
        valueField: "value",
        labelField: "text",
        searchField: "text",
        create: true,
        maxOptions: 50,
        options: values,
        items: current ? [current] : [],
        dropdownParent: "body",
        onChange: function (value) {
          var next = value || "";
          if (next === committed) return;
          var previous = committed;
          committed = next;
          var body = {};
          body[field] = next;
          patch(id, body)
            .then(function (updated) {
              refreshRow(id, updated);
              var dialog = el.closest("dialog");
              if (dialog) updateApproveButton(dialog, updated);
            })
            .catch(function (error) {
              committed = previous;
              if (ts) ts.setValue(previous, true);
              showToast(error.message || "Update failed", "error");
            });
        },
      });
    });
  }

  // === Approve / unapprove from the modal ===

  function wireApprove(dialog, id) {
    var button = dialog.querySelector("[data-modal-approve]");
    if (!button) return;
    button.addEventListener("click", function () {
      var value = button.dataset.approveValue === "true";
      button.disabled = true;
      patch(id, { marked_for_approval: value })
        .then(function (updated) {
          refreshRow(id, updated);
          var api = inbox();
          if (typeof api.adjustMarkedCount === "function") {
            api.adjustMarkedCount(value ? 1 : -1);
          }
          dialog.close();
        })
        .catch(function (error) {
          button.disabled = false;
          showToast(error.message || "Could not update approval", "error");
        });
    });
  }

  // === Open / close ===

  function closeModal(container) {
    var dialog = container.querySelector("dialog");
    if (dialog && dialog.open) dialog.close();
  }

  function destroyTomSelects(container) {
    container.querySelectorAll("select").forEach(function (el) {
      if (el.tomselect) el.tomselect.destroy();
    });
  }

  function openModal(txnId) {
    var container = document.getElementById(CONTAINER_ID);
    if (!container) return;
    fetch("/inbox-tabulator/transactions/" + txnId + "/edit-modal")
      .then(function (response) {
        if (!response.ok) throw new Error("Could not load transaction");
        return response.text();
      })
      .then(function (html) {
        container.innerHTML = html;
        if (window.htmx) window.htmx.process(container);
        if (typeof window.initTomSelects === "function") {
          window.initTomSelects(container);
        }
        if (window.Alpine && typeof window.Alpine.initTree === "function") {
          window.Alpine.initTree(container);
        }
        initJsonSelects(container);
        if (window.lucide) window.lucide.createIcons();

        var dialog = container.querySelector("dialog");
        if (!dialog) return;
        wireApprove(dialog, txnId);
        dialog.addEventListener(
          "close",
          function () {
            // Splits may have changed the split_count / category, so refetch
            // the row before emptying the container.
            fetch("/api/transactions/" + txnId)
              .then(function (response) {
                return response.ok ? response.json() : null;
              })
              .then(function (data) {
                if (data) refreshRow(txnId, data);
              })
              .finally(function () {
                destroyTomSelects(container);
                container.innerHTML = "";
              });
          },
          { once: true }
        );
        dialog.showModal();
      })
      .catch(function (error) {
        showToast(error.message || "Could not load transaction", "error");
      });
  }

  window.PipancesInboxModal = {
    open: openModal,
    close: function () {
      closeModal(document.getElementById(CONTAINER_ID));
    },
    initJsonSelects: initJsonSelects,
  };
})();
