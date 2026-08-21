# HTMX Attributes Reference

Full reference for all `hx-*` attributes in htmx 2.x.

## Core Attributes

### hx-get / hx-post / hx-put / hx-patch / hx-delete

Issue an AJAX request to the given URL on trigger.

```html
<button hx-get="/api/items">Load Items</button>
<form hx-post="/api/items">...</form>
<button hx-put="/api/items/1">Replace</button>
<button hx-patch="/api/items/1">Update</button>
<button hx-delete="/api/items/1">Delete</button>
```

By default, element values (or enclosing form values for non-GET verbs) are sent as parameters.

### hx-trigger

Specifies which event triggers the request. Multiple triggers separated by commas.

**Syntax:** `hx-trigger="<event> [modifiers], <event> [modifiers], ..."`

**Default triggers by element:**

- `input`, `textarea`, `select` → `change`
- `form` → `submit`
- all other elements → `click`

**Modifiers:**

| Modifier | Description |
|---|---|
| `once` | Only trigger the first time |
| `changed` | Only if element value changed since last request |
| `delay:<time>` | Debounce: wait, reset timer if event fires again (e.g. `delay:500ms`) |
| `throttle:<time>` | Throttle: discard events within window, fire at end (e.g. `throttle:1s`) |
| `from:<CSS selector>` | Listen on a different element (re-evaluated on page changes: no) |
| `target:<CSS selector>` | Filter events to those originating from matching element |
| `consume` | Prevent event from propagating after htmx handles it |
| `queue:<strategy>` | Queue behavior when requests overlap: `first`, `last`, `all`, `none` |

**Trigger filters** — JS expression in `[...]`, only triggers if truthy:

```html
<div hx-get="/data" hx-trigger="click[ctrlKey]">Ctrl+Click me</div>
<div hx-get="/data" hx-trigger="keyup[key=='Enter']">Press Enter</div>
```

Properties resolve against the event first, then global scope. `this` = current element.

**Special events:**

- `load` — fires once when element is first loaded (great for lazy loading)
- `revealed` — fires once when element first scrolls into viewport
- `intersect` — fires once on intersection. Options: `root:<sel>`, `threshold:<float>`
- `every <time>` — polling (e.g. `every 2s`). Respond with HTTP 286 to stop polling.

**Examples:**

```html
<!-- active search: debounced, only on value change -->
<input hx-get="/search" hx-trigger="keyup changed delay:500ms" hx-target="#results">

<!-- lazy load on scroll-into-view -->
<div hx-get="/content" hx-trigger="revealed" hx-swap="outerHTML">Loading...</div>

<!-- poll every 5 seconds -->
<div hx-get="/status" hx-trigger="every 5s"></div>

<!-- keyboard shortcut: listen on body -->
<div hx-get="/shortcut" hx-trigger="keyup[key=='s'] from:body">...</div>

<!-- multiple triggers -->
<input hx-get="/search" hx-trigger="keyup changed delay:300ms, search">
```

### hx-target

CSS selector for the element to swap the response into. Defaults to the element itself.

```html
<button hx-get="/data" hx-target="#output">Load</button>
<div id="output"></div>
```

**Extended selectors:**

- `this` — the element with the `hx-target` attribute
- `closest <sel>` — nearest ancestor matching selector
- `next <sel>` — next element in DOM matching selector
- `previous <sel>` — previous element in DOM matching selector
- `find <sel>` — first descendant matching selector

```html
<!-- target the closest table row -->
<button hx-delete="/item/1" hx-target="closest tr" hx-swap="outerHTML">Delete</button>

<!-- target an error div right after the input -->
<input hx-post="/validate" hx-target="next .error">
<div class="error"></div>
```

### hx-swap

How to swap the response HTML into the target. Default: `innerHTML`.

| Value | Effect |
|---|---|
| `innerHTML` | Replace inner content of target (default) |
| `outerHTML` | Replace entire target element |
| `afterbegin` | Prepend inside target (before first child) |
| `beforebegin` | Insert before target element in its parent |
| `beforeend` | Append inside target (after last child) |
| `afterend` | Insert after target element in its parent |
| `delete` | Delete target regardless of response body |
| `none` | Don't swap anything (still process OOB and response headers) |

**Swap modifiers** (appended after style, colon-separated):

| Modifier | Description |
|---|---|
| `swap:<time>` | Delay between clearing old and inserting new content |
| `settle:<time>` | Delay before settling new content (for CSS transitions) |
| `ignoreTitle:true` | Don't update document title from `<title>` in response |
| `scroll:top` / `scroll:bottom` | Scroll target to top/bottom after swap |
| `show:top` / `show:bottom` | Scroll target's top/bottom into viewport |
| `focus-scroll:true` | Scroll focused element into view |
| `transition:true` | Use View Transition API for this swap |

```html
<!-- append with animation delay -->
<button hx-post="/items" hx-target="#list" hx-swap="beforeend swap:100ms">Add</button>

<!-- scroll to top after loading -->
<a hx-get="/page2" hx-target="#content" hx-swap="innerHTML show:top">Next page</a>

<!-- ignore title updates -->
<button hx-post="/like" hx-swap="outerHTML ignoreTitle:true">Like</button>
```

**Morph swaps** (requires idiomorph extension — `hx-ext="morph"` on ancestor):

```html
<button hx-get="/data" hx-swap="morph">Morph outerHTML</button>
<button hx-get="/data" hx-swap="morph:outerHTML">Morph outerHTML</button>
<button hx-get="/data" hx-swap="morph:innerHTML">Morph innerHTML only</button>
```

### hx-swap-oob

Mark elements in a **response** to be swapped into the DOM by their `id`, independent of the primary target.

```html
<!-- in the server's HTML response: -->
<div id="primary-target">Main content</div>

<!-- these will be swapped OOB by matching id: -->
<div id="notification-area" hx-swap-oob="true">New notification!</div>
<span id="badge-count" hx-swap-oob="true">5</span>

<!-- use a specific swap style: -->
<div id="log" hx-swap-oob="beforeend">New log entry</div>

<!-- target a different element by selector: -->
<div hx-swap-oob="outerHTML:#some-other-id">Replacement</div>
```

For `<tr>`, `<td>`, `<th>` elements (which can't stand alone in DOM):

```html
<template>
  <tr id="row-42" hx-swap-oob="true"><td>Updated</td></tr>
</template>
```

OOB-only response (button triggers OOB updates only, no primary swap):

```html
<button hx-post="/action" hx-target="none" hx-swap="none">Trigger</button>
```

### hx-select

Select a subset of the response to swap in (CSS selector applied to response HTML):

```html
<button hx-get="/page" hx-select="#main-content">Load section</button>
```

### hx-select-oob

Pick out specific elements from response for OOB swap (comma-separated IDs or `id:swap-style` pairs):

```html
<button hx-get="/page" hx-select="#main" hx-select-oob="#sidebar,#nav:outerHTML">Load</button>
```

### hx-vals

Add extra static parameters to the request as JSON:

```html
<button hx-post="/click" hx-vals='{"userId": 42, "action": "approve"}'>Approve</button>

<!-- dynamic JS values with js: prefix -->
<button hx-post="/click" hx-vals='js:{"timestamp": Date.now(), "page": window.location.pathname}'>Submit</button>
```

### hx-vars

Comma-separated name-expression pairs (deprecated, prefer `hx-vals`):

```html
<button hx-post="/click" hx-vars="timestamp:Date.now()">Submit</button>
```

### hx-include

Include values from other elements in the request:

```html
<!-- include a specific element's value -->
<button hx-get="/search" hx-include="#search-input">Search</button>

<!-- include all inputs in a form -->
<button hx-post="/submit" hx-include="closest form">Submit</button>
```

### hx-params

Filter which parameters are submitted:

```html
<!-- only include these params -->
<form hx-post="/register" hx-params="username,email">...</form>

<!-- exclude these params -->
<form hx-post="/update" hx-params="not csrf_token">...</form>

<!-- include none -->
<button hx-post="/ping" hx-params="none">Ping</button>

<!-- include all (default) -->
<form hx-post="/submit" hx-params="*">...</form>
```

### hx-encoding

Change request encoding type (for file uploads):

```html
<form hx-post="/upload" hx-encoding="multipart/form-data">
  <input type="file" name="file">
  <button type="submit">Upload</button>
</form>
```

### hx-boost

Convert anchor tags and forms to AJAX requests (degrades gracefully):

```html
<div hx-boost="true">
  <a href="/blog">Blog</a>        <!-- issues AJAX GET, swaps into <body> -->
  <form action="/submit" method="POST">...</form>
</div>
```

### hx-indicator

Specify which element gets the `htmx-request` class (and thus reveals `.htmx-indicator` children):

```html
<!-- show a spinner that's a sibling, not a child -->
<button hx-get="/data" hx-indicator="#global-spinner">Load</button>
<img id="global-spinner" class="htmx-indicator" src="/spinner.gif" alt="Loading...">
```

### hx-disabled-elt

Add `disabled` attribute to specified elements during the request:

```html
<!-- disable the button itself -->
<button hx-post="/submit" hx-disabled-elt="this">Submit</button>

<!-- disable multiple elements -->
<button hx-post="/submit" hx-disabled-elt="this, #cancel-btn">Submit</button>

<!-- disable closest form inputs -->
<button hx-post="/submit" hx-disabled-elt="closest form">Submit</button>
```

### hx-confirm

Show a JS `confirm()` dialog before issuing the request:

```html
<button hx-delete="/account" hx-confirm="Are you sure you wish to delete your account?">
  Delete My Account
</button>
```

### hx-prompt

Show a JS `prompt()` dialog and send the result as `HX-Prompt` header:

```html
<button hx-post="/rename" hx-prompt="Enter new name:">Rename</button>
```

### hx-push-url

Push a URL into the browser history stack after the request:

```html
<a hx-get="/blog" hx-push-url="true">Blog</a>
<a hx-get="/page" hx-push-url="/custom-url">Go</a>  <!-- push a custom URL -->
<a hx-get="/page" hx-push-url="false">No history</a>
```

### hx-replace-url

Replace the current URL in the browser bar (no new history entry):

```html
<button hx-get="/search?q=foo" hx-replace-url="true">Search</button>
```

### hx-history-elt

Specify which element to snapshot for browser history (defaults to `<body>`):

```html
<main id="content" hx-history-elt>...</main>
```

### hx-history

Prevent the page from being saved to localStorage history cache:

```html
<div hx-history="false">Sensitive content not cached</div>
```

### hx-sync

Coordinate request timing between elements:

```html
<!-- abort input validation if form submit starts -->
<input hx-post="/validate" hx-trigger="change" hx-sync="closest form:abort">

<!-- queue requests: only run after previous completes -->
<button hx-post="/step" hx-sync="this:queue last">Next Step</button>
```

Strategies: `drop`, `abort`, `replace`, `queue first`, `queue last`, `queue all`

### hx-on*

Respond to any event inline (generalizes `onclick` etc. to arbitrary events):

```html
<!-- respond to a standard event -->
<button hx-on:click="alert('clicked!')">Click me</button>

<!-- respond to an htmx event (use kebab-case for camelCase events) -->
<button hx-post="/submit"
        hx-on:htmx:config-request="event.detail.parameters.token = getToken()">
  Submit
</button>

<!-- reset form after successful request -->
<form hx-post="/submit"
      hx-on:htmx:after-request="if(event.detail.successful) this.reset()">
  ...
</form>
```

Note: HTML attributes are case-insensitive. Use kebab-case for events with camelCase names (e.g. `htmx:configRequest` → `hx-on:htmx:config-request`).

### hx-headers

Add extra headers to the request:

```html
<!-- CSRF token pattern -->
<body hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token }}"}'>
  ...
</body>

<!-- dynamic JS value -->
<form hx-post="/api" hx-headers='js:{"Authorization": "Bearer " + getToken()}'>
  ...
</form>
```

### hx-request

Configure request behavior:

```html
<!-- set timeout (ms) -->
<button hx-get="/slow" hx-request='{"timeout": 5000}'>Load</button>

<!-- add credentials to cross-site requests -->
<button hx-get="https://api.example.com/data" hx-request='{"credentials": "include"}'>Load</button>

<!-- no loading indicator (suppress htmx-request class) -->
<button hx-post="/fast" hx-request='{"noPrompt": true}'>Fast</button>
```

### hx-validate

Force non-form elements to validate before making requests:

```html
<input type="email" name="email" hx-post="/check-email" hx-validate="true">
```

### hx-preserve

Keep an element unchanged across swaps (e.g. a playing video):

```html
<video id="player" hx-preserve src="/stream.mp4" controls autoplay></video>
```

### hx-ext

Enable extensions for an element and its descendants:

```html
<body hx-ext="response-targets">...</body>
<div hx-ext="morph, debug">...</div>
```

### hx-disable

Prevent htmx from processing attributes on this element and all descendants:

```html
<div hx-disable>
  <!-- htmx attributes in here are ignored -->
  <%= raw(untrusted_content) %>
</div>
```

### hx-disinherit

Disable inheritance of specific attributes for child elements:

```html
<!-- children won't inherit hx-confirm or hx-target -->
<div hx-confirm="Sure?" hx-target="#output" hx-disinherit="hx-confirm hx-target">
  <button hx-post="/action">Action</button>
</div>
```

### hx-inherit

When global inheritance is disabled (`htmx.config.disableInheritance = true`), explicitly re-enable specific attributes:

```html
<div hx-target="#output" hx-inherit="hx-target">
  <button hx-post="/action">Action</button>
</div>
```
