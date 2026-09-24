// Read-only transactions table for Data > Transactions — Tabulator in fully
// remote mode, built from the shared factory (static/js/tables.js).
// The only imperative code here is wiring the page-level date-range control.
(function () {
  var root = document.getElementById("transactions-table-root");
  var container = document.getElementById("transactions-table");
  if (!root || !container) return;

  var dateFrom = root.dataset.dateFrom || "";
  var dateTo = root.dataset.dateTo || "";

  var table = window.PipancesTables.transactions(container, {
    ajaxParams: function () {
      return { date_from: dateFrom, date_to: dateTo };
    },
  });

  function activatePreset(key) {
    root.querySelectorAll(".date-preset-btn").forEach(function (btn) {
      btn.classList.toggle("btn-active", btn.dataset.preset === key);
    });
    var customRange = document.getElementById("transactions-custom-range");
    if (customRange) customRange.classList.toggle("hidden", key !== "custom");
  }

  // Reload without stacking requests: setPage(1) fires the remote request when
  // coming from another page, setData() covers the already-on-page-1 case.
  function reload() {
    if (table.getPage() === 1) {
      table.setData();
    } else {
      table.setPage(1);
    }
  }

  root.querySelectorAll(".date-preset-btn").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var key = btn.dataset.preset;
      if (key === "custom") {
        activatePreset("custom");
        return;
      }
      dateFrom = btn.dataset.dateFrom || "";
      dateTo = btn.dataset.dateTo || "";
      activatePreset(key);
      reload();
    });
  });

  var applyBtn = document.getElementById("transactions-apply-custom");
  if (applyBtn) {
    applyBtn.addEventListener("click", function () {
      dateFrom = document.getElementById("transactions-date-from").value || "";
      dateTo = document.getElementById("transactions-date-to").value || "";
      activatePreset("custom");
      reload();
    });
  }
})();
