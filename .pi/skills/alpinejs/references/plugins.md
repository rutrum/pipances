# Alpine.js Plugins Reference

All plugins must be loaded **before** Alpine core in the `<head>`. They extend Alpine with new directives and magic properties.

```html
<!-- Plugin scripts FIRST, then Alpine -->
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

## Focus — `x-trap` (Most Commonly Needed)

Traps keyboard focus inside a modal/dialog until the condition becomes false. Essential for accessible dialogs.

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
```

**Basic usage:**

```html
<div x-data="{ open: false }">
    <button @click="open = true">Open Dialog</button>

    <div x-show="open" x-trap="open">
        <p>Focus is trapped here while open.</p>
        <input type="text" placeholder="Tab cycles within...">
        <button @click="open = false">Close</button>
    </div>
</div>
```

When `open` becomes `false`, focus returns to where it was before trapping began. Supports nested dialogs — each `x-trap` stacks correctly.

**Modifiers:**

```html
<!-- .inert: hide all other page content from screen readers while trapped -->
<div x-show="open" x-trap.inert="open">...</div>

<!-- .noscroll: prevent page from scrolling while focus is trapped -->
<div x-show="open" x-trap.noscroll="open">...</div>

<!-- .noreturn: don't return focus to previous element when untrapped -->
<div x-show="open" x-trap.noreturn="open">...</div>
```

## Persist — `$persist`

Persists reactive data to `localStorage` so it survives page refreshes.

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/persist@3.x.x/dist/cdn.min.js"></script>
```

**Basic usage** — wrap any value in `$persist()`:

```html
<div x-data="{ count: $persist(0) }">
    <button @click="count++">Increment</button>
    <span x-text="count"></span>
    <!-- count survives page refresh -->
</div>
```

**Custom localStorage key** (default key is derived from property name):

```html
<div x-data="{ count: $persist(0).as('my-counter') }">
```

**Use sessionStorage** instead (clears when tab closes):

```html
<div x-data="{ token: $persist('').using(sessionStorage) }">
```

**Inside Alpine.data()** — must use regular function, not arrow function:

```javascript
Alpine.data('settings', function() {
    return {
        darkMode: this.$persist(false).as('theme-dark')
    }
})
```

**In Alpine.store():**

```javascript
Alpine.store('prefs', {
    darkMode: Alpine.$persist(false).as('dark-mode')
})
```

## Collapse — `x-collapse`

Animates an element's height smoothly when toggled with `x-show`. Much smoother than `x-transition` for variable-height content like accordions.

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/collapse@3.x.x/dist/cdn.min.js"></script>
```

**Usage** — add `x-collapse` alongside `x-show`:

```html
<div x-data="{ expanded: false }">
    <button @click="expanded = !expanded">Toggle</button>
    <div x-show="expanded" x-collapse>
        Long content that animates its height...
    </div>
</div>
```

**Modifiers:**

```html
<!-- Custom animation duration -->
<div x-show="expanded" x-collapse.duration.500ms>

<!-- Minimum height when collapsed (peeks content instead of fully hiding) -->
<div x-show="expanded" x-collapse.min.50px>
```

Accordion pattern with DaisyUI:

```html
<div x-data="{ active: null }">
    <template x-for="(item, i) in items" :key="i">
        <div class="collapse">
            <button class="collapse-title" @click="active = active === i ? null : i"
                    x-text="item.title"></button>
            <div x-show="active === i" x-collapse class="collapse-content"
                 x-text="item.body"></div>
        </div>
    </template>
</div>
```

## Intersect — `x-intersect`

Runs expressions when an element enters or leaves the browser viewport, using `IntersectionObserver`.

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/intersect@3.x.x/dist/cdn.min.js"></script>
```

**Basic usage:**

```html
<!-- Fire when element enters viewport -->
<div x-intersect="loadMoreItems()">Load trigger</div>

<!-- Fire on enter AND leave -->
<div x-intersect:enter="visible = true" x-intersect:leave="visible = false">
    <span x-show="visible">I'm visible!</span>
</div>
```

**Modifiers:**

```html
<!-- .once: only fire the first time the element enters -->
<div x-intersect.once="trackImpression()">Ad unit</div>

<!-- .half: fire when 50% of the element is visible -->
<div x-intersect.half="animate = true">

<!-- .full: fire only when fully visible -->
<div x-intersect.full="fullyVisible = true">

<!-- .threshold-N: custom threshold (0-100) — .threshold-50 = 50% -->
<div x-intersect.threshold-75="mostlyVisible = true">

<!-- .margin: expand/contract the root margin -->
<div x-intersect.margin.200px="nearViewport = true">
```

Lazy-loading pattern:

```html
<img x-data="{ src: null }"
     x-intersect.once="src = $el.dataset.src"
     :src="src"
     data-src="/heavy-image.jpg"
     alt="Lazy loaded image">
```

## Mask — `x-mask`

Formats an input value as the user types (phone numbers, dates, credit cards, etc.).

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/mask@3.x.x/dist/cdn.min.js"></script>
```

**Static mask** — `9` matches a digit, `a` matches a letter, `*` matches any character:

```html
<input x-mask="(999) 999-9999" placeholder="(555) 555-5555">
<input x-mask="99/99/9999" placeholder="MM/DD/YYYY">
<input x-mask="9999 9999 9999 9999" placeholder="Card number">
```

**Dynamic mask** — function that returns a mask based on the current value:

```html
<input x-mask:dynamic="$input.startsWith('4') ? '9999 9999 9999 9999' : '9999 999999 99999'">
```

## Resize — `x-resize`

Calls an expression whenever the element's size changes, using `ResizeObserver`. Receives `width` and `height` via `$width` and `$height`.

**CDN:**

```html
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/resize@3.x.x/dist/cdn.min.js"></script>
```

```html
<div x-data="{ w: 0, h: 0 }"
     x-resize="w = $width; h = $height">
    Size: <span x-text="w + 'x' + h"></span>
</div>
```

Modifier `.document` observes the document element (window resize):

```html
<div x-resize.document="isWide = $width > 1024">
```

## Other Plugins — Overview

These plugins are available but less commonly needed in typical HTMX+Alpine projects:

| Plugin | What it does | CDN package |
|---|---|---|
| **Anchor** | Positions an element relative to another (like Popper.js / Floating UI). Useful for tooltips and dropdowns that need smart placement. Use `x-anchor` directive. | `@alpinejs/anchor` |
| **Morph** | Intelligently patches a DOM tree to match new HTML, preserving focus and input state. Useful when Alpine state must survive a server-pushed update. | `@alpinejs/morph` |
| **Sort** | Drag-and-drop list sorting via `x-sort` directive. Provides `$item` and `$position` callbacks. | `@alpinejs/sort` |

For full documentation on these, visit https://alpinejs.dev/plugins/anchor, /morph, /sort.
