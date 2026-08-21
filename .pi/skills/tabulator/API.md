# Tabulator v6.x API Reference

Focused reference for: **General Usage, Sorting, Filtering, Pagination, Client/Server Side**.

---

## 1. General Usage

### Constructor

```js
new Tabulator(HTMLElement_or_CSS_selector, options_object)
```

Returns the table instance. All methods below are called on this instance.

### Key Setup Options

| Option | Type | Default | Description |
|---|---|---|---|
| `height` | string/int | `false` | Table height (enables virtual DOM). CSS value e.g. `"300px"` |
| `layout` | string | `"fitData"` | Column layout: `"fitData"`, `"fitColumns"`, `"fitDataFill"`, `"fitDataStretch"` |
| `index` | string | `"id"` | Unique row identifier field |
| `data` | array | `false` | Initial row data |
| `ajaxURL` | string/bool | `false` | URL for AJAX data loading |
| `columns` | array | `[]` | Column definition array |
| `columnDefaults` | object | `{}` | Default options applied to all columns |
| `autoColumns` | bool/string | `false` | Auto-generate columns from data (use `"full"` to scan all rows) |
| `autoColumnsDefinitions` | fn/arr/obj | `false` | Customize auto-generated column definitions |
| `placeholder` | string/DOM | `""` | Empty state content |
| `footerElement` | string/DOM | `false` | Custom footer HTML |
| `headerVisible` | bool | `true` | Show/hide all column headers |
| `nestedFieldSeparator` | string/bool | `"."` | Separator for nested field notation. Set `false` to disable |
| `selectableRows` | bool/int/string | `"highlight"` | Row selection: `true`, `false`, integer, `"highlight"` |
| `movableColumns` | bool | `false` | Allow column reorder |
| `movableRows` | bool | `false` | Allow row reorder |
| `history` | bool | `false` | Enable undo/redo |
| `clipboard` | bool | `false` | Enable copy/paste |
| `locale` | string/bool | `false` | Set locale language |
| `langs` | object | `{}` | Localization templates |
| `debugInvalidOptions` | bool | `true` | Warn on invalid options |

### Column Definition

Every column in the `columns` array is an object with the following properties:

| Property | Type | Default | Description |
|---|---|---|---|
| `title` | string | — | Header text |
| `field` | string | — | Data key. Dot notation for nested: `"user.name"` |
| `visible` | bool | `true` | Initially visible |
| `width` | int | auto | Column width (px or % with fitColumns) |
| `minWidth` | int | — | Minimum width in px |
| `maxWidth` | int | — | Maximum width in px |
| `maxInitialWidth` | int | — | Max width on first render (user can resize beyond this) |
| `widthGrow` | int | — | Grow ratio in fitColumns layout |
| `widthShrink` | int | — | Shrink ratio in fitColumns layout |
| `resizable` | bool | — | User can resize (see `resizableColumns` global) |
| `frozen` | bool | `false` | Freeze column when scrolling |
| `responsive` | int | — | Priority for responsive hiding (lower = hidden first) |
| `hozAlign` | string | — | Horizontal alignment: `"left"`, `"center"`, `"right"` |
| `vertAlign` | string | — | Vertical alignment: `"top"`, `"middle"`, `"bottom"` |
| `headerHozAlign` | string | — | Header title alignment |
| `cssClass` | string | — | Space-separated CSS classes on header + cells |
| `tooltip` | bool/string/fn | — | Cell tooltip |
| `headerTooltip` | bool/string/fn | — | Header tooltip |
| `headerVertical` | bool/str | `false` | `true` or `"flip"` for vertical headers |
| `editableTitle` | bool | — | Allow user to edit column title |
| `headerWordWrap` | bool | — | Allow text wrapping in header |
| `formatter` | string/fn | — | Cell formatter: `"progress"`, `"star"`, `"tickCross"`, `"money"`, `"color"`, `"traffic"`, `"link"`, `"image"`, `"buttonTick"`, `"buttonCross"`, `"rownum"`, `"handle"`, `"textarea"`, `"plaintext"`, `"html"`, `"json"`, `"array"`, `"lookup"`, `"datetime"`, `"datetimediff"`, `"toggle"`, `"adaptable"`, or custom fn |
| `formatterParams` | object | — | Params for the formatter |
| `editor` | string/fn/bool | — | Cell editor: `"input"`, `"number"`, `"textarea"`, `"select"`, `"list"`, `"date"`, `"time"`, `"datetime"`, `"tickCross"`, `"star"`, `"progress"`, `"range"`, `"adaptable"`, or custom fn. `true` uses editor from column defaults |
| `editorParams` | object | — | Params for the editor |
| `variableHeight` | bool | — | Auto-height rows to fit cell content |
| `htmlOutput` | bool | — | Include in getHtml output |
| `print` | bool | — | Include in print output |
| `clipboard` | bool | — | Include in clipboard output |
| `download` | bool | — | Include in downloaded file |
| `topCalc` | string/fn | — | Column calculation at top: `"sum"`, `"min"`, `"max"`, `"avg"`, `"count"`, or custom |
| `bottomCalc` | string/fn | — | Column calculation at bottom |

**Cell event callbacks (per column):** `cellClick`, `cellDblClick`, `cellContext`, `cellMouseEnter`, `cellMouseLeave`, `cellMouseOver`, `cellMouseOut`, `cellMouseDown`, `cellMouseUp`, `cellEditing`, `cellEdited`, `cellEditCancelled`, `cellTap`, `cellDblTap`, `cellTapHold`

**Header event callbacks (per column):** `headerClick`, `headerDblClick`, `headerContext`, `headerMouseEnter`, `headerMouseLeave`, `headerMouseOver`, `headerMouseOut`, `headerMouseDown`, `headerMouseUp`, `headerTap`, `headerDblTap`, `headerTapHold`

### Column Methods

```js
table.setColumns(newDefs);                         // Replace all columns
table.addColumn({ title:"Age", field:"age" }, true, "name");  // Add column (before=true, next to "name")
table.deleteColumn("name");                        // Delete by field
table.updateColumnDefinition("name", { title:"Full Name", width:200 });  // Update properties
table.getColumnDefinitions();                      // Get current definition array
table.getColumns();                                // Get ColumnComponent[]
table.getColumns(true);                            // Includes column groups
table.getColumn("age");                            // Get ColumnComponent by field
table.showColumn("name");                          // Show hidden column
table.hideColumn("name");                          // Hide column
table.toggleColumn("name");                        // Toggle visibility
```

### Data Methods

```js
table.setData(array_or_url);          // Load data (array or AJAX URL)
table.setData(url, params, config);   // AJAX with params and fetch config
table.getData();                      // All row data
table.getData("active");              // Filtered/sorted visible rows
table.getData("all");                 // All rows including filtered out
table.addRow(data, true);             // Add row (true=top, false=bottom)
table.updateRow(index, newData);      // Update row by index
table.updateOrAddRow(index, newData); // Update if exists, else add
table.deleteRow(index);               // Delete row by index
table.clearData();                    // Clear all data
```

### Row Methods

```js
table.getRows();              // Get all RowComponent[]
table.getRow(index);          // Get RowComponent by index
table.selectRow();            // Select all
table.selectRow("active");    // Deselect
table.deselectRow();          // Deselect all
table.getSelectedRows();      // Selected RowComponent[]
```

On a RowComponent: `getData()`, `getElement()`, `getCell(column)`, `select()`, `deselect()`, `delete()`, `update(data)`, `scrollTo()`, `pageTo()`, `getIndex()`.

### Component Lookup

Many `table` methods accept any of the following for column lookup:
- Field name string: `"age"`
- Column component object
- Column header DOM element

Row lookup accepts:
- Row index value (integer or string matching the `index` field)
- Row component object
- Row DOM element
- Row data object (must have the `index` field)

### Events

```js
table.on("tableBuilt", () => {});
table.on("dataLoading", (data) => {});
table.on("dataLoaded", (data) => {});
table.on("dataLoadError", (error) => {});
table.on("dataProcessing", (data) => {});
table.on("dataProcessed", (data) => {});
table.on("renderStarted", () => {});
table.on("renderComplete", () => {});
table.on("rowClick", (e, row) => {});
table.on("rowDblClick", (e, row) => {});
table.on("rowContext", (e, row) => {});
table.on("cellClick", (e, cell) => {});
table.on("cellDblClick", (e, cell) => {});
table.on("dataTreeRowExpanded", (row, level) => {});
table.on("dataTreeRowCollapsed", (row, level) => {});
table.on("columnMoved", (column, columns) => {});
table.on("columnResized", (column) => {});
table.on("columnVisibilityChanged", (column, visible) => {});
table.on("columnTitleChanged", (column) => {});
```

---

## 2. Sorting

### Built-in Sorters

| Name | Key | sorterParams |
|---|---|---|
| String | `"string"` | `{ locale: "en", alignEmptyValues: "top"\|"bottom" }` |
| Numeric | `"number"` | `{ thousandSeparator: ",", decimalSeparator: ".", alignEmptyValues: "top"\|"bottom" }` |
| Alphanumeric | `"alphanum"` | `{ alignEmptyValues: "top"\|"bottom" }` |
| Boolean | `"boolean"` | — |
| Field Exists | `"exists"` | — |
| Date | `"date"` | `{ format: "yyyy-MM-dd", alignEmptyValues: "top"\|"bottom" }` — requires Luxon |
| Time | `"time"` | `{ format: "HH:mm:ss", alignEmptyValues: "top"\|"bottom" }` — requires Luxon |
| Date Time | `"datetime"` | `{ format: "yyyy-MM-dd HH:mm:ss", alignEmptyValues: "top"\|"bottom" }` — requires Luxon |
| Array | `"array"` | `{ type: "length"\|"sum"\|"max"\|"min"\|"avg"\|"string", alignEmptyValues: "top"\|"bottom", valueMap: "property.path"\|fn }` |

### Column Definition for Sorting

```js
{ title: "Name", field: "name", sorter: "string" }
{ title: "Age", field: "age", sorter: "number", sorterParams: { alignEmptyValues: "top" } }
{ title: "Birthday", field: "dob", sorter: "date", sorterParams: { format: "MM/dd/yyyy" } }
{ title: "Tags", field: "tags", sorter: "array", sorterParams: { type: "max", valueMap: "details.age" } }
```

**Dynamic sorterParams via function:**
```js
sorterParams: (column, dir) => ({ format: dir === "asc" ? "yyyy-MM-dd" : "dd-MM-yyyy" })
```

### Custom Sorter

```js
{
  title: "Name", field: "name",
  sorter: (a, b, aRow, bRow, column, dir, sorterParams) => {
    // a, b — the two values being compared
    // aRow, bRow — RowComponents for the rows
    // column — ColumnComponent for the column
    // dir — "asc" or "desc"
    // sorterParams — from column definition
    return String(a).toLowerCase().localeCompare(String(b).toLowerCase());
  }
}
```

### Header Sort Configuration

**Per-column:**
```js
{ field: "age", headerSort: true }              // default — set false to disable
{ field: "age", headerSortStartingDir: "desc" } // first click sorts desc (default: asc)
{ field: "age", headerSortTristate: true }      // none → asc → desc → none
```

**Global:**
```js
columnHeaderSortMulti: false,      // disable ctrl+click multi-column sort (default: true)
sortOrderReverse: true,            // reverse sort application order
headerSortClickElement: "icon",    // "header" (default) or "icon" — restrict click target
headerSortElement: "<i class='fas fa-arrow-up'></i>",  // custom sort icon HTML
```

**headerSortElement callback:**
```js
headerSortElement: (column, dir) => {
  // dir is "asc", "desc", or "none"
  switch(dir) {
    case "asc":  return "<i class='fas fa-sort-up'>";
    case "desc": return "<i class='fas fa-sort-down'>";
    default:     return "<i class='fas fa-sort'>";
  }
}
```

### Initial Sort

```js
initialSort: [
  { column: "age", dir: "asc" },
  { column: "name", dir: "desc" },
]
```

### Programmatic Sort API

```js
table.setSort("age", "asc");
table.setSort([
  { column: "age", dir: "asc" },
  { column: "name", dir: "desc" },
]);
table.getSorters();
// Returns: [{ column: ColumnComponent, field: "age", dir: "asc" }, ...]
table.clearSort();
```

### Server-side Sorting

```js
sortMode: "remote",
```

When set, the `sorters` parameter is sent with AJAX requests:
```
sorters[0][field]=age&sorters[0][dir]=asc
```

The parameter name can be customized via `dataSendParams.sorters`.

### Sort Events

```js
table.on("sortChanged", (sorters, dir) => {
  // sorters — current sort array
  // dir — current sort direction
});
```

### Sort Icon CSS

Tabulator adds `aria-sort` attribute to sorted columns:
```css
.tabulator-col[aria-sort="none"] .tabulator-col-sorter i { /* unsorted */ }
.tabulator-col[aria-sort="asc"] .tabulator-col-sorter i  { /* ascending */ }
.tabulator-col[aria-sort="desc"] .tabulator-col-sorter i { /* descending */ }
```

---

## 3. Filtering

### Built-in Filter Types

| Type | Key | Description |
|---|---|---|
| Equal | `"="` | Exact match |
| Not Equal | `"!="` | Not exact match |
| Less Than | `"<"` | Numeric less than |
| Less or Equal | `"<="` | Numeric less than or equal |
| Greater Than | `">"` | Numeric greater than |
| Greater or Equal | `">="` | Numeric greater than or equal |
| Like | `"like"` | Case-insensitive substring match |
| Keywords | `"keywords"` | Match any/all space-separated keywords (default: any) |
| Starts With | `"starts"` | Case-insensitive starts-with |
| Ends With | `"ends"` | Case-insensitive ends-with |
| In Array | `"in"` | Value present in array |
| Regex | `"regex"` | Regex match |
| Smart | `"smart"` | Smart filter — supports `>100`, `<50`, `>=`, `<=`, `=value`, `.` (non-empty), `!` (empty), space-separated AND of multiple terms |
| Smarter | `"smarter"` | Like smart but supports explicit `AND`/`OR` operators: `">100 AND <500"`, `"john OR jane"` |

### Programmatic Filter API

```js
// Single filter
table.setFilter("age", ">", 10);
table.setFilter("name", "like", "steve");
table.setFilter("name", "keywords", "red green blue", { matchAll: true });
table.setFilter("name", "in", ["steve", "bob", "jim"]);
table.setFilter("name", "regex", /^[A-Z]/);

// Multiple filters (AND)
table.setFilter([
  { field: "age", type: ">", value: 52 },
  { field: "height", type: "<", value: 142 },
]);

// Complex (AND with OR)
table.setFilter([
  { field: "age", type: ">", value: 52 },
  [
    { field: "height", type: "<", value: 142 },
    { field: "name", type: "=", value: "steve" },
  ],
]);

// Custom filter function
table.setFilter(function(data, filterParams) {
  // data — row data object
  // filterParams — params from second argument
  return data.car && data.rating < 3;
}, { customParam: true });
```

### Managing Filters

```js
table.addFilter("age", ">", 22);                    // Append to existing filters
table.addFilter("tags", "keywords", "red green", { matchAll: true });

table.removeFilter("age", ">", 22);                 // Remove specific filter
table.refreshFilter();                               // Re-run all filters

table.getFilters();                                  // Programmatic filters only
table.getFilters(true);                              // Including header filters
table.getHeaderFilters();                            // Header filters only

table.clearFilter();                                 // Clear programmatic filters
table.clearFilter(true);                             // Clear programmatic + header
table.clearHeaderFilter();                           // Clear header filters only
```

Returns array of `{ field, type, value }` objects.

### Initial Filter

```js
initialFilter: [
  { field: "color", type: "=", value: "red" },
]
```

### Header Filter Configuration

**Per-column:**
```js
{ title: "Name",   field: "name",   headerFilter: "input" },
{ title: "Age",    field: "age",    headerFilter: "number",
  headerFilterPlaceholder: "Min Age",
  headerFilterFunc: ">=" },
{ title: "Active", field: "active", headerFilter: "tickCross",
  headerFilterParams: { tristate: true } },
{ title: "Dept",   field: "dept",   headerFilter: "list",
  headerFilterParams: { values: ["Engineering", "Sales"], clearable: true } },
{ title: "Score",  field: "score",  headerFilter: "true",  // auto-match editor type
  headerFilterLiveFilter: false },                         // disable live filtering
```

**Available header filter editors:** `"input"`, `"number"`, `"textarea"`, `"list"` (dropdown), `"tickCross"` (checkbox), `"date"`, `"time"`, `"range"`, `true` (auto-match column editor)

**Custom header filter function:**
```js
{ title: "Age", field: "age", headerFilter: "input",
  headerFilterFunc: (headerValue, rowValue, rowData, filterParams) => {
    // headerValue — the filter input value
    // rowValue — the cell value
    // rowData — the full row data
    // filterParams — from headerFilterFuncParams
    return rowValue < headerValue;
  },
  headerFilterFuncParams: { margin: 5 },
}
```

**Placeholder:**
```js
headerFilterPlaceholder: "Search..."
```

**Live filter delay (global):**
```js
headerFilterLiveFilterDelay: 600   // ms after last keystroke (default: 300)
```

**Empty check (customize what resets the filter):**
```js
headerFilterEmptyCheck: (value) => !value,  // return true when filter should be cleared
```

### Header Filter API

```js
table.setHeaderFilterValue("name", "Steve");     // Set header filter value
table.getHeaderFilterValue("name");               // Get current value
table.setHeaderFilterFocus("name");               // Focus the header filter element
```

### Initial Header Filter Values

```js
initialHeaderFilter: [
  { field: "color", value: "red" },
]
```

### Search (Non-destructive)

```js
table.searchRows("age", ">", 12);         // Returns RowComponent[]
table.searchData("age", ">", 12);          // Returns row data objects[]

// Works with any setFilter-compatible arguments:
table.searchRows([
  { field: "age", type: ">", value: 12 },
  { field: "name", type: "like", value: "bob" },
]);
```

### Server-side Filtering

```js
filterMode: "remote",
```

Sends `filters` parameter with AJAX requests:
```
filters[0][field]=age&filters[0][type]=>&filters[0][value]=52
```

Custom filters send `filters[0][type]=function`.
Parameter name customizable via `dataSendParams.filters`.

### Filter Events

```js
table.on("filterChanged", (filters) => {
  // filters — current filter array
});
table.on("headerFilterCreated", (field, element) => {
  // field — column field name
  // element — DOM element of the header filter
});
```

### Filter Comparison Details

| Type | Match |
|---|---|
| `"="` | `rowVal == filterVal` |
| `"!="` | `rowVal != filterVal` |
| `"<"` | `rowVal < filterVal` |
| `"<="` | `rowVal <= filterVal` |
| `">"` | `rowVal > filterVal` |
| `">="` | `rowVal >= filterVal` |
| `"like"` | Case-insensitive `String(rowVal).includes(filterVal)` |
| `"keywords"` | Split filterVal by separator (default space), check each as like, `matchAll` controls AND vs OR |
| `"starts"` | Case-insensitive `String(rowVal).startsWith(filterVal)` |
| `"ends"` | Case-insensitive `String(rowVal).endsWith(filterVal)` |
| `"in"` | `filterVal.includes(rowVal)` |
| `"regex"` | `filterVal.test(rowVal)` (accepts string or RegExp) |
| `"smart"` | `=value`, `>num`, `<num`, `>=num`, `<=num`, `.` (non-empty), `!` (empty), space-separated terms AND'd |
| `"smarter"` | Smart with explicit `AND` / `OR` operators |

---

## 4. Pagination

### Overview

Two modes:
- **Local:** Tabulator loads all data, then paginates client-side
- **Remote:** Tabulator requests individual pages via AJAX

When pagination is active, a footer with navigation controls is added to the table. Changing sort/filter resets to page 1.

### Local Pagination

```js
pagination: true,           // enables local pagination (equivalent to pagination: "local")
paginationSize: 10,         // rows per page
paginationSizeSelector: [10, 25, 50, 100],  // or true (auto-generate multiples)
paginationCounter: "rows",  // show "Showing X-Y of Z rows"
paginationButtonCount: 5,   // number of page number buttons
paginationInitialPage: 2,   // start on page 2 (default: 1)
```

**Auto page size from height:** If `height` is set but `paginationSize` is not, Tabulator calculates page size to fill the table height.

**Page size selector with "All":**
```js
paginationSizeSelector: [10, 25, 50, 100, true]   // true = show all rows
```

### Remote Pagination

```js
pagination: true,
paginationMode: "remote",
ajaxURL: "/api/data",
paginationSize: 25,
paginationInitialPage: 2,
```

**Custom parameter names:**
```js
dataSendParams: {
  page: "page",           // default: "page"
  size: "size",           // default: "size"
  sorters: "sorters",     // default: "sorters"
  filters: "filters",     // default: "filters"
},
dataReceiveParams: {
  last_page: "last_page", // default: "last_page"
  last_row: "last_row",   // default: "last_row"
  data: "data",           // default: "data"
}
```

**Remote response format:**
```json
{
  "last_page": 20,
  "last_row": 500,
  "data": [ /* row data objects */ ]
}
```

`last_page` is required and must be > 0. `last_row` is needed for accurate row counting in counters.

**Custom URL generation:**
```js
ajaxURLGenerator: (url, config, params) => {
  // url — from ajaxURL or setData
  // config — fetch config object
  // params — includes pagination, sort, filter params
  return url + "?params=" + encodeURI(JSON.stringify(params));
}
```

### Pagination Options

| Option | Type | Default | Description |
|---|---|---|---|
| `pagination` | bool | `false` | Enable pagination |
| `paginationMode` | string | `"local"` | `"local"` or `"remote"` |
| `paginationSize` | int | `10` | Rows per page |
| `paginationSizeSelector` | bool/arr | `false` | Enable page size dropdown. `true` = auto-generate, or `[10,25,50]` |
| `paginationElement` | DOM/selector | footer | Custom container for pagination controls |
| `paginationCounter` | string/fn | — | Enable counter: `"rows"`, `"pages"`, or custom function |
| `paginationCounterElement` | DOM/selector | footer | Custom container for counter |
| `paginationButtonCount` | int | `5` | Number of page buttons in footer |
| `paginationInitialPage` | int | `1` | Initial page to display |
| `paginationAddRow` | string | `"page"` | `"page"` (relative to current) or `"table"` (relative to table) |
| `paginationOutOfRange` | int/str/fn | — | Behavior when page is out of range: `"first"`, `"last"`, integer, or callback |

### Pagination API

```js
table.setPage(5);                       // Go to specific page
table.setPage("first");                 // "first" | "prev" | "next" | "last"
table.nextPage();
table.previousPage();
table.setPageToRow(12);                 // Go to page containing row with index 12 (local only)
table.setPageSize(50);                  // Change rows per page
table.getPage();                        // Current page number (or false if disabled)
table.getPageMax();                     // Max page number (or false if disabled)
table.getPageSize();                    // Current page size
```

All page-changing methods return a Promise:
```js
table.setPage(1)
  .then(() => { /* data loaded */ })
  .catch((error) => { /* handle error */ });
```

### Custom Pagination Counter

```js
paginationCounter: (pageSize, currentRow, currentPage, totalRows, totalPages) => {
  // pageSize — rows per page
  // currentRow — first visible row position
  // currentPage — current page number
  // totalRows — total rows in table
  // totalPages — total pages

  return `Showing ${pageSize} rows of ${totalRows} total`;
  // Return string, valid HTML, or DOM node
}
```

### Built-in Counters

- `"rows"` → "Showing X-X of X rows"
- `"pages"` → "Showing X of X pages"

Counter label localization:
```js
langs: {
  "default": {
    "pagination": {
      "counter": {
        "showing": "Showing",
        "of": "of",
        "rows": "rows",
        "pages": "pages",
      }
    }
  }
}
```

### Pagination Events

```js
table.on("pageLoaded", (pageno) => {
  // pageno — the page number that was loaded
});
table.on("pageSizeChanged", (size) => {
  // size — new page size
});
```

---

## 5. Client / Server Side

### Mode Configuration

Three independent switches control where data operations happen:

```js
sortMode: "local",       // "local" | "remote"
filterMode: "local",     // "local" | "remote"
paginationMode: "local", // "local" | "remote"
```

Any combination is valid. When all three are `"local"` (the default), all data is processed client-side with no AJAX needed.

### Full Remote (All data handled server-side)

```js
var table = new Tabulator("#example-table", {
  layout: "fitColumns",
  pagination: true,
  paginationMode: "remote",
  sortMode: "remote",
  filterMode: "remote",
  ajaxURL: "/api/data",
  paginationSize: 25,
  columns: [
    { title: "Name",  field: "name",  sorter: "string", headerFilter: "input" },
    { title: "Age",   field: "age",   sorter: "number", headerFilter: "number", headerFilterFunc: ">=" },
    { title: "Dept",  field: "dept",  sorter: "string", headerFilter: "list",
      headerFilterParams: { values: ["Eng", "Sales"], clearable: true } },
  ],
});
```

### AJAX Request Parameters

When any mode is `"remote"`, Tabulator sends the following as query/form parameters:

| Parameter | Type | Condition |
|---|---|---|
| `page` | int | Remote pagination enabled |
| `size` | int | Remote pagination + `paginationSize` set |
| `sorters[0][field]` | string | Remote sorting + table sorted |
| `sorters[0][dir]` | string | `"asc"` or `"desc"` |
| `filters[0][field]` | string | Remote filtering + filters active |
| `filters[0][type]` | string | Filter type: `"="`, `">"`, `"like"`, etc. |
| `filters[0][value]` | string | Filter value |
| (any `ajaxParams`) | — | Custom static/dynamic params |

Custom param names via `dataSendParams`:
```js
dataSendParams: {
  page: "pageNo",
  size: "pageSize",
  sorters: "orderBy",
  filters: "conditions",
}
```

### AJAX Response Handling

**Expected response (no pagination):**
```json
[ { "id": 1, "name": "Bob" }, { "id": 2, "name": "Alice" } ]
```

**Expected response (remote pagination):**
```json
{
  "last_page": 10,
  "last_row": 250,
  "data": [ /* row data */ ]
}
```

Custom field mapping via `dataReceiveParams`:
```js
dataReceiveParams: {
  last_page: "totalPages",
  last_row: "totalRecords",
  data: "rows",
}
```

**Response transformation:**
```js
ajaxResponse: (url, params, response) => {
  // Return an array of row data (for non-paginated)
  // Or a pagination object { last_page, last_row, data }
  return response.results;
}
```

### AJAX Configuration

```js
ajaxURL: "/api/data",
ajaxParams: { token: "ABC123" },
ajaxParams: () => ({ token: localStorage.getItem("token") }),  // dynamic
ajaxConfig: "POST",
ajaxConfig: {
  method: "POST",
  headers: { "X-API-Key": "abc123" },
  credentials: "include",
},
ajaxContentType: "json",     // JSON-encode params. "form" = form-encoded (default)
ajaxContentType: {
  headers: { "Content-Type": "text/plain" },
  body: (url, config, params) => JSON.stringify(params),
},
ajaxURLGenerator: (url, config, params) => {
  return url + "?" + new URLSearchParams(params);
},
ajaxRequestFunc: (url, config, params) => {
  // Replace fetch entirely — return a Promise resolving to row data
  return new Promise((resolve, reject) => {
    resolve([ /* row data array */ ]);
  });
},
ajaxResponse: (url, params, response) => {
  return response.data;
},
```

### Error Handling

```js
// Promise-based
table.setData("/api/data")
  .then(() => { /* success */ })
  .catch((error) => { /* Fetch Response object */ });

// Event-based
table.on("dataLoadError", (error) => {
  // error — Fetch Response object with status, body, etc.
});
```

**Abort a request before it starts:**
```js
ajaxRequesting: (url, params) => {
  return url.startsWith("/api/");  // return false to abort
}
```

### Progressive Loading

Load data in chunks without pagination controls visible:

```js
// Scroll mode — load as user scrolls
progressiveLoad: "scroll",
progressiveLoadScrollMargin: 200,  // px from bottom to trigger next request

// Load mode — sequentially load all pages
progressiveLoad: "load",
progressiveLoadDelay: 100,  // ms between requests

// Must include:
ajaxURL: "/api/data",
paginationSize: 50,         // size of each chunk
```

**Note:** Requires server to return paginated response format: `{ last_page, data }`.

### Multiple Remote Features — Request Example

When a user changes a header filter on a table with remote pagination + sorting, the request looks like:

```
GET /api/data?page=1&size=25&sorters[0][field]=age&sorters[0][dir]=asc&filters[0][field]=name&filters[0][type]=like&filters[0][value]=bob
```

---

## Themes

Include the appropriate CSS:
```html
<link href="dist/css/tabulator.min.css" rel="stylesheet">              <!-- default -->
<link href="dist/css/tabulator_bootstrap5.min.css" rel="stylesheet">   <!-- Bootstrap 5 -->
<link href="dist/css/tabulator_midnight.min.css" rel="stylesheet">     <!-- dark -->
<link href="dist/css/tabulator_simple.min.css" rel="stylesheet">       <!-- minimal -->
<link href="dist/css/tabulator_modern.min.css" rel="stylesheet">       <!-- modern -->
<link href="dist/css/tabulator_site.min.css" rel="stylesheet">         <!-- dark site -->
```

---

## Installation

```bash
npm install tabulator-tables --save
```

```js
// ESM import
import {TabulatorFull as Tabulator} from 'tabulator-tables';

// Or from CDN
import {Tabulator} from 'https://unpkg.com/tabulator-tables/dist/js/tabulator_esm.min.js';
```

```html
<!-- CDN script tag -->
<link href="https://unpkg.com/tabulator-tables/dist/css/tabulator.min.css" rel="stylesheet">
<script src="https://unpkg.com/tabulator-tables/dist/js/tabulator.min.js"></script>
```
