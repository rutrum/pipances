---
name: tabulator
description: Reference for building interactive data tables with Tabulator v6.x. Use whenever writing or reviewing JavaScript that uses new Tabulator(), column definitions, sorting, filtering (including header filters), pagination (local or remote/AJAX), data loading via array/AJAX/import, or any Tabulator API calls. Also triggers for questions about client-side vs server-side table operations, virtual DOM rendering, formatters, editors, row selection, column grouping, tree data, or integrating with backend APIs.
---

# Tabulator v6.x Skill

Interactive table generation JavaScript library.

**Version:** 6.5.0  
**Site:** https://www.tabulator.info  
**GitHub:** https://github.com/tabulator-tables/tabulator

---

## Quickstart

```html
<!-- CDN -->
<link href="https://unpkg.com/tabulator-tables/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://unpkg.com/tabulator-tables/dist/js/tabulator.min.js"></script>

<!-- With a theme (e.g. Bootstrap 5) -->
<link href="https://unpkg.com/tabulator-tables/dist/css/tabulator_bootstrap5.min.css" rel="stylesheet">
```

```js
new Tabulator("#my-table", {
  height: "300px",      // enables virtual DOM for large datasets
  data: tabledata,      // inline array, or use ajaxURL for remote
  layout: "fitColumns", // columns expand to fill width
  columns: [
    { title: "Name", field: "name", sorter: "string" },
    { title: "Age",  field: "age",  sorter: "number", hozAlign: "right" },
  ],
});
```

**Import (ESM / npm):**
```js
import {TabulatorFull as Tabulator} from 'tabulator-tables';
```

**npm:**
```
npm install tabulator-tables --save
```

### Virtual DOM

- Set `height` on the table (CSS, inline, or `height` option) to enable the virtual DOM
- Without a height, all rows are rendered — **very slow** for large datasets
- If the table is hidden when `setData()` is called, call `table.redraw()` when it becomes visible

---

## Column Definition Essentials

```js
columns: [
  {
    title: "Name",           // Header text (required for display columns)
    field: "name",           // Data key (required for data columns); supports dot notation: "user.name"
    sorter: "string",        // Built-in or custom sorter
    headerSort: true,        // Enable click-to-sort (default: true)
    headerFilter: "input",   // Header filter editor type
    formatter: "progress",   // Built-in or custom formatter
    editor: "input",         // Cell editor for inline editing
    hozAlign: "right",       // "left" | "center" | "right"
    vertAlign: "middle",     // "top" | "middle" | "bottom"
    width: 200,              // Column width in px (or % with fitColumns)
    minWidth: 50,
    maxWidth: 500,
    frozen: false,           // Freeze column on scroll
    visible: true,           // Initially visible
    tooltip: true,           // Show cell tooltip on hover
    cssClass: "my-class",    // CSS classes on header + cells
    headerVertical: true,    // Vertical header text
    resizable: true,         // User can resize column edges
    responsive: 0,           // Priority for responsive hiding (lower = hidden first)
  },
]
```

**Column grouping:**
```js
columns: [
  { title: "Name", field: "name" },
  {
    title: "Details",
    columns: [
      { title: "Age",  field: "age" },
      { title: "Dept", field: "dept" },
    ],
  },
]
```

**columnDefaults** — apply options globally:
```js
columnDefaults: { tooltip: true, hozAlign: "center" }
```

**autoColumns** — auto-generate from data:
```js
autoColumns: true,
// Customize generated columns:
autoColumnsDefinitions: (definitions) => {
  definitions.forEach(col => { col.headerFilter = true; });
  return definitions;
},
// Or per-field lookup:
autoColumnsDefinitions: { name: { editor: "input" } }
```

---

## Sorting

**Built-in sorters:** `"string"`, `"number"`, `"alphanum"`, `"boolean"`, `"exists"`, `"date"`, `"time"`, `"datetime"`, `"array"`

**Per-column:**
```js
{ title: "Birthday", field: "dob", sorter: "date",
  sorterParams: { format: "yyyy-MM-dd" } }
```

**Custom sorter:**
```js
{
  title: "Name", field: "name",
  sorter: (a, b, aRow, bRow, column, dir, sorterParams) => {
    return String(a).toLowerCase().localeCompare(String(b).toLowerCase());
  }
}
```

**Header sort behavior (per column):**
```js
{ field: "age",
  headerSort: true,                // default - set false to disable
  headerSortStartingDir: "desc",   // default: "asc"
  headerSortTristate: true,        // asc → desc → none
}
```

**Global sort options:**
```js
columnHeaderSortMulti: false,       // disable multi-column sort via ctrl/shift
sortOrderReverse: true,             // reverse sort application order
headerSortClickElement: "icon",     // "header" (default) | "icon" - restrict click target
headerSortElement: "<i class='fas fa-arrow-up'></i>",  // custom sort icon HTML
```

**Initial sort:**
```js
initialSort: [
  { column: "age", dir: "asc" },
  { column: "name", dir: "desc" },
]
```

**Programmatic API:**
```js
table.setSort("age", "asc");
table.setSort([
  { column: "age", dir: "asc" },
  { column: "name", dir: "desc" },
]);
table.getSorters();   // [{column, field, dir}, ...]
table.clearSort();
```

**Server-side sorting:**
```js
sortMode: "remote",
// Sends "sorters" param: [{field:"age", dir:"asc"}]
```

---

## Filtering

**Built-in filter types:** `"="`, `"!="`, `"<"`, `"<="`, `">"`, `">="`, `"like"`, `"keywords"`, `"starts"`, `"ends"`, `"in"`, `"regex"`, `"smart"`, `"smarter"`

**Programmatic:**
```js
table.setFilter("age", ">", 10);
table.setFilter("name", "like", "steve");
table.setFilter("name", "keywords", "red green blue", { matchAll: true });
table.setFilter("name", "in", ["steve", "bob", "jim"]);
table.setFilter("name", "regex", /^[A-Z]/);
```

**Multiple filters (AND):**
```js
table.setFilter([
  { field: "age", type: ">", value: 52 },
  { field: "height", type: "<", value: 142 },
]);
```

**Complex (AND with OR inside):**
```js
table.setFilter([
  { field: "age", type: ">", value: 52 },
  [
    { field: "height", type: "<", value: 142 },
    { field: "name", type: "=", value: "steve" },
  ],
]);
```

**Custom filter function:**
```js
table.setFilter((data, filterParams) => {
  return data.car && data.rating < 3;
}, { /* optional params */ });
```

**Managing filters:**
```js
table.addFilter("age", ">", 22);           // add to existing filters
table.removeFilter("age", ">", 22);        // remove one filter
table.refreshFilter();                     // re-run existing filters
table.getFilters();                        // programmatic only
table.getFilters(true);                    // include header filters
table.getHeaderFilters();                  // header filters only
table.clearFilter();                       // clear programmatic
table.clearFilter(true);                   // clear programmatic + header
table.clearHeaderFilter();                 // clear header filters only
```

**Initial filters:**
```js
initialFilter: [
  { field: "color", type: "=", value: "red" },
]
```

**Search (non-destructive):**
```js
table.searchRows("age", ">", 12);   // returns RowComponent[]
table.searchData("age", ">", 12);   // returns row data[]
```

**Server-side filtering:**
```js
filterMode: "remote",
// Sends "filters" param: [{field:"age", type:">", value:52}]
```

---

## Header Filters

**Per-column header filter:**
```js
{ title: "Name",  field: "name", headerFilter: "input" },
{ title: "Age",   field: "age",  headerFilter: "number",
  headerFilterPlaceholder: "Min", headerFilterFunc: ">=" },
{ title: "Dept",  field: "dept", headerFilter: "list",
  headerFilterParams: { values: ["Eng", "Sales", "Marketing"], clearable: true } },
{ title: "Active", field: "active", headerFilter: "tickCross",
  headerFilterParams: { tristate: true } },
```

**Available header filter editors:** Same as cell editors — `"input"`, `"number"`, `"list"`, `"tickCross"`, `"textarea"`, `"date"`, `"time"`, `"range"`. Set to `true` to auto-match the column's `editor` type.

**Placeholder:**
```js
headerFilterPlaceholder: "Search..."
```

**Custom filter function for header:**
```js
{ title: "Age", field: "age", headerFilter: "input",
  headerFilterFunc: (headerValue, rowValue, rowData, filterParams) => {
    return rowData.name === "bob" && rowValue < headerValue;
  },
  headerFilterFuncParams: { name: "bob" },
}
```

**Live filter behavior:**
```js
headerFilterLiveFilter: false,     // disable live keystroke filtering (default: true)
headerFilterLiveFilterDelay: 600,  // debounce delay in ms (default: 300)
```

**Empty check (what counts as "empty" for the filter):**
```js
headerFilterEmptyCheck: (value) => !value,
```

**Programmatic header filter control:**
```js
table.setHeaderFilterValue("name", "Steve");
table.getHeaderFilterValue("name");
table.setHeaderFilterFocus("name");
```

**Initial header filter values:**
```js
initialHeaderFilter: [
  { field: "color", value: "red" },
]
```

---

## Pagination

### Local (client-side)

```js
pagination: "local",           // or just pagination: true
paginationSize: 10,
paginationSizeSelector: [10, 25, 50, 100],  // or true (auto-generate multiples)
paginationCounter: "rows",     // "Showing X-Y of Z rows"
paginationCounter: "pages",    // "Showing X of Y pages"
paginationButtonCount: 5,      // number of page number buttons in footer
paginationInitialPage: 2,      // start on page 2
```

**Auto page size from height:** If `height` is set and `paginationSize` is not, page size auto-fills to table height.

**Page size selector with "All":**
```js
paginationSizeSelector: [10, 25, 50, 100, true]   // true = "All" option
```

**Add row behavior:**
```js
paginationAddRow: "table",     // "page" (default, relative to current page) | "table"
```

**Custom counter:**
```js
paginationCounter: (pageSize, currentRow, currentPage, totalRows, totalPages) => {
  return `Showing ${pageSize} rows of ${totalRows} total`;
}
```

### Remote (server-side)

```js
pagination: true,
paginationMode: "remote",
ajaxURL: "/api/data",
paginationSize: 25,
```

**Custom parameter names:**
```js
dataSendParams: {
  page: "page",
  size: "size",
  sorters: "sorters",
  filters: "filters",
},
dataReceiveParams: {
  last_page: "last_page",
  last_row: "last_row",
  data: "data",
},
```

**Remote response format:**
```json
{
  "last_page": 15,
  "last_row": 246,
  "data": [ /* row data objects */ ]
}
```

**Custom URL generation:**
```js
ajaxURLGenerator: (url, config, params) => {
  return url + "?params=" + encodeURI(JSON.stringify(params));
}
```

### Pagination API

```js
table.setPage(5);                 // integer, or "first"|"prev"|"next"|"last"
table.nextPage();
table.previousPage();
table.setPageToRow(rowIndex);     // local pagination only
table.setPageSize(50);
table.getPage();                  // current page number
table.getPageMax();               // max page number
table.getPageSize();              // rows per page
```

All page-changing methods return Promises:
```js
table.setPage(1)
  .then(() => { /* after page loaded */ })
  .catch((error) => { /* handle error */ });
```

**Page out of range:**
```js
paginationOutOfRange: "last",     // "first"|"prev"|"next"|"last"|integer|callback
```

**Custom pagination element:**
```js
paginationElement: document.getElementById("my-pagination")
```

**Custom counter element:**
```js
paginationCounterElement: "#page-count"
```

---

## Client / Server Side Modes

Three independent mode switches:

| Feature | Client-side | Server-side |
|---|---|---|
| Sorting | `sortMode: "local"` (default) | `sortMode: "remote"` |
| Filtering | `filterMode: "local"` (default) | `filterMode: "remote"` |
| Pagination | `paginationMode: "local"` (default) | `paginationMode: "remote"` + `ajaxURL` |

They can be mixed. Example: local pagination (load all data at once) but remote sorting:

```js
pagination: true,
paginationMode: "local",
sortMode: "remote",
ajaxURL: "/api/data",
```

### AJAX Parameters Sent

When any mode is `"remote"`, the AJAX request includes:

| Param | Type | Description |
|---|---|---|
| `page` | int | Requested page number (if remote pagination) |
| `size` | int | Rows per page (if remote pagination) |
| `sorters` | array | `[{field:"age", dir:"asc"}, ...]` (if remote sorting) |
| `filters` | array | `[{field:"age", type:">", value:52}, ...]` (if remote filtering) |

Customize param names with `dataSendParams`.

### AJAX Configuration

```js
ajaxURL: "/api/data",
ajaxParams: { token: "ABC123" },
ajaxParams: () => ({ token: getToken() }),      // dynamic params callback
ajaxConfig: "POST",                              // or fetch config object
ajaxConfig: { method: "POST", headers: { "X-Custom": "val" } },
ajaxContentType: "json",                         // or "form"
ajaxResponse: (url, params, response) => response.rows,  // transform response
ajaxRequestFunc: myCustomFetchFn,                // replace fetch entirely
ajaxURLGenerator: (url, config, params) => url,  // custom URL builder
```

### Progressive Loading

Load data in chunks without showing pagination controls:

```js
progressiveLoad: "scroll",    // load as user scrolls
progressiveLoadScrollMargin: 300,  // px from bottom to trigger next load
progressiveLoad: "load",      // sequential load all pages
progressiveLoadDelay: 200,    // ms delay between requests
```

**Note:** Uses pagination module internally. Server must return paginated response format.

---

## Data Loading

```js
// From array (initial)
data: [{ id: 1, name: "Bob" }, ...]

// From array (programmatic)
table.setData([{ id: 1, name: "Bob" }, ...]);

// From AJAX
table.setData("/api/data");
table.setData("/api/data", { key: "val" }, "POST");

// Reload from ajaxURL
table.setData();

// Import from file (6.1+)
table.import("csv", ".csv");
table.import("json", ".json");
table.import("xlsx", ".xlsx", "buffer");  // requires SheetJS

// Import with setData
importFormat: "csv",
table.setData(csvString);

// From HTML table
// Just point Tabulator at the table element; it reads <thead> and <tbody>
new Tabulator("#existing-table", {});

// Clear data
table.clearData();
```

`setData()` returns a Promise:
```js
table.setData(data)
  .then(() => { /* loaded */ })
  .catch((err) => { /* error */ });
```

---

## Table Methods — Quick Reference

```js
// Data
table.getData();                       // all row data
table.getData("active");               // filtered/sorted visible rows
table.addRow({ name: "New" }, true);   // true = top, false = bottom
table.updateRow(index, { age: 30 });
table.updateOrAddRow(index, rowData);
table.deleteRow(index);

// Rows
table.getRows();                       // RowComponent[]
table.getRow(index);
table.selectRow("active");
table.deselectRow();
table.getSelectedRows();

// Columns
table.getColumns();                    // ColumnComponent[]
table.getColumns(true);                // includes column groups
table.getColumn("age");
table.showColumn("name");
table.hideColumn("name");
table.toggleColumn("name");
table.setColumns(newDefs);
table.addColumn(def, before, positionField);
table.updateColumnDefinition("name", { title: "Full Name" });

// Sorting — see Sorting section
// Filtering — see Filtering section
// Pagination — see Pagination section

// Layout
table.redraw();
table.redraw(true);                    // force full recalculation

// Export
table.download("csv", "data.csv");
table.download("xlsx", "data.xlsx");
table.download("pdf", "data.pdf", { orientation: "landscape" });
table.copyToClipboard("active");

// State
Tabulator.findTable("#my-table");      // lookup table from CSS selector
Tabulator.defaultOptions.layout = "fitColumns";  // set global defaults
```

---

## Events

```js
table.on("rowClick", (e, row) => { /* RowComponent */ });
table.on("rowDblClick", (e, row) => {});
table.on("cellClick", (e, cell) => { /* CellComponent */ });
table.on("dataLoaded", () => {});
table.on("dataLoadError", (error) => {});
table.on("dataLoading", (data) => {});
table.on("tableBuilt", () => {});
table.on("renderStarted", () => {});
table.on("renderComplete", () => {});

// Sorting
table.on("sortChanged", (sorters, dir) => {});

// Filtering
table.on("filterChanged", (filters) => {});
table.on("headerFilterCreated", (field, element) => {});

// Pagination
table.on("pageLoaded", (pageno) => {});
table.on("pageSizeChanged", (size) => {});

// Data
table.on("rowAdded", (row) => {});
table.on("rowUpdated", (row) => {});
table.on("rowDeleted", (row) => {});
table.on("dataProcessed", () => {});

// Column
table.on("columnMoved", (column, columns) => {});
table.on("columnResized", (column) => {});
table.on("columnVisibilityChanged", (column, visible) => {});
table.on("columnTitleChanged", (column) => {});

// Selection
table.on("rowSelected", (row) => {});
table.on("rowDeselected", (row) => {});

// AJAX
table.on("ajaxRequesting", (url, params) => {});
table.on("ajaxResponse", (url, params, response) => {});
table.on("ajaxError", (url, params, error) => {});
```

---

## Themes

Tabulator ships with multiple CSS themes:
- `tabulator.min.css` — default theme
- `tabulator_bootstrap5.css` — Bootstrap 5
- `tabulator_midnight.css` — dark theme
- `tabulator_simple.css` — minimal theme
- `tabulator_modern.css` — modern flat
- `tabulator_site.css` — dark site theme

Usage:
```html
<link href="dist/css/tabulator_bootstrap5.min.css" rel="stylesheet">
```

---

## Key Setup Options

```js
height: "300px",           // enables virtual DOM
minHeight: "200px",
maxHeight: "800px",
layout: "fitColumns",      // fitData | fitDataFill | fitDataStretch
index: "id",               // unique row identifier field
placeholder: "No data",    // empty state
selectableRows: true,      // highlight (default) | true | false | integer
movableColumns: true,
movableRows: true,
resizableRows: true,
history: true,             // undo/redo support
clipboard: true,           // copy/paste
reactiveData: false,       // reactive data binding
headerVisible: true,       // hide all column headers
footerElement: "<div>...</div>",  // custom footer HTML
locale: true,              // enable localization
langs: { "default": { "pagination": { "counter": { "rows": "rows" } } } },