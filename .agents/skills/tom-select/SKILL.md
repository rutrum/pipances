---
name: tom-select
description: Reference for building custom select/tag inputs with Tom Select v2.x. Use whenever writing or reviewing HTML/JavaScript that uses new TomSelect(), settings/configuration, plugins, render templates, option/item management, remote data loading, event handlers, or any Tom Select API calls. Also triggers for questions about creating tags, multi-select, single-select, optgroups, remote search, custom rendering, or integrating Tom Select with FastAPI/Jinja2 backends.
---

# Tom Select v2.x Skill

A dynamic, framework-agnostic `<select>` UI control with autocomplete and keyboard navigation. Useful for tagging, contact lists, country selectors, etc. Forked from Selectize.js — modernized, jQuery-free.

**Version:** 2.x  
**Site:** <https://tom-select.js.org/>  
**Docs:** <https://tom-select.js.org/docs/>  
**GitHub:** <https://github.com/orchidjs/tom-select>  
**License:** Apache 2.0

---

## Quickstart

### CDN

```html
<link href="https://cdn.jsdelivr.net/npm/tom-select@2.6.2/dist/css/tom-select.css" rel="stylesheet">
<script src="https://cdn.jsdelivr.net/npm/tom-select@2.6.2/dist/js/tom-select.complete.min.js"></script>
```

### Basic usage with `<input>` (tag-style)

```html
<input id="input-tags" value="awesome,neat" autocomplete="off" placeholder="Add tags...">
<script>
  new TomSelect('#input-tags', {
    persist: false,
    createOnBlur: true,
    create: true,
  });
</script>
```

### Basic usage with `<select>`

```html
<select id="select-beast" placeholder="Select a person..." autocomplete="off">
  <option value="">Select a person...</option>
  <option value="4">Thomas Edison</option>
  <option value="1">Nikola Tesla</option>
</select>
<script>
  new TomSelect('#select-beast', {
    create: true,
    sortField: { field: "text", direction: "asc" },
  });
</script>
```

### NPM / ESM

```js
import TomSelect from 'tom-select';
import 'tom-select/dist/css/tom-select.css';
```

For a lean build with individually-selected plugins:

```js
import TomSelect from 'tom-select/base';
import remove_button from 'tom-select/plugins/remove_button';

TomSelect.define('remove_button', remove_button);
```

### Multiple instances via class selector

```js
document.querySelectorAll('.select').forEach((el) => {
  new TomSelect(el, { /* settings */ });
});
```

---

## Glossary

| Term | Definition |
|---|---|
| **Settings** | Configuration parameters passed to the TomSelect constructor; accessible via `tom.settings` |
| **Options** | The list of objects to display. Each must have a unique `value` field and a `label` field (configurable via `valueField`/`labelField`) |
| **Items** | The list of selected option values |
| **NodeDefinition** | An `HTMLElement` or DOMString (CSS selector or innerHTML string) |

---

## Core Settings

### General Configuration

| Setting | Type | Default | Description |
|---|---|---|---|
| `options` | `array` | `[]` | Array of `{value, text}` objects (auto-populated from `<select>`/`<input>`) |
| `items` | `array` | `[]` | Initial selected values (auto-populated from original element) |
| `create` | `boolean\|function` | `false` | Allow creating new items not in initial options. Can be a function: `function(input){ return {value:input, text:input}; }` or async: `function(input, callback){ ... callback(data); }` |
| `createOnBlur` | `boolean` | `false` | Create new option on blur (requires `create: true`) |
| `createFilter` | `RegExp\|string\|function` | `null` | Regex or predicate to validate created item text |
| `delimiter` | `string` | `','` | Separator for multiple values in text input; also used for paste-splitting |
| `highlight` | `boolean` | `true` | Toggle match highlighting in dropdown |
| `persist` | `boolean` | `true` | If `false`, user-created items disappear from dropdown when unselected |
| `openOnFocus` | `boolean` | `true` | Show dropdown immediately on focus |
| `maxOptions` | `int` | `50` | Max options in dropdown; `null` for unlimited |
| `maxItems` | `int` | `null` | Max selectable items; `1` makes it single-select, `null` = unlimited |
| `hideSelected` | `boolean` | `null` | Hide already-selected options from dropdown (defaults `true` for multi, `false` for single) |
| `closeAfterSelect` | `boolean` | `undefined` | Force close dropdown after selection (overrides default multi=open/single=close) |
| `allowEmptyOption` | `boolean` | `false` | Treat `""` value as a normal option |
| `loadThrottle` | `int` | `300` | Milliseconds to debounce remote load requests; `null` disables |
| `refreshThrottle` | `int` | `300` | Milliseconds to debounce local option refresh |
| `loadingClass` | `string` | `'loading'` | Class added to wrapper during load |
| `placeholder` | `string` | `undefined` | Placeholder text (override input attribute). Update post-init: `tom.settings.placeholder = "new"; tom.inputState();` |
| `hidePlaceholder` | `boolean` | `null` | Hide placeholder when items selected and not focused |
| `preload` | `boolean\|string` | `false` | Call `load` on init (`true`) or on focus (`'focus'`) |
| `dropdownParent` | `string` | `null` | Element to append dropdown to; `null` = child of control |
| `addPrecedence` | `boolean` | `false` | "Add..." option is default selection in dropdown |
| `selectOnTab` | `boolean` | `false` | Tab key selects highlighted item or creates new |
| `diacritics` | `boolean` | `true` | International character support |
| `controlInput` | `NodeDefinition\|null` | `<input>` | Custom input element; `null` disables |
| `duplicates` | `boolean` | `false` | Allow selecting same option multiple times (also set `hideSelected: false`) |
| `clearAfterSelect` | `boolean` | `false` | Clear input text after selecting an option |

### Data / Searching

| Setting | Type | Default | Description |
|---|---|---|---|
| `optgroups` | `array` | `[]` | Option groups for bucketing options (auto-populated from `<optgroup>`) |
| `dataAttr` | `string` | `null` | `<option>` attribute to read JSON data from |
| `valueField` | `string` | `'value'` | Property name for option values |
| `labelField` | `string` | `'text'` | Property name for option/item labels |
| `optgroupValueField` | `string` | `'value'` | Property name for optgroup unique identifier |
| `optgroupLabelField` | `string` | `'label'` | Property name for optgroup label |
| `optgroupField` | `string` | `'optgroup'` | Property name to group items by |
| `disabledField` | `string` | `'disabled'` | Property name for disabled option/optgroup |
| `sortField` | `string\|array\|function` | `[{field:'$score'}, {field:'$order'}]` | Sort configuration (maps to Sifter sort). Disable sort: `[{field:'$order'}, {field:'$score'}]` |
| `searchField` | `array` | `['text']` | Property names to search. With weights: `[{field:'text',weight:2},{field:'text2',weight:0.5}]`. Disable client-side search: `[]` |
| `searchConjunction` | `string` | `'and'` | `'and'` or `'or'` for multi-term search |
| `lockOptgroupOrder` | `boolean` | `false` | Display optgroups in original order |
| `copyClassesToDropdown` | `boolean` | `true` | Copy input CSS classes to dropdown element |
| `optionGroupRegister` | `function` | `null` | Transform/manage non-existent optgroups for remote data |

---

## Plugins

### Usage

```js
// Without options
new TomSelect('#select', { plugins: ['plugin_a', 'plugin_b'] });

// With options
new TomSelect('#select', {
  plugins: {
    'plugin_a': { /* options */ },
    'plugin_b': { /* options */ },
  }
});
```

### Bundles

| Bundle | Includes |
|---|---|
| `tom-select.complete.js` | All plugins |
| `tom-select.popular.js` | `dropdown_input`, `remove_button`, `no_backspace_delete`, `restore_on_backspace` |
| `tom-select.base.js` | No plugins (load individually) |

### Available Plugins

| Plugin | Category | Description |
|---|---|---|
| **remove_button** | Items | Adds an × button on each selected item to remove it. Config: `label` (default `&times;`), `title` (default `Remove`), `className` (default `remove`) |
| **clear_button** | Items | Adds a button to clear all selected items. Config: `html` (callback), `title` (default `Clear All`), `className` (default `clear-button`) |
| **no_backspace_delete** | Items | Prevents removing items with backspace/delete (combine with `no_active_items` to fully disable keyboard removal) |
| **restore_on_backspace** | Items | Restore option to dropdown when user removes it via backspace |
| **no_active_items** | Items | Disables the "active item" state — backspace always goes to the last item without highlighting it first |
| **caret_position** | Other | Allow arrow keys to move caret between selected items |
| **checkbox_options** | Dropdown | Adds checkboxes to dropdown options for multi-select |
| **dropdown_header** | Dropdown | Adds a header to the dropdown. Config: `title` (string), `headerClass`, `titleRowClass`, `labelClass` |
| **dropdown_input** | Control Input | Moves the search input into the dropdown instead of inline in the control |
| **input_autogrow** | Control Input | Automatically grows the input width to fit content |
| **change_listener** | Other | Fires change events on the original `<select>`/`<input>` when Tom Select's value changes |
| **drag_drop** | Items | Enables drag-and-drop reordering of selected items |
| **virtual_scroll** | Dropdown | Virtual scrolling for very large dropdown option lists |
| **optgroup_columns** | Dropdown | Display optgroup options in columns side-by-side |

---

## Callbacks

```js
new TomSelect('#select', {
  load: function(query, callback) {
    // Fetch data from server
    fetch('/api/search?q=' + encodeURIComponent(query))
      .then(r => r.json())
      .then(data => callback(data))
      .catch(() => callback());
  },
  shouldLoad: function(query) {
    return query.length >= 3; // min query length
  },
  score: function(search) {
    // Override scoring; return a function that returns a score (0 = no match)
    var score = this.getScoreFunction(search);
    return function(item) { return item.text.startsWith(search.query) ? score(item) : 0; };
  },
  onChange: function(value) { /* value changed */ },
  onItemAdd: function(value, $item) { /* item selected */ },
  onItemRemove: function(value, $item) { /* item deselected */ },
  onDropdownOpen: function(dropdown) { /* dropdown opened */ },
  onDropdownClose: function(dropdown) { /* dropdown closed */ },
  onType: function(str) { /* user typed */ },
  onLoad: function(options, optgroups) { /* remote data loaded */ },
  onInitialize: function() { /* control initialized */ },
  onFocus: function() { /* control focused */ },
  onBlur: function() { /* control blurred */ },
  onDelete: function(values, event) { return false; /* prevent delete */ },
  onClear: function() { /* cleared */ },
  onOptionAdd: function(value, data) { /* option added */ },
  onOptionRemove: function(value) { /* option removed */ },
});
```

### Full Callback List

| Callback | Description |
|---|---|
| `load(query, callback)` | Load remote data. Call `callback(data)` with results or `callback()` on error |
| `shouldLoad(query)` | Validate input before `load()` fires. Return `false` to skip |
| `score(search)` | Override scoring. Return a function that scores each option |
| `onInitialize()` | Control fully initialized |
| `onFocus()` | Control gained focus |
| `onBlur()` | Control lost focus |
| `onChange(value)` | Value changed |
| `onItemAdd(value, $item)` | Item selected |
| `onItemRemove(value, $item)` | Item deselected |
| `onClear()` | Control cleared via `clear()` |
| `onDelete(values, event)` | User attempts to delete selection. Return `false` to prevent |
| `onOptionAdd(value, data)` | New option added to list |
| `onOptionRemove(value)` | Option removed from list |
| `onDropdownOpen(dropdown)` | Dropdown opened |
| `onDropdownClose(dropdown)` | Dropdown closed |
| `onType(str)` | User typed while filtering |
| `onLoad(options, optgroups)` | Remote data loaded and added |

---

## Render Templates

Customize HTML for every part of Tom Select. Each template is a `function(data, escape)` returning a `NodeDefinition`.

```js
new TomSelect('#input', {
  optionClass: 'option',
  itemClass: 'item',
  render: {
    option: function(data, escape) {
      return '<div>' + escape(data.text) + '</div>';
    },
    item: function(data, escape) {
      return '<div>' + escape(data.text) + '</div>';
    },
    option_create: function(data, escape) {
      return '<div class="create">Add <strong>' + escape(data.input) + '</strong>&hellip;</div>';
    },
    no_results: function(data, escape) {
      return '<div class="no-results">No results found for "' + escape(data.input) + '"</div>';
    },
    not_loading: function(data, escape) {
      // No default content
    },
    optgroup: function(data) {
      let optgroup = document.createElement('div');
      optgroup.className = 'optgroup';
      optgroup.appendChild(data.options);
      return optgroup;
    },
    optgroup_header: function(data, escape) {
      return '<div class="optgroup-header">' + escape(data.label) + '</div>';
    },
    loading: function(data, escape) {
      return '<div class="spinner"></div>';
    },
    dropdown: function() {
      return '<div></div>';
    }
  }
});
```

### Render Templates Table

| Template | Description |
|---|---|
| `render.option` | An option in the dropdown list |
| `render.item` | A selected item (tag) |
| `render.option_create` | The "create new" option at bottom. Data includes `input` (user's typed text) |
| `render.optgroup_header` | Header of an option group |
| `render.optgroup` | Wrapper for an optgroup. Data has `html` (raw HTML of header + options) |
| `render.no_results` | Displayed when no options match. Set to `null` to disable |
| `render.not_loading` | Content shown when `shouldLoad` returns `false` |
| `render.loading` | Displayed during `load()` |
| `render.dropdown` | Where dropdown content is displayed |

---

## Events API

Tom Select instances have an event emitter interface: `.on()`, `.off()`, `.trigger()`.

```js
var select = new TomSelect('#input-id');
select.on('item_add', function(value, item) {
  console.log('Added:', value);
});
select.off('item_add');
```

### Available Events

| Event | Params | Description |
|---|---|---|
| `"initialize"` | — | Control fully initialized |
| `"change"` | `value` | Value changed |
| `"focus"` | — | Control gained focus |
| `"blur"` | — | Control lost focus |
| `"item_add"` | `value`, `item` | Option selected |
| `"item_remove"` | `value`, `$item` | Item deselected |
| `"item_select"` | `item` | Item highlighted/selected in dropdown |
| `"clear"` | — | Control cleared via `clear()` |
| `"option_add"` | `value`, `data` | New option added |
| `"option_remove"` | `value` | Option removed |
| `"option_clear"` | — | All options removed |
| `"optgroup_add"` | `id`, `data` | Optgroup added |
| `"optgroup_remove"` | `id` | Optgroup removed |
| `"optgroup_clear"` | — | All optgroups removed |
| `"dropdown_open"` | `dropdown` | Dropdown opened |
| `"dropdown_close"` | `dropdown` | Dropdown closed |
| `"type"` | `str` | User typed while filtering |
| `"load"` | `data` | New options loaded (remote) |
| `"destroy"` | — | Control is about to be destroyed |

---

## API Methods

### Accessing an Existing Instance

```js
var control = document.getElementById('select').tomselect;
```

### Option Methods

| Method | Description |
|---|---|
| `addOption(data, user_created=false)` | Add an available option (doesn't refresh dropdown) |
| `addOptions(data[], user_created=false)` | Add multiple options |
| `updateOption(value, data)` | Update an existing option |
| `removeOption(value)` | Remove an option |
| `getOption(value, create=false)` | Get option's DOM element |
| `getAdjacent(element, direction)` | Get previous (-1) or next (1) option relative to highlighted |
| `refreshOptions(triggerDropdown)` | Refresh dropdown options list |
| `clearOptions(clearFilter?)` | Remove all unselected options |
| `clearFilter(option, value)` | Callback for `clearOptions()` — return `true` to keep |

### Item Methods

| Method | Description |
|---|---|
| `clear(silent)` | Clear all selected items |
| `getItem(value)` | Get item's DOM element |
| `addItem(value, silent)` | Select an item |
| `removeItem(value, silent)` | Deselect an item |
| `createItem(value, callback)` | Invoke the `create` method and add result |
| `refreshItems()` | Re-render selected items |

### Optgroup Methods

| Method | Description |
|---|---|
| `addOptionGroup(id, data)` | Register a new optgroup |
| `removeOptionGroup(id)` | Remove an optgroup |
| `clearOptionGroups()` | Remove all optgroups |

### Dropdown & Control Methods

| Method | Description |
|---|---|
| `open()` | Open the dropdown |
| `close()` | Close the dropdown |
| `positionDropdown()` | Recalculate dropdown position |
| `focus()` | Focus the control |
| `blur()` | Blur the control |
| `lock()` | Disable user input (still focusable) |
| `unlock()` | Re-enable user input |
| `disable()` | Fully disable control (can't focus) |
| `enable()` | Enable control |
| `getValue()` | Get current value (string or array) |
| `setValue(value, silent)` | Set selected items |
| `setCaret(index)` | Move caret to position in selected items |
| `isFull()` | Check if max items reached |
| `clearCache()` | Clear cached option renderings |
| `setTextboxValue(str)` | Set input field value |
| `sync()` | Sync with underlying `<select>` or `<input>` |
| `load(query)` | Initiate remote loading |
| `destroy()` | Destroy control and unbind events |

---

## Examples

### Single select (mono-selection)

```html
<select id="single-select" placeholder="Pick one..." autocomplete="off">
  <option value="">Pick one...</option>
  <option value="1">Option 1</option>
  <option value="2">Option 2</option>
</select>
<script>
  new TomSelect('#single-select', { maxItems: 1 });
</script>
```

### Multi-select with max limit

```html
<select id="multi-select" name="state[]" multiple placeholder="Select states..." autocomplete="off">
  <option value="" selected>California</option>
  <option value="CO">Colorado</option>
</select>
<script>
  new TomSelect('#multi-select', { maxItems: 3 });
</script>
```

### Tag input with creation

```html
<input id="tags" value="awesome,neat" autocomplete="off" placeholder="Add tags...">
<script>
  new TomSelect('#tags', {
    persist: false,
    createOnBlur: true,
    create: true,
  });
</script>
```

### Remote search with minimum query length

```js
new TomSelect('#remote-select', {
  valueField: 'id',
  labelField: 'name',
  searchField: ['name', 'email'],
  preload: 'focus',
  shouldLoad: function(query) { return query.length >= 2; },
  load: function(query, callback) {
    fetch('/api/users?q=' + encodeURIComponent(query))
      .then(r => r.json())
      .then(data => callback(data))
      .catch(() => callback());
  },
  render: {
    option: function(data, escape) {
      return '<div>' + escape(data.name) + ' <small>' + escape(data.email) + '</small></div>';
    }
  }
});
```

### With remove_button + clear_button plugins

```js
new TomSelect('#select', {
  plugins: {
    remove_button: { title: 'Remove this item' },
    clear_button: { title: 'Remove all selected options' },
  },
  persist: false,
  create: true,
});
```

### With dropdown_header plugin

```js
new TomSelect('#select', {
  sortField: 'text',
  plugins: {
    dropdown_header: { title: 'Language' }
  }
});
```

### Programmatic control

```js
var tom = new TomSelect('#select');
tom.addOption({ value: 'new', text: 'New Option' });
tom.addItem('new');
tom.disable();
// Later...
tom.enable();
console.log(tom.getValue());
tom.destroy();
```

---

## Integration with HTMX

When Tom Select is used inside HTMX-partial-rendered content, re-initialize Tom Select after the swap. Use HTMX's `htmx:afterSwap` event or `hx-trigger` with `revealed` / `intersect` to handle dynamic content.

```html
<input id="dynamic-select" name="category" />

<script>
  document.addEventListener('htmx:afterSwap', function(evt) {
    if (evt.target.querySelector('#dynamic-select')) {
      new TomSelect('#dynamic-select', { create: true });
    }
  });
</script>
```

When Tom Select's value should trigger an HTMX request, listen for the `change` event:

```js
var select = new TomSelect('#filter-select');
select.on('change', function(value) {
  htmx.trigger('#filter-select', 'change');
});
```

---

## Styling

Tom Select ships with default themes:
- `tom-select.css` / `tom-select.default.css`
- `tom-select.bootstrap4.css` / `tom-select.bootstrap5.css`

The SCSS sources are available in `dist/scss/` for custom builds using SASS variables.

**Key CSS classes for custom styling:**

| Class | Element |
|---|---|
| `.ts-wrapper` | Outer wrapper |
| `.ts-control` | The control container (input area) |
| `.ts-control .item` | Selected items (tags) |
| `.ts-control input` | The search input |
| `.ts-dropdown` | The dropdown container |
| `.ts-dropdown .option` | Dropdown options |
| `.ts-dropdown .option.active` | Highlighted option |
| `.ts-dropdown .optgroup-header` | Optgroup header |
| `.ts-wrapper.multi` | Multi-select mode wrapper |
| `.ts-wrapper.single` | Single-select mode wrapper |
| `.ts-wrapper.disabled` | Disabled state |
| `.ts-wrapper.focus` | Focused state |
