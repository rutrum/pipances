// Read-only transactions table for Explore — Tabulator in fully remote mode,
// built from the shared factory (static/js/tables.js).
// Date presets do full-page navigation (server-rendered stats/charts must stay
// in sync), so this script only reads the date/filter seed from the root
// element's data attributes. Query-string name filters seed Tabulator's header
// filters; everything else is Tabulator's own remote sorting/filtering.
(function () {
  var root = document.getElementById("transactions-table-root");
  var container = document.getElementById("transactions-table");
  if (!root || !container) return;

  var dateFrom = root.dataset.dateFrom || "";
  var dateTo = root.dataset.dateTo || "";

  var initialHeaderFilter = [];
  try {
    var seeded = JSON.parse(root.dataset.initialFilter || "{}");
    Object.keys(seeded).forEach(function (field) {
      if (seeded[field]) {
        initialHeaderFilter.push({ field: field, value: seeded[field] });
      }
    });
  } catch (err) {
    // Malformed seed payload: start with no header filters.
  }

  window.PipancesTables.transactions(container, {
    ajaxURL: root.dataset.endpoint || "/api/transactions/table",
    ajaxParams: function () {
      return { date_from: dateFrom, date_to: dateTo };
    },
    initialHeaderFilter: initialHeaderFilter,
  });
})();
