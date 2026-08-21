# Alpine.js Magics & Global APIs — Deep Reference

## $watch — Watching Data Properties

Watch a single property and run a callback when it changes:

```javascript
// Inside x-init or an Alpine.data() init() method
this.$watch('open', value => {
    document.body.style.overflow = value ? 'hidden' : ''
})
```

**Deep watching** (objects and arrays):

```javascript
this.$watch('filters', (newVal, oldVal) => {
    this.fetchResults()
}, { deep: true })
```

Without `deep: true`, the callback only fires when the reference changes, not when nested properties change.

**Inline in x-init:**

```html
<div x-data="{ query: '' }"
     x-init="$watch('query', q => q.length > 2 && search(q))">
    <input x-model.debounce.300ms="query">
</div>
```

## $dispatch — Custom Events

Dispatches a bubbling `CustomEvent` from the current element. Other Alpine components (or plain DOM listeners) can catch it.

```html
<!-- Dispatcher -->
<button @click="$dispatch('item-removed', { id: item.id })">Remove</button>

<!-- Listener anywhere up the DOM tree -->
<div @item-removed="handleRemove($event.detail.id)">
    ...
</div>
```

**Event detail** is accessed via `$event.detail`. The event bubbles up through the DOM, so the listener can be a parent, grandparent, or `window`.

**Listening on window** (cross-component, anywhere on page):

```html
<!-- Dispatcher -->
<button @click="$dispatch('toast', { message: 'Saved!', level: 'success' })">Save</button>

<!-- Toast component elsewhere in the page -->
<div x-data="{ messages: [] }"
     @toast.window="messages.push($event.detail); setTimeout(() => messages.shift(), 3000)">
    <template x-for="msg in messages" :key="msg.message">
        <div class="alert" :class="'alert-' + msg.level" x-text="msg.message"></div>
    </template>
</div>
```

Note: `$dispatch` fires a DOM event — it cannot cross shadow DOM boundaries.

## $nextTick — Post-DOM-Update Callback

Run code after Alpine has finished updating the DOM. Useful for focusing elements after they become visible, or reading updated DOM dimensions.

```html
<!-- Focus input after modal opens -->
<div x-data="{ open: false }">
    <button @click="open = true; $nextTick(() => $refs.input.focus())">Open</button>
    <div x-show="open">
        <input x-ref="input" type="text">
    </div>
</div>
```

Also available as a Promise (for async contexts):

```javascript
await this.$nextTick()
// DOM is now updated
```

## $id and x-id

`$id(name)` generates a unique-per-component ID string. Register the names with `x-id` first.

```html
<div x-data x-id="['toggle', 'panel']">
    <button :id="$id('toggle')" :aria-controls="$id('panel')">Toggle</button>
    <div :id="$id('panel')" :aria-labelledby="$id('toggle')">Content</div>
</div>
```

Each `x-id` scope gets its own incrementing counter — two instances of the same component will have IDs like `toggle-1`/`toggle-2`.

## Alpine.data() — Reusable Components

Register named components to keep logic out of HTML. Defined before `Alpine.start()` or inside `alpine:init`.

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.data('dropdown', (defaultOpen = false) => ({
        open: defaultOpen,

        // Called automatically before Alpine renders the component
        init() {
            this.$watch('open', val => {
                // Magic properties work via `this`
                this.$dispatch('dropdown:changed', { open: val })
            })
        },

        // Called automatically when component is removed from DOM
        destroy() {
            // Clean up external event listeners, timers, etc.
        },

        toggle() {
            this.open = !this.open
        },

        close() {
            this.open = false
        }
    }))
})
```

**Usage:**

```html
<!-- No parameters -->
<div x-data="dropdown">...</div>

<!-- With initial parameters -->
<div x-data="dropdown(true)">...</div>
```

**With `$persist` in Alpine.data** — use a regular function (not arrow) so Alpine can bind `this`:

```javascript
Alpine.data('settings', function() {
    return {
        darkMode: this.$persist(false)
    }
})
```

**Using `x-bind` to encapsulate directives** — bundle both data and template directives together:

```javascript
Alpine.data('dropdown', () => ({
    open: false,

    // Encapsulated directive sets
    trigger: {
        ['@click']() { this.open = !this.open },
        [':aria-expanded']() { return this.open }
    },

    panel: {
        ['x-show']() { return this.open },
        ['@click.outside']() { this.open = false }
    }
}))
```

```html
<div x-data="dropdown">
    <button x-bind="trigger">Toggle</button>
    <div x-bind="panel">Contents</div>
</div>
```

## Alpine.store() — Global State

Define global reactive state accessible everywhere via `$store.name`:

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.store('cart', {
        items: [],

        add(item) {
            this.items.push(item)
        },

        remove(id) {
            this.items = this.items.filter(i => i.id !== id)
        },

        get count() {
            return this.items.length
        }
    })
})
```

**In templates:**

```html
<span x-text="$store.cart.count"></span>
<button @click="$store.cart.add(item)">Add to Cart</button>
```

**From JavaScript** (outside of Alpine templates):

```javascript
// Read
Alpine.store('cart').count

// Write — changes are reactive, templates update automatically
Alpine.store('cart').items = []
```

**Simple value stores:**

```javascript
Alpine.store('darkMode', false)  // $store.darkMode is a plain boolean
```

```html
<button @click="$store.darkMode = !$store.darkMode">Toggle Theme</button>
<html :data-theme="$store.darkMode ? 'dark' : 'light'">
```

## Alpine.bind() — Reusable Attribute Sets

Define a named object of HTML attributes (including Alpine directives) to apply to elements with `x-bind`:

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.bind('CloseButton', () => ({
        type: 'button',
        '@click'() { this.open = false },
        ':aria-label'() { return this.open ? 'Close' : 'Open' }
    }))
})
```

```html
<!-- Apply to any element -->
<button x-bind="CloseButton">×</button>
```

`Alpine.bind()` is static (not tied to a component's data scope), so it's best for generic UI patterns. For component-specific encapsulation, use the `x-bind` object pattern inside `Alpine.data()` instead.

## $el — Current Element

Reference to the DOM element the current expression is attached to:

```html
<button @click="$el.textContent = 'Clicked!'">Click Me</button>
```

Useful for passing the element to third-party libraries or for reading attributes:

```html
<button @click="handleClick($el)" data-action="delete">Delete</button>
```

## $refs — Element References

Object containing all elements in the component marked with `x-ref`:

```html
<div x-data>
    <input x-ref="search" type="text">
    <button @click="$refs.search.select()">Select All</button>
</div>
```

`$refs` is populated after `x-init` runs, so it's safe to use in event handlers but not synchronously in `x-init` before `$nextTick`.

## $root — Root Component Element

Reference to the root element of the nearest `x-data` component — useful when you need to traverse up from a deeply nested element:

```html
<div x-data="{ open: false }">
    <div>
        <button @click="$root.querySelector('[x-ref=panel]').focus()">Focus Panel</button>
    </div>
    <div x-ref="panel" tabindex="-1" x-show="open">...</div>
</div>
```

## $data — Component Data Object

Returns the entire reactive data object of the current component. Useful for passing component state to external functions:

```html
<form x-data="{ name: '', email: '' }" @submit.prevent="submitForm($data)">
    <input x-model="name">
    <input x-model="email">
    <button type="submit">Submit</button>
</form>

<script>
function submitForm(data) {
    console.log(data.name, data.email)
}
</script>
```
