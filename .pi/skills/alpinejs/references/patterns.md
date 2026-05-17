# Alpine.js Patterns

Common patterns for Alpine.js in a FastAPI + HTMX + Jinja2 + DaisyUI project.

## FOUC Prevention with x-cloak

Without `x-cloak`, elements with `x-show="false"` flash visible before Alpine initializes.

Add to your base template `<head>` (once, globally):

```html
<style>[x-cloak] { display: none !important; }</style>
```

Then add `x-cloak` to any element that should be hidden by default:

```html
<div x-cloak x-show="open">This won't flash on load</div>
```

Also useful for the entire component when it should be invisible until Alpine is ready:

```html
<nav x-cloak x-data="{ mobileOpen: false }">
    <div x-show="mobileOpen">Mobile menu</div>
</nav>
```

## Dropdown / Menu

```html
<div x-data="{ open: false }" class="dropdown">
    <button @click="open = !open" class="btn">
        Options
        <svg :class="{ 'rotate-180': open }" class="w-4 h-4 transition-transform">...</svg>
    </button>
    <ul x-show="open"
        x-transition
        @click.outside="open = false"
        class="dropdown-content menu">
        <li><a>Action 1</a></li>
        <li><a>Action 2</a></li>
    </ul>
</div>
```

## Modal Dialog

Combines `x-trap` (Focus plugin), `x-teleport`, and a DaisyUI modal:

```html
<div x-data="{ open: false }">
    <button @click="open = true" class="btn btn-primary">Open Modal</button>

    <template x-teleport="body">
        <div x-show="open"
             x-trap.inert.noscroll="open"
             @keydown.escape="open = false"
             class="modal modal-open">
            <div class="modal-box" @click.stop>
                <h3 class="font-bold text-lg">Title</h3>
                <p>Content goes here.</p>
                <div class="modal-action">
                    <button @click="open = false" class="btn">Close</button>
                </div>
            </div>
            <!-- Click backdrop to close -->
            <div class="modal-backdrop" @click="open = false"></div>
        </div>
    </template>
</div>
```

## Tabs

```html
<div x-data="{ tab: 'overview' }">
    <div role="tablist" class="tabs tabs-bordered">
        <button role="tab"
                @click="tab = 'overview'"
                :class="{ 'tab-active': tab === 'overview' }"
                class="tab">Overview</button>
        <button role="tab"
                @click="tab = 'details'"
                :class="{ 'tab-active': tab === 'details' }"
                class="tab">Details</button>
    </div>

    <div x-show="tab === 'overview'" x-transition>
        Overview content
    </div>
    <div x-show="tab === 'details'" x-transition>
        Details content
    </div>
</div>
```

For tabs that load content from the server, combine with HTMX — see the HTMX+Alpine section below.

## Toast Notifications (Global)

A page-level toast system using `Alpine.store()` and `$dispatch`:

```html
<!-- In base.html — persistent toast container -->
<div x-data
     @toast.window="
         $store.toasts.add($event.detail);
         setTimeout(() => $store.toasts.remove($event.detail.id), $event.detail.duration ?? 3000)
     "
     class="toast toast-end z-50">
    <template x-for="t in $store.toasts.list" :key="t.id">
        <div class="alert" :class="'alert-' + t.level">
            <span x-text="t.message"></span>
        </div>
    </template>
</div>
```

```javascript
// In base.html <script> or a separate JS file loaded once
document.addEventListener('alpine:init', () => {
    Alpine.store('toasts', {
        list: [],
        _id: 0,
        add(toast) {
            this.list.push({ id: ++this._id, level: 'info', ...toast })
        },
        remove(id) {
            this.list = this.list.filter(t => t.id !== id)
        }
    })
})
```

**Dispatch a toast from anywhere on the page:**

```html
<!-- From Alpine -->
<button @click="$dispatch('toast', { message: 'Saved!', level: 'success' })">Save</button>
```

```python
# From HTMX response header (server-side)
return HTMLResponse(content, headers={
    "HX-Trigger": json.dumps({"toast": {"message": "Saved!", "level": "success"}})
})
```

## Accordion

```html
<div x-data="{ active: null }" class="space-y-2">
    <template x-for="(item, i) in items" :key="i">
        <div class="collapse collapse-arrow bg-base-200">
            <button class="collapse-title text-xl font-medium"
                    @click="active = active === i ? null : i"
                    x-text="item.title">
            </button>
            <div class="collapse-content" x-show="active === i" x-collapse>
                <p x-text="item.body"></p>
            </div>
        </div>
    </template>
</div>
```

## Inline Edit (Alpine-only, no server round-trip)

```html
<div x-data="{ editing: false, value: '{{ item.name }}', original: '{{ item.name }}' }">
    <span x-show="!editing"
          @dblclick="editing = true; $nextTick(() => $refs.input.select())"
          x-text="value"
          class="cursor-pointer">
    </span>

    <input x-show="editing"
           x-ref="input"
           x-model="value"
           @keyup.enter="editing = false"
           @keyup.escape="value = original; editing = false"
           @blur="editing = false"
           class="input input-bordered input-sm">
</div>
```

For inline edits that need server persistence, use the HTMX inline editing pattern and let HTMX handle the PATCH request.

## Dark Mode Toggle

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.store('theme', {
        dark: Alpine.$persist(
            window.matchMedia('(prefers-color-scheme: dark)').matches
        ).as('theme-dark'),
        toggle() { this.dark = !this.dark }
    })
})
```

```html
<html x-data :data-theme="$store.theme.dark ? 'dark' : 'light'">
<head>...</head>
<body>
    <button @click="$store.theme.toggle()" class="btn btn-ghost">
        <span x-text="$store.theme.dark ? '☀️' : '🌙'"></span>
    </button>
</body>
```

## Reusable Components with Alpine.data()

Extract complex logic so templates stay clean:

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.data('combobox', (options = []) => ({
        options,
        query: '',
        open: false,
        selected: null,

        get filtered() {
            return this.options.filter(o =>
                o.label.toLowerCase().includes(this.query.toLowerCase())
            )
        },

        select(option) {
            this.selected = option
            this.query = option.label
            this.open = false
        },

        init() {
            this.$watch('query', q => { this.open = q.length > 0 })
        }
    }))
})
```

```html
<div x-data="combobox([{ label: 'Apple', value: 'apple' }, { label: 'Banana', value: 'banana' }])">
    <input x-model="query" @focus="open = true" @click.outside="open = false" class="input">
    <ul x-show="open" class="dropdown-content menu">
        <template x-for="option in filtered" :key="option.value">
            <li><button @click="select(option)" x-text="option.label"></button></li>
        </template>
    </ul>
</div>
```

## Cross-Component Communication

**Via `$dispatch`** (child → parent/ancestor, bubbles up):

```html
<div @user-selected="selectedUserId = $event.detail.id">
    <!-- deep child -->
    <button @click="$dispatch('user-selected', { id: user.id })">Select</button>
</div>
```

**Via `.window`** (truly global, any component to any component):

```html
<button @click="$dispatch('sidebar:toggle')">Toggle Sidebar</button>

<aside @sidebar:toggle.window="open = !open" x-data="{ open: true }" x-show="open">
```

**Via `Alpine.store()`** (shared mutable state):

```html
<!-- Component A writes -->
<button @click="$store.filters.status = 'active'">Show Active</button>

<!-- Component B reads reactively -->
<div x-text="$store.filters.status"></div>
```

## HTMX + Alpine.js Integration

HTMX and Alpine complement each other naturally: **HTMX handles server communication**, **Alpine handles local UI state**.

### Division of Responsibility

```
HTMX  → server requests, HTML swaps, history, form submission, pagination
Alpine → dropdowns, modals, tabs, toggles, transient UI state, animations
```

If it needs a round trip to the server → HTMX. If it's purely visual → Alpine.

### Initializing Alpine on HTMX-Swapped Content

Alpine automatically watches for new DOM nodes via `MutationObserver` — no setup needed. Components in HTMX-swapped partials initialize automatically. Just make sure `[x-cloak]` CSS is in the main page `<head>`, not in the partial.

### Passing Server Data to Alpine State

Render initial state server-side with Jinja2 `tojson`:

```html
<div x-data="{ items: {{ items | tojson }}, selected: null }">
    <template x-for="item in items" :key="item.id">
        <div @click="selected = item.id"
             :class="{ 'bg-primary text-primary-content': selected === item.id }">
            <span x-text="item.name"></span>
        </div>
    </template>
</div>
```

For updates, let HTMX swap in a new partial with fresh `x-data` rather than trying to mutate Alpine state from the server.

### Reacting to HTMX Lifecycle Events in Alpine

HTMX fires DOM events — Alpine's `@` can catch them:

```html
<form x-data="{ loading: false }"
      @htmx:before-request="loading = true"
      @htmx:after-request="loading = false"
      hx-post="/submit"
      hx-target="#result">
    <button :disabled="loading" class="btn btn-primary">
        <span x-show="loading" class="loading loading-spinner loading-xs"></span>
        Submit
    </button>
</form>
```

Common HTMX events usable in Alpine:

| Event | When it fires |
|---|---|
| `htmx:before-request` | Just before a request is sent |
| `htmx:after-request` | After response is received |
| `htmx:after-swap` | After HTML has been swapped into DOM |
| `htmx:before-swap` | Before swap — can inspect/modify response |

### Triggering HTMX from Alpine

Use `htmx.trigger()` to programmatically fire an htmx element:

```html
<div x-data="{ confirmed: false }">
    <button @click="if (confirm('Delete?')) htmx.trigger($refs.deleteBtn, 'confirmed')">
        Delete
    </button>
    <button x-ref="deleteBtn"
            hx-delete="/item/{{ item.id }}"
            hx-trigger="confirmed"
            hx-target="closest tr"
            hx-swap="outerHTML"
            class="hidden">
    </button>
</div>
```

### HTMX Response Header → Alpine Event

The server can trigger Alpine events via `HX-Trigger` response header:

```python
import json

return HTMLResponse(content, headers={
    "HX-Trigger": json.dumps({"toast": {"message": "Item saved!", "level": "success"}})
})
```

HTMX fires the event on the element. To catch it globally in Alpine, use `.window`:

```html
<!-- Note: camelCase "showToast" becomes kebab-case "show-toast" in Alpine -->
<div @toast.window="$store.toasts.add($event.detail)">
```

### Alpine `$dispatch` → HTMX Trigger

Alpine's `$dispatch` fires real DOM events — HTMX can listen with `hx-trigger`:

```html
<div x-data
     hx-get="/data"
     hx-trigger="refresh-needed"
     hx-target="#data-table">
</div>

<!-- Anywhere on page, e.g. after user makes a change -->
<button @click="$dispatch('refresh-needed')">Refresh</button>
```

### Preserving Alpine State Across Swaps (Idiomorph)

Normal HTMX swaps destroy and recreate DOM nodes, resetting Alpine state. Use the Idiomorph morph extension to patch the DOM in-place instead:

```html
<body hx-ext="morph">
    <div x-data="{ count: 0 }">
        <button @click="count++">+</button>
        <span x-text="count"></span>
        <!-- Morph swap: DOM patched in-place, count preserved -->
        <div hx-get="/refresh" hx-swap="morph:innerHTML" hx-trigger="every 10s">
            <!-- server-rendered content -->
        </div>
    </div>
</body>
```

### Inline Script in HTMX Partials

For behavior that can't be expressed with Alpine attributes, add a self-contained IIFE to the partial. Bridge back to HTMX by triggering clicks on elements with `hx-*` attributes rather than making fetch calls directly from JS.

```html
<!-- _search_results.html -->
<ul id="results" role="listbox">
    {% for item in items %}
    <li role="option"
        tabindex="-1"
        hx-get="/select/{{ item.id }}"
        hx-target="#selected-area"
        class="cursor-pointer hover:bg-base-200 p-2">
        {{ item.name }}
    </li>
    {% endfor %}
</ul>

<script>
(function() {
    const list = document.getElementById('results');
    if (!list) return;
    list.addEventListener('keydown', function(e) {
        const items = Array.from(list.querySelectorAll('[role=option]'));
        const idx = items.indexOf(document.activeElement);
        if (e.key === 'ArrowDown') { e.preventDefault(); items[Math.min(idx + 1, items.length - 1)]?.focus(); }
        if (e.key === 'ArrowUp')   { e.preventDefault(); items[Math.max(idx - 1, 0)]?.focus(); }
        if (e.key === 'Enter')     { document.activeElement?.click(); }
    });
})();
</script>
```
