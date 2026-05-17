# Alpine.js Directives — Deep Reference

## x-bind — Full Details

### Class Object Syntax

When using object syntax, Alpine does NOT overwrite the element's static `class` attribute — it merges:

```html
<!-- opacity-50 is always present; hidden toggles based on `hide` -->
<div class="opacity-50" :class="{ 'hidden': hide, 'ring-2': focused }">
```

String and array class bindings replace the entire dynamic portion:

```html
<div :class="isError ? 'text-error' : 'text-success'">
<div :class="['btn', size === 'sm' ? 'btn-sm' : 'btn-lg']">
```

### Style Object Syntax

```html
<div :style="{ color: 'red', fontSize: size + 'px', display: flex ? 'flex' : 'block' }">
```

Merges with any static `style` attribute on the element.

### Binding Alpine Directives via Object

`x-bind` can accept a full object of attributes including Alpine directives:

```html
<button x-bind="triggerAttrs">Click</button>

<script>
Alpine.data('dropdown', () => ({
    open: false,
    triggerAttrs: {
        '@click'() { this.open = !this.open },
        ':aria-expanded'() { return this.open },
        'class': 'btn btn-primary'
    }
}))
</script>
```

### Boolean Attributes

Alpine evaluates boolean attributes correctly — if the expression is falsy, the attribute is removed entirely (not set to `"false"`):

```html
<button :disabled="isSubmitting">Submit</button>   <!-- removes disabled when false -->
<input :required="field.required">
<details :open="expanded">
```

## x-model — All Input Types and Modifiers

### Input Types

```html
<!-- Text / Textarea -->
<input type="text" x-model="name">
<textarea x-model="bio"></textarea>

<!-- Single checkbox → boolean -->
<input type="checkbox" x-model="accepted">

<!-- Multiple checkboxes → array of values -->
<input type="checkbox" value="read"   x-model="permissions">
<input type="checkbox" value="write"  x-model="permissions">
<input type="checkbox" value="delete" x-model="permissions">

<!-- Radio -->
<input type="radio" value="monthly" x-model="billing">
<input type="radio" value="annual"  x-model="billing">

<!-- Select (single) -->
<select x-model="country">
    <option value="">Choose...</option>
    <option value="US">United States</option>
</select>

<!-- Select (multiple) → array -->
<select x-model="tags" multiple>
    <option>alpine</option>
    <option>htmx</option>
</select>

<!-- Range -->
<input type="range" min="0" max="100" x-model="volume">
```

### Modifiers

```html
<!-- .lazy: sync on change event instead of input (fires on blur) -->
<input x-model.lazy="email">

<!-- .number: coerce value to a JS number -->
<input type="number" x-model.number="quantity">

<!-- .boolean: coerce string "true"/"false" to boolean (useful for select) -->
<select x-model.boolean="enabled">
    <option value="true">Yes</option>
    <option value="false">No</option>
</select>

<!-- .debounce: delay syncing (default 250ms) -->
<input x-model.debounce.500ms="searchQuery">

<!-- .throttle: throttle syncing (default 250ms) -->
<input x-model.throttle.300ms="sliderValue">
```

## x-transition — CSS Class Approach

For full animation control using Tailwind or custom CSS:

```html
<div x-show="open"
     x-transition:enter="transition ease-out duration-300"
     x-transition:enter-start="opacity-0 translate-y-4"
     x-transition:enter-end="opacity-100 translate-y-0"
     x-transition:leave="transition ease-in duration-200"
     x-transition:leave-start="opacity-100 translate-y-0"
     x-transition:leave-end="opacity-0 translate-y-4">
```

| Stage attribute | When classes apply |
|---|---|
| `:enter` | Entire entering phase |
| `:enter-start` | Before element is shown; removed 1 frame after |
| `:enter-end` | Added 1 frame after shown; removed when transition finishes |
| `:leave` | Entire leaving phase |
| `:leave-start` | Immediately when leaving starts; removed after 1 frame |
| `:leave-end` | Added 1 frame after leaving starts; removed when transition finishes |

**Transition helper modifiers** (when not using CSS classes):

```html
<!-- Only fade, no scale -->
<div x-show="open" x-transition.opacity>

<!-- Only scale, no fade -->
<div x-show="open" x-transition.scale>

<!-- Scale to 80% from top -->
<div x-show="open" x-transition.scale.80.origin.top>

<!-- Custom duration per phase -->
<div x-show="open"
     x-transition:enter.duration.300ms
     x-transition:leave.duration.150ms>
```

## x-for — Keys, Indexes, Nested Loops

```html
<!-- Basic with :key -->
<template x-for="item in items" :key="item.id">
    <div x-text="item.name"></div>
</template>

<!-- Destructure with index -->
<template x-for="(item, index) in items" :key="item.id">
    <div>
        <span x-text="index + 1"></span>.
        <span x-text="item.label"></span>
    </div>
</template>

<!-- Iterate over object (value, key) -->
<template x-for="(value, key) in config">
    <div><span x-text="key"></span>: <span x-text="value"></span></div>
</template>

<!-- Range (1 to N) -->
<template x-for="i in 5">
    <span x-text="i"></span>
</template>

<!-- Nested loops — each x-for has its own scope -->
<template x-for="group in groups" :key="group.id">
    <div>
        <h3 x-text="group.name"></h3>
        <template x-for="item in group.items" :key="item.id">
            <p x-text="item.label"></p>
        </template>
    </div>
</template>
```

**Important:** `<template>` must contain exactly one root element. Wrap multiple elements in a `<div>` or `<template>`.

## x-teleport — Render Elsewhere in DOM

Moves an element's content to a different part of the DOM (e.g., modals to `<body>`). The Alpine scope of the source is preserved.

```html
<!-- Renders the content inside <body> while Alpine scope stays here -->
<div x-data="{ open: false }">
    <button @click="open = true">Open Modal</button>

    <template x-teleport="body">
        <div x-show="open" class="modal modal-open">
            <div class="modal-box">
                <p>I'm rendered in body, but share x-data scope above</p>
                <button @click="open = false">Close</button>
            </div>
        </div>
    </template>
</div>
```

`x-teleport` must be on a `<template>` element. The teleported content can still read and write to the parent component's data.

## x-modelable — Expose Internal Value

Lets a child component expose a property for a parent to bind with `x-model`. Useful for custom input components.

```html
<!-- Custom toggle component -->
<div x-data="{ on: false }" x-modelable="on" x-model="parentValue">
    <button @click="on = !on" :class="on ? 'btn-success' : 'btn-ghost'">
        Toggle
    </button>
</div>

<!-- Parent uses x-model to bind to it -->
<div x-data="{ myToggle: false }">
    <div x-data="{ on: false }" x-modelable="on" x-model="myToggle">
        <button @click="on = !on">Toggle</button>
    </div>
    <span x-text="myToggle ? 'On' : 'Off'"></span>
</div>
```

## x-id / $id — Scoped Unique IDs

Generate unique IDs that are scoped to a component — critical for accessible `for`/`id` label linkage when a component is rendered multiple times.

```html
<div x-data x-id="['my-input']">
    <!-- $id('my-input') returns a unique string like "my-input-1" -->
    <label :for="$id('my-input')">Username</label>
    <input :id="$id('my-input')" type="text">
</div>

<!-- A second instance gets a different ID: "my-input-2" -->
<div x-data x-id="['my-input']">
    <label :for="$id('my-input')">Username</label>
    <input :id="$id('my-input')" type="text">
</div>
```

`x-id` takes an array of ID names to register. `$id('name')` returns the scoped value.

## x-effect

Re-evaluates its expression whenever any reactive data it references changes. Different from `x-init` which only runs once.

```html
<div x-data="{ query: '' }" x-effect="console.log('searching for:', query)">
    <input x-model="query">
</div>
```

Useful for syncing Alpine state to third-party libraries or performing DOM side effects without watching specific properties.

## x-ignore

Prevents Alpine from initializing on an element and all its children. Useful for Jinja2-rendered sections that contain `{{` `}}` syntax you don't want Alpine to parse.

```html
<div x-ignore>
    <!-- Alpine will not process anything here -->
    <span>{{ jinja_variable }}</span>
</div>
```
