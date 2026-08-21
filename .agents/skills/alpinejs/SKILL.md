---
name: alpinejs
description: Reference for building Alpine.js UIs. Use whenever writing or reviewing HTML that uses x-data, x-show, x-model, x-on/@, x-bind/:, x-for, x-ref, x-transition, x-trap, x-collapse, or any Alpine magic ($dispatch, $watch, $store, $nextTick, $persist, $refs). Also triggers for questions about Alpine plugins (Focus/Trap, Persist, Collapse, Intersect, Mask, Morph, Sort, Anchor, Resize), event modifiers, reactivity, reusable components via Alpine.data(), global state via Alpine.store(), integrating Alpine with HTMX, FastAPI, Jinja2, or DaisyUI. Make sure to use this skill whenever Alpine.js attributes, directives, or patterns are involved.
---

# Alpine.js Reference Skill

Alpine.js v3 is a lightweight JavaScript framework for sprinkling interactivity into server-rendered HTML. It uses reactive data declared directly in HTML attributes — no build step required.

## Reference Files

Load these on demand when you need depth beyond what's here:

| File | When to load |
|---|---|
| `references/directives.md` | Deep dive on specific directives: `x-bind` class/style syntax, `x-model` input types + modifiers, `x-transition` CSS classes, `x-for` keys/indexes, `x-teleport`, `x-modelable`, `x-id` |
| `references/magics-globals.md` | `$watch` deep watching, `Alpine.data()` init params + lifecycle hooks, `Alpine.store()`, `Alpine.bind()`, `$dispatch`, `$id` |
| `references/plugins.md` | Focus/Trap, Persist, Collapse, Intersect, Mask, Resize — CDN install + usage for all plugins |
| `references/patterns.md` | Reusable components, cross-component comms, HTMX+Alpine integration, `x-cloak` FOUC prevention |

## Installation

```html
<!-- CDN (preferred — add to base template <head>) -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

`defer` is required — Alpine initializes after the DOM is parsed.

**With plugins** — load plugin scripts before Alpine core:

```html
<!-- Plugin first, then Alpine -->
<script defer src="https://cdn.jsdelivr.net/npm/@alpinejs/focus@3.x.x/dist/cdn.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.x.x/dist/cdn.min.js"></script>
```

## x-data — Component Scope

Declares a reactive data object. All directives inside the element have access to these properties. Every property change automatically updates the DOM.

```html
<div x-data="{ count: 0, open: false }">
    <!-- directives here can read/write count and open -->
</div>
```

**Computed properties** use JS getters — they re-evaluate whenever their dependencies change:

```html
<div x-data="{
    search: '',
    items: ['foo', 'bar', 'baz'],
    get filtered() {
        return this.items.filter(i => i.includes(this.search))
    }
}">
```

**Reusable components** — register with `Alpine.data()` (read `references/magics-globals.md` for full details):

```html
<div x-data="dropdown">...</div>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', () => ({
        open: false,
        toggle() { this.open = !this.open }
    }))
})
</script>
```

## x-show / x-if — Visibility

`x-show` toggles `display:none` — element stays in DOM, Alpine state is preserved:

```html
<div x-show="open">Visible when open is truthy</div>
```

`x-if` adds/removes the element from the DOM entirely — must be on a `<template>` tag:

```html
<template x-if="open">
    <div>Only exists in DOM when open is true</div>
</template>
```

**Prefer `x-show`** for elements that toggle frequently (cheaper). Use `x-if` when the element is expensive to render or when you want lifecycle cleanup.

## x-bind / : — Attribute Binding

Dynamically set any HTML attribute. `:` is the shorthand for `x-bind:`.

```html
<input :placeholder="placeholderText">
<button :disabled="isLoading">Submit</button>
<a :href="'/items/' + item.id" x-text="item.name"></a>
```

**Class binding** — object syntax merges with existing classes (safe to use alongside static `class="..."`):

```html
<div class="btn" :class="{ 'btn-primary': active, 'btn-disabled': disabled }">
```

**Style binding** — object syntax:

```html
<div :style="{ color: textColor, fontSize: size + 'px' }">
```

## x-on / @ — Events

Listen for any DOM event. `@` is the shorthand.

```html
<button @click="count++">Increment</button>
<input @keyup.enter="submit()">
<div @click.outside="close()">Dropdown</div>
```

**Key modifiers for keyboard events:** `.enter` `.escape` `.tab` `.space` `.up` `.down` `.left` `.right` `.shift` `.ctrl` `.cmd` `.alt` `.caps-lock` — chain for combos: `@keyup.shift.enter`

**Essential event modifiers:**

| Modifier | Effect |
|---|---|
| `.prevent` | `event.preventDefault()` |
| `.stop` | `event.stopPropagation()` |
| `.outside` | Only fires when click is outside the element |
| `.window` | Listens on `window` instead of the element |
| `.document` | Listens on `document` |
| `.once` | Handler fires once, then is removed |
| `.debounce` | Debounce 250ms (customize: `.debounce.500ms`) |
| `.throttle` | Throttle 250ms (customize: `.throttle.1s`) |
| `.self` | Only fires if the event originated on this element, not a child |
| `.passive` | Marks listener passive (improves scroll performance for touch events) |
| `.capture` | Listen in capture phase |
| `.camel` | Listen for camelCase event name (`@custom-event.camel` → `customEvent`) |

**Access the native event object** via `$event`:

```html
<input @change="handleChange($event)">
```

## x-text / x-html — Content

```html
<span x-text="message"></span>          <!-- sets textContent -->
<div x-html="trustedHtml"></div>        <!-- sets innerHTML — only use with trusted content -->
```

## x-model — Two-Way Binding

Syncs an input's value with a data property.

```html
<input type="text"     x-model="name">
<input type="checkbox" x-model="agreed">           <!-- boolean -->
<input type="checkbox" value="red" x-model="colors"> <!-- array when multiple -->
<input type="radio"    value="yes" x-model="answer">
<select x-model="selected"><option>A</option></select>
<textarea x-model="message"></textarea>
```

**Modifiers:** `.lazy` (sync on `change` not `input`) · `.number` (coerce to number) · `.boolean` (coerce to boolean) · `.debounce.500ms` · `.throttle`

## x-for — Loops

Must be on a `<template>` element with exactly one child. Use `:key` for stable identity when items reorder.

```html
<template x-for="item in items" :key="item.id">
    <li x-text="item.name"></li>
</template>

<!-- With index -->
<template x-for="(item, index) in items" :key="item.id">
    <li><span x-text="index + 1"></span>. <span x-text="item.name"></span></li>
</template>

<!-- Range loop -->
<template x-for="i in 5">
    <span x-text="i"></span>
</template>
```

## x-init — Initialization

Runs a JS expression when the component initializes. Useful for fetching initial data.

```html
<div x-data="{ users: [] }" x-init="users = await (await fetch('/api/users')).json()">
```

When using `Alpine.data()`, define an `init()` method instead — Alpine calls it automatically.

## x-ref — DOM References

Store a reference to a DOM element, accessible via `$refs`.

```html
<input x-ref="searchInput" type="text">
<button @click="$refs.searchInput.focus()">Focus</button>
```

## x-cloak — Prevent Flash of Unstyled Content

Hide elements until Alpine has initialized. Add the CSS rule to your base template `<head>`:

```html
<style>[x-cloak] { display: none !important; }</style>
```

```html
<!-- Hidden until Alpine runs, then x-cloak is removed -->
<div x-cloak x-data="{ open: false }" x-show="open">...</div>
```

## x-transition — Animations

Add to any element that uses `x-show`. The default is a smooth fade+scale:

```html
<div x-show="open" x-transition>...</div>
```

**Customize duration/delay:**

```html
<div x-show="open" x-transition.duration.300ms>...</div>
<div x-show="open" x-transition:enter.duration.300ms x-transition:leave.duration.150ms>...</div>
```

**CSS class approach** (for full Tailwind control — see `references/directives.md` for full details):

```html
<div x-show="open"
     x-transition:enter="transition ease-out duration-300"
     x-transition:enter-start="opacity-0 scale-95"
     x-transition:enter-end="opacity-100 scale-100"
     x-transition:leave="transition ease-in duration-200"
     x-transition:leave-start="opacity-100 scale-100"
     x-transition:leave-end="opacity-0 scale-95">
```

## x-effect — Reactive Side Effects

Re-runs whenever any reactive data it reads changes:

```html
<div x-data="{ count: 0 }" x-effect="console.log('count is:', count)">
```

## Magic Properties — Quick Reference

| Magic | What it gives you |
|---|---|
| `$el` | The current DOM element |
| `$refs` | Object of elements marked with `x-ref` |
| `$data` | The component's data object |
| `$root` | The root `x-data` element |
| `$store.name` | Read/write global store (see below) |
| `$watch('prop', cb)` | Watch a data property for changes |
| `$dispatch('event', detail)` | Fire a bubbling custom DOM event |
| `$nextTick(cb)` | Run after Alpine finishes updating the DOM |
| `$id('name')` | Generate a unique scoped ID (use with `x-id`) |

**`$dispatch`** — fire custom events that bubble up the DOM:

```html
<button @click="$dispatch('item-selected', { id: item.id })">Select</button>

<!-- Parent listens -->
<div @item-selected="selectedId = $event.detail.id">
```

**`$store`** — access global state registered with `Alpine.store()`:

```html
<button @click="$store.cart.add(item)">Add to Cart</button>
<span x-text="$store.cart.count"></span>
```

**`$watch`** — react to property changes:

```html
<div x-data="{ open: false }" x-init="$watch('open', val => val && loadData())">
```

**`$nextTick`** — run code after the DOM updates:

```html
<button @click="open = true; $nextTick(() => $refs.input.focus())">Open & Focus</button>
```

## Global APIs — Quick Reference

**`Alpine.store(name, obj)`** — global reactive state, accessible via `$store.name`:

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.store('theme', {
        dark: false,
        toggle() { this.dark = !this.dark }
    })
})
```

**`Alpine.data(name, factory)`** — register a reusable component (supports `init()` / `destroy()` lifecycle, initial parameters, magic access via `this.$watch`):

```javascript
Alpine.data('modal', (initialOpen = false) => ({
    open: initialOpen,
    init() { this.$watch('open', val => document.body.classList.toggle('overflow-hidden', val)) },
    destroy() { document.body.classList.remove('overflow-hidden') }
}))
```

```html
<div x-data="modal(true)">...</div>
```

**`Alpine.bind(name, attrs)`** — reusable attribute sets (see `references/magics-globals.md`).
