// Internal accounts table — Tabulator in fully remote mode with inline editing.
// Data comes from POST /api/accounts/table; edits PATCH /api/accounts/{id};
// the add form POSTs /api/accounts.
(function () {
  var container = document.getElementById("accounts-table");
  if (!container) return;

  var editors = window.PipancesEditors;
  var headerFilterParams = {
    elementAttributes: { class: "input input-xs" },
  };
  var KIND_OPTIONS = [
    { value: "checking", text: "Checking" },
    { value: "savings", text: "Savings" },
    { value: "credit_card", text: "Credit Card" },
  ];
  var KIND_LABELS = {
    checking: "Checking",
    savings: "Savings",
    credit_card: "Credit Card",
  };

  var showClosed = false;

  function editUrl(cell) {
    return "/api/accounts/" + cell.getRow().getData().id;
  }

  var table = new Tabulator(container, {
    ajaxURL: "/api/accounts/table",
    ajaxConfig: "POST",
    ajaxContentType: "json",
    ajaxParams: function () {
      return { show_closed: showClosed };
    },
    height: "70vh",
    layout: "fitColumns",
    placeholder: "No accounts yet",
    pagination: true,
    paginationMode: "remote",
    paginationSize: 25,
    paginationSizeSelector: [25, 50, 100],
    paginationCounter: "rows",
    sortMode: "remote",
    filterMode: "remote",
    initialSort: [{ column: "name", dir: "asc" }],
    columns: [
      {
        title: "Name",
        field: "name",
        sorter: "string",
        editor: "input",
        editorParams: {
          elementAttributes: { class: "input input-sm w-full" },
        },
        headerFilter: "input",
        headerFilterParams: headerFilterParams,
        headerFilterPlaceholder: "Search...",
        cellEdited: function (cell) {
          editors.saveCell(cell, { url: editUrl(cell), field: "name" });
        },
      },
      {
        title: "Type",
        field: "kind",
        sorter: "string",
        width: 150,
        editor: editors.tomSelect,
        editorParams: { values: KIND_OPTIONS },
        formatter: function (cell) {
          return KIND_LABELS[cell.getValue()] || cell.getValue();
        },
        cellEdited: function (cell) {
          editors.saveCell(cell, { url: editUrl(cell), field: "kind" });
        },
      },
      {
        title: "Starting Balance",
        field: "starting_balance",
        sorter: "number",
        hozAlign: "right",
        width: 160,
        editor: "number",
        editorParams: {
          step: 0.01,
          elementAttributes: { class: "input input-sm w-full" },
        },
        formatter: "money",
        formatterParams: { precision: 2, symbol: "$" },
        cellEdited: function (cell) {
          editors.saveCell(cell, { url: editUrl(cell), field: "starting_balance" });
        },
      },
      {
        title: "Balance Date",
        field: "balance_date",
        sorter: "string",
        width: 150,
        editor: editors.dateInput,
        formatter: function (cell) {
          return cell.getValue() || "—";
        },
        cellEdited: function (cell) {
          editors.saveCell(cell, { url: editUrl(cell), field: "balance_date" });
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
          var row = cell.getRow().getData();
          var explore =
            '<a class="btn btn-ghost btn-xs" title="View in Explore" ' +
            'href="/explore?internal=' +
            encodeURIComponent(row.name) +
            '"><i data-lucide="compass" class="w-4 h-4"></i></a>';
          var label = row.active ? "Close" : "Reopen";
          var cls = row.active ? "text-warning" : "text-success";
          var toggle =
            '<button type="button" class="btn btn-ghost btn-xs ' +
            cls +
            '" data-action="toggle-active">' +
            label +
            "</button>";
          return explore + toggle;
        },
      },
    ],
    rowFormatter: function (row) {
      row
        .getElement()
        .classList.toggle("opacity-50", row.getData().active === false);
    },
  });

  table.on("renderComplete", function () {
    if (window.lucide) window.lucide.createIcons();
  });

  // Close / reopen an account, then reload so the show-closed filter applies.
  table.on("cellClick", function (event, cell) {
    if (cell.getField() !== "_actions") return;
    var button = event.target.closest("[data-action='toggle-active']");
    if (!button) return;

    var data = cell.getRow().getData();
    fetch(editUrl(cell), {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ active: !data.active }),
    })
      .then(function (response) {
        if (!response.ok) {
          return response.json().then(function (body) {
            throw new Error(body.detail || "Update failed");
          });
        }
        return response.json();
      })
      .then(function () {
        table.setData();
      })
      .catch(function (error) {
        editors.showToast(error.message || "Update failed", "error");
      });
  });

  // Show-closed toggle reloads the table with the new flag.
  var showClosedToggle = document.getElementById("accounts-show-closed");
  if (showClosedToggle) {
    showClosedToggle.addEventListener("change", function (event) {
      showClosed = event.target.checked;
      table.setData();
    });
  }

  // Add-account form: a plain JSON POST, then reload the table.
  var kindSelect = document.getElementById("account-add-kind");
  var kindControl = null;
  if (kindSelect) {
    kindControl = new TomSelect(kindSelect, {
      valueField: "value",
      labelField: "text",
      searchField: "text",
      options: KIND_OPTIONS,
      maxItems: 1,
      create: false,
      placeholder: "Type",
    });
  }

  var addForm = document.getElementById("account-add-form");
  if (addForm) {
    addForm.addEventListener("submit", function (event) {
      event.preventDefault();
      var form = event.target;
      var errorEl = document.getElementById("account-add-error");
      if (errorEl) errorEl.innerHTML = "";

      var payload = {
        name: form.elements["name"].value,
        kind: kindControl
          ? kindControl.getValue()
          : form.elements["kind"].value,
        starting_balance: form.elements["starting_balance"].value
          ? parseFloat(form.elements["starting_balance"].value)
          : 0,
        balance_date: form.elements["balance_date"].value || null,
      };

      fetch("/api/accounts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (response) {
          if (!response.ok) {
            return response.json().then(function (body) {
              throw new Error(body.detail || "Could not add account");
            });
          }
          return response.json();
        })
        .then(function () {
          form.reset();
          if (kindControl) kindControl.clear();
          table.setData();
        })
        .catch(function (error) {
          if (errorEl) {
            errorEl.innerHTML =
              '<div class="alert alert-error alert-sm"><span>' +
              error.message +
              "</span></div>";
          }
        });
    });
  }
})();
