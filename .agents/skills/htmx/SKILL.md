---
name: htmx
description: Reference for building htmx-powered web UIs. Use whenever writing or reviewing HTML that uses hx-* attributes, htmx triggers, swaps, OOB swaps, extensions (response-targets, SSE, WebSockets, idiomorph), server response headers, or any htmx-related pattern. Also triggers for questions about active search, infinite scroll, polling, inline editing, or other HTMX UI patterns, integrating htmx with FastAPI/Jinja2 backends, or combining HTMX with Alpine.js (htmx:before-request events, triggering htmx from Alpine, passing server data, preserving Alpine state across swaps).
---

# HTMX Reference Skill

htmx lets you add AJAX, CSS transitions, WebSockets, and SSE directly from HTML attributes. Server responds with **HTML**, not JSON. Version in use: **htmx 2.x**.

## Reference Files

Load these on demand when you need depth beyond what's here:

| File | When to load |
|---|---|
| `references/attributes.md` | Details on a specific `hx-*` attribute, all modifiers, full syntax |
| `references/server.md` | Request/response headers, error handling, 422 pattern, CSRF, CORS |
| `references/events.md` | htmx lifecycle events, JS API (`htmx.on`, `htmx.process`, etc.) |
| `references/extensions.md` | response-targets, SSE, WebSockets, idiomorph, preload — full usage |
| `references/patterns.md` | Active search, infinite scroll, polling, inline editing, OOB patterns, HTMX+Alpine integration |

## Core AJAX Attributes

Any element can issue any HTTP verb. The element value (or enclosing form values) is sent as parameters.

```html
<button hx-get="/items">Load</button>
<button hx-post="/items">Create</button>
<button hx-put="/items/1">Replace</button>
<button hx-patch="/items/1">Update</button>
<button hx-delete="/items/1">Delete</button>
```

Default trigger per element type:

- `input`, `textarea`, `select` → `change`
- `form` → `submit`
- everything else → `click`

## hx-trigger

Override the triggering event. Multiple triggers separated by commas.

```html
<!-- trigger on mouseenter -->
<div hx-get="/data" hx-trigger="mouseenter">...</div>

<!-- active search: trigger on keyup, debounced 500ms, only if value changed -->
<input hx-get="/search" hx-trigger="keyup changed delay:500ms" hx-target="#results">

<!-- poll every 2 seconds -->
<div hx-get="/updates" hx-trigger="every 2s">...</div>

<!-- fire once on load -->
<div hx-get="/lazy" hx-trigger="load">...</div>

<!-- fire when scrolled into viewport (once) -->
<div hx-get="/more" hx-trigger="revealed">...</div>

<!-- multiple triggers -->
<input hx-get="/search" hx-trigger="keyup changed delay:300ms, search">
```

### Trigger Modifiers

| Modifier | Meaning |
|---|---|
| `once` | Only trigger the first time |
| `changed` | Only trigger if element value changed |
| `delay:<time>` | Debounce — wait, reset if event fires again (e.g. `delay:500ms`) |
| `throttle:<time>` | Throttle — discard events within the window (e.g. `throttle:1s`) |
| `from:<selector>` | Listen on a different element (e.g. `from:body` for keyboard shortcuts) |

### Trigger Filters

Square-bracket JS expression after event name — only fires if truthy:

```html
<!-- only on Ctrl+click -->
<div hx-get="/clicked" hx-trigger="click[ctrlKey]">...</div>
```

### Special Events

- `load` — fires once when element is first loaded into DOM
- `revealed` — fires once when element scrolls into viewport
- `intersect` — fires once on viewport intersection (supports `root:<sel>` and `threshold:<float>`)

## hx-target

Which element to swap the response into. Defaults to the element itself.

```html
<input hx-get="/search" hx-target="#results">
<div id="results"></div>
```

### Extended CSS Selectors (work in hx-target and most selector attributes)

| Syntax | Meaning |
|---|---|
| `this` | The element with the attribute |
| `closest <sel>` | Nearest ancestor matching selector (e.g. `closest tr`) |
| `next <sel>` | Next sibling in DOM matching selector |
| `previous <sel>` | Previous sibling in DOM matching selector |
| `find <sel>` | First descendant matching selector |

## hx-swap

How to insert the response HTML. Default: `innerHTML`.

| Value | Effect |
|---|---|
| `innerHTML` | Replace inner content of target (default) |
| `outerHTML` | Replace the entire target element |
| `afterbegin` | Prepend inside target (before first child) |
| `beforebegin` | Insert before target in its parent |
| `beforeend` | Append inside target (after last child) |
| `afterend` | Insert after target in its parent |
| `delete` | Delete target regardless of response |
| `none` | Do nothing (but still process OOB swaps and response headers) |

### Swap Modifiers (append after swap style)

```html
<!-- morph swap (requires idiomorph extension) -->
<button hx-get="/data" hx-swap="morph">...</button>

<!-- delay before swap, delay before settle -->
<button hx-get="/data" hx-swap="innerHTML swap:100ms settle:200ms">...</button>

<!-- ignore title tag in response -->
<button hx-post="/like" hx-swap="outerHTML ignoreTitle:true">Like</button>

<!-- scroll target to top after swap -->
<button hx-get="/page2" hx-swap="innerHTML show:top">Next</button>

<!-- view transition -->
<button hx-get="/page" hx-swap="innerHTML transition:true">...</button>
```

## Out-of-Band (OOB) Swaps

Swap additional elements in the response by their `id`, independent of the main target. The response HTML includes `hx-swap-oob` on elements to be swapped elsewhere.

```html
<!-- Server returns this HTML: -->
<div id="main-content">Primary response content</div>
<div id="toast-container" hx-swap-oob="true">
  <div class="alert">Action completed!</div>
</div>
<span id="item-count" hx-swap-oob="true">42 items</span>
```

- `hx-swap-oob="true"` — swap using `outerHTML` (default)
- `hx-swap-oob="beforeend"` — use a specific swap style
- `hx-swap-oob="outerHTML:#other-id"` — swap a different element by selector

**Important for table elements** (`<tr>`, `<td>`, etc.) — wrap in `<template>`:

```html
<template>
  <tr id="row-1" hx-swap-oob="true"><td>Updated</td></tr>
</template>
```

**OOB-only responses** (button does nothing to itself, only triggers OOB updates):

```html
<button hx-post="/action" hx-target="none" hx-swap="none">Do It</button>
```

## Request Indicators

Show a spinner while a request is in flight. The `.htmx-indicator` class is opacity:0 by default; becomes opacity:1 when `.htmx-request` is present on an ancestor.

```html
<button hx-get="/click">
  Click Me!
  <img class="htmx-indicator" src="/spinner.gif" alt="Loading...">
</button>

<!-- point to a separate indicator element -->
<button hx-get="/click" hx-indicator="#spinner">Click</button>
<img id="spinner" class="htmx-indicator" src="/spinner.gif" alt="Loading...">

<!-- disable a button during request -->
<button hx-post="/submit" hx-disabled-elt="this">Submit</button>
```

## Parameters & Values

```html
<!-- include values from other elements -->
<button hx-get="/search" hx-include="#filter-select">Search</button>

<!-- filter out specific params -->
<form hx-post="/submit" hx-params="not password">...</form>

<!-- static extra values (JSON) -->
<button hx-post="/click" hx-vals='{"userId": 42}'>Click</button>

<!-- dynamic extra values (JS expression) -->
<button hx-post="/click" hx-vars="timestamp:Date.now()">Click</button>

<!-- file upload -->
<form hx-post="/upload" hx-encoding="multipart/form-data">
  <input type="file" name="file">
  <button type="submit">Upload</button>
</form>
```

## Attribute Inheritance

Most `hx-*` attributes inherit down the DOM tree. Hoist shared attributes to a parent:

```html
<div hx-confirm="Are you sure?">
  <button hx-delete="/account">Delete</button>
  <button hx-put="/account">Update</button>
  <!-- cancel button opts out with unset -->
  <button hx-confirm="unset" hx-get="/">Cancel</button>
</div>
```

Disable inheritance for specific attributes: `hx-disinherit="hx-confirm hx-target"`
Disable all inheritance globally: `htmx.config.disableInheritance = true`, then opt-in with `hx-inherit`.

## Boosting

Convert all `<a>` and `<form>` elements to AJAX requests (degrades gracefully without JS):

```html
<div hx-boost="true">
  <a href="/blog">Blog</a>        <!-- AJAX GET to /blog, swaps into body -->
  <form action="/submit" method="POST">...</form>
</div>
```

## History

```html
<!-- push URL into browser history on request -->
<a hx-get="/blog" hx-push-url="true">Blog</a>

<!-- replace current URL instead of pushing -->
<button hx-get="/search?q=foo" hx-replace-url="true">Search</button>

<!-- prevent sensitive page from being cached in localStorage history -->
<div hx-history="false">...</div>
```

> **Note:** If you push a URL, you must be able to serve a full page at that URL (for back button / direct navigation). Always set `htmx.config.historyRestoreAsHxRequest = false` when using `HX-Request` to serve partials.

## Synchronization

Prevent race conditions between requests on multiple elements:

```html
<!-- abort input's validation request if form is submitted -->
<form hx-post="/store">
  <input hx-post="/validate" hx-trigger="change" hx-sync="closest form:abort">
  <button type="submit">Submit</button>
</form>
```

`hx-sync` strategies: `drop`, `abort`, `replace`, `queue first`, `queue last`, `queue all`

Programmatic cancel:

```javascript
htmx.trigger('#request-button', 'htmx:abort')
```

## Security

```html
<!-- prevent htmx from processing untrusted injected content -->
<div hx-disable>
  <%= raw(user_content) %>
</div>
```

Config:

```javascript
htmx.config.selfRequestsOnly = true    // only same-domain requests
htmx.config.allowScriptTags = false    // don't execute <script> in new content
htmx.config.allowEval = false          // disable eval-based features
```

## Configuration

Set via JS or meta tag:

```html
<meta name="htmx-config" content='{"defaultSwapStyle":"outerHTML", "historyRestoreAsHxRequest": false}'>
```

Key config options:

```javascript
htmx.config.defaultSwapStyle        // default: "innerHTML"
htmx.config.defaultSwapDelay        // default: 0
htmx.config.defaultSettleDelay      // default: 20 (ms)
htmx.config.selfRequestsOnly        // default: true
htmx.config.historyRestoreAsHxRequest // default: true — set false when using HX-Request for partials
htmx.config.globalViewTransitions   // default: false
htmx.config.responseHandling        // array of {code, swap, error} — see references/server.md
```

## Enabling Extensions

Load the extension script after htmx, then enable with `hx-ext` on a container or `<body>`:

```html
<head>
  <script src="...htmx.min.js"></script>
  <script src="...htmx-ext-response-targets.js"></script>
</head>
<body hx-ext="response-targets">
  ...
</body>
```

Core extensions: `response-targets`, `sse`, `ws`, `morph` (idiomorph), `preload`, `head-support`, `htmx-1-compat`

See `references/extensions.md` for full details on each.
