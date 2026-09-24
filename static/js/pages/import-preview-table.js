// CSV import preview — Tabulator in client mode.
// The parsed rows are serialized server-side into the container's data-rows
// attribute (an attribute, not an inline <script>, because djlint's format_js
// mangles {{ }} inside script tags). The script tag lives inside the preview
// fragment so HTMX re-runs it each time the account-select dedup re-renders
// #csv-preview.
(function () {
  // Deliberately selected by data hook, not id: htmx attribute-settling
  // restores class/style on same-id elements after a swap, which would wipe
  // Tabulator's classes on the dedup re-render of #csv-preview.
  var container = document.querySelector("[data-preview-table]");
  if (!container || container.dataset.initialized === "true") return;
  container.dataset.initialized = "true";

  var rows;
  try {
    rows = JSON.parse(container.dataset.rows || "[]");
  } catch (err) {
    return;
  }
  if (!Array.isArray(rows)) return;

  function money(cell) {
    var cents = cell.getValue() || 0;
    var sign = cents < 0 ? "-" : "";
    return sign + "$" + (Math.abs(cents) / 100).toFixed(2);
  }

  new Tabulator(container, {
    data: rows,
    layout: "fitColumns",
    height: "24rem",
    placeholder: "No rows",
    columns: [
      {
        title: "Date",
        field: "date",
        sorter: "string",
        width: 130,
      },
      {
        title: "Amount",
        field: "amount_cents",
        sorter: "number",
        hozAlign: "right",
        width: 130,
        formatter: money,
      },
      {
        title: "Description",
        field: "description",
        sorter: "string",
      },
    ],
    rowFormatter: function (row) {
      var el = row.getElement();
      var duplicate = row.getData().duplicate === true;
      el.classList.toggle("line-through", duplicate);
      el.classList.toggle("opacity-50", duplicate);
    },
  });
})();
