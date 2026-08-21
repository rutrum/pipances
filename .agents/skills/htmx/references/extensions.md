# HTMX Extensions Reference

Extensions augment htmx's core behavior. Load extension scripts after htmx, then enable with `hx-ext` on a container.

## How Extensions Work

```html
<head>
  <!-- 1. Load htmx core first -->
  <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.10/dist/htmx.min.js"
          integrity="sha384-H5SrcfygHmAuTDZphMHqBJLc3FhssKjG7w/CeCpFReSfwBWDTKpkzPP8c+cLsK+V"
          crossorigin="anonymous"></script>

  <!-- 2. Load extension script(s) -->
  <script src="https://cdn.jsdelivr.net/npm/htmx-ext-response-targets@2.0.4"
          integrity="sha384-T41oglUPvXLGBVyRdZsVRxNWnOOqCynaPubjUVjxhsjFTKrFJGEMm3/0KGmNQ+Pg"
          crossorigin="anonymous"></script>
</head>

<!-- 3. Enable on a container (usually <body>) -->
<body hx-ext="response-targets">
  ...
</body>
```

Multiple extensions: `hx-ext="response-targets, debug"` — enable on any ancestor.

## Core Extensions (Supported by htmx team)

### response-targets

Route responses to different target elements based on HTTP status code.

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-response-targets@2.0.4"
        integrity="sha384-T41oglUPvXLGBVyRdZsVRxNWnOOqCynaPubjUVjxhsjFTKrFJGEMm3/0KGmNQ+Pg"
        crossorigin="anonymous"></script>
```

**Usage:**

```html
<body hx-ext="response-targets">
  <form hx-post="/register"
        hx-target="#response"
        hx-target-422="#errors"
        hx-target-5*="#fatal-error"
        hx-target-error="#generic-error">
    ...
  </form>
  <div id="response"></div>
  <div id="errors"></div>
  <div id="fatal-error"></div>
  <div id="generic-error"></div>
</body>
```

**Attribute syntax:** `hx-target-[CODE]` where `[CODE]` is a numeric status code, optionally with wildcard `*`.

Special aliases:

- `hx-target-error` — matches both 4xx and 5xx
- `hx-target-5*` — wildcard: matches 500, 501, 502, etc.
- `hx-target-422` — specific code

**Selector values** (same extended selectors as `hx-target`):

```html
hx-target-422="this"
hx-target-422="closest .error-container"
hx-target-422="find .field-errors"
hx-target-422="next .error"
hx-target-422="previous .error"
```

**Config options:**

```javascript
htmx.config.responseTargetPrefersRetargetHeader = true  // default: honor HX-Retarget header
htmx.config.responseTargetPrefersExisting = false        // default: override existing target
htmx.config.responseTargetUnsetsError = true             // default: isError=false for matched targets
```

### sse (Server-Sent Events)

Connect to an `EventSource` stream and swap HTML fragments as events arrive.

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-sse@2.2.4"
        integrity="sha384-A986SAtodyH8eg8x8irJnYUk7i9inVQqYigD6qZ9evobksGNIXfeFvDwLSHcp31N"
        crossorigin="anonymous"></script>
```

**Attributes:**

- `sse-connect="<url>"` — URL of the SSE endpoint
- `sse-swap="<event-name>"` — event name to swap into the element
- `hx-trigger="sse:<event-name>"` — use SSE event as trigger for an AJAX request
- `sse-close="<event-name>"` — close the connection when this event is received

**Usage:**

```html
<body hx-ext="sse">
  <!-- Swap content directly when "update" SSE event fires -->
  <div sse-connect="/stream" sse-swap="update">
    Initial content, replaced when SSE "update" event fires.
  </div>

  <!-- Trigger an AJAX request when SSE event fires -->
  <div sse-connect="/notifications">
    <div hx-get="/notifications/latest" hx-trigger="sse:new_notification" hx-target="#notif-list">
      Listening for notifications...
    </div>
  </div>

  <!-- Close connection after receiving "done" event -->
  <div sse-connect="/progress" sse-swap="progress" sse-close="done">
    Waiting for progress...
  </div>
</body>
```

**SSE is uni-directional** — server pushes to client only. For bidirectional, use WebSockets.

**SSE Events:**

- `htmx:sseOpen` — connection established (`detail.source` = EventSource)
- `htmx:sseError` — connection error (`detail.error`, `detail.source`)
- `htmx:sseBeforeMessage` — before message is swapped; `preventDefault()` to cancel swap
- `htmx:sseMessage` — after message is swapped
- `htmx:sseClose` — connection closed (`detail.type`: `"nodeMissing"`, `"nodeReplaced"`, or `"message"`)

**Server-side (Python/FastAPI):**

```python
from fastapi.responses import StreamingResponse
import asyncio

async def event_stream():
    while True:
        data = await get_update()
        yield f"event: update\ndata: <div>New content</div>\n\n"
        await asyncio.sleep(1)

@app.get("/stream")
async def stream():
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

### ws (WebSockets)

Bi-directional communication via WebSocket, with HTML fragment swapping.

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-ws@2.0.4"
        integrity="sha384-1RwI/nvUSrMRuNj7hX1+27J8XDdCoSLf0EjEyF69nacuWyiJYoQ/j39RT1mSnd2G"
        crossorigin="anonymous"></script>
```

**Attributes:**

- `ws-connect="<url>"` — WebSocket URL (optionally prefixed with `ws://` or `wss://`)
- `ws-send` — on child form: send form values to the WebSocket on trigger

**Usage:**

```html
<body hx-ext="ws">
  <div ws-connect="/chatroom">
    <!-- Messages received will be OOB-swapped by id -->
    <div id="messages"></div>
    <div id="user-list"></div>

    <!-- Sending: form values are serialized as JSON + HEADERS field -->
    <form ws-send>
      <input name="message" placeholder="Type a message...">
      <button type="submit">Send</button>
    </form>
  </div>
</body>
```

**Receiving messages:** Server sends HTML fragments. htmx swaps them using OOB logic (match by `id`):

```html
<!-- Server sends: swap into #messages using beforeend -->
<div id="messages" hx-swap-oob="beforeend">
  <p>New message!</p>
</div>
```

**Auto-reconnect:** Automatically reconnects on unexpected closure using exponential backoff with full jitter.

**Custom reconnect delay:**

```javascript
htmx.config.wsReconnectDelay = function(retryCount) {
    return retryCount * 1000;  // linear backoff
}
```

**WebSocket Events:**

- `htmx:wsConnecting` — connection attempt started
- `htmx:wsOpen` — connection established (`detail.elt`, `detail.socketWrapper`)
- `htmx:wsClose` — connection closed (`detail.elt`, `detail.event`, `detail.socketWrapper`)
- `htmx:wsError` — error occurred (`detail.elt`, `detail.error`, `detail.socketWrapper`)
- `htmx:wsBeforeMessage` — before message processed; `preventDefault()` to cancel
- `htmx:wsAfterMessage` — after message fully processed
- `htmx:wsConfigSend` — before sending; modify `detail.parameters` or `detail.messageBody`
- `htmx:wsBeforeSend` — just before sending; cancel to discard
- `htmx:wsAfterSend` — after sending

**Socket wrapper** (via `detail.socketWrapper`):

```javascript
htmx.on('htmx:wsOpen', function(evt) {
    const ws = evt.detail.socketWrapper;
    ws.send('<div>Custom message</div>', evt.detail.elt);
    ws.sendImmediately('<div>Urgent</div>', evt.detail.elt);
    console.log('Queue size:', ws.queue.length);
});
```

### morph (Idiomorph)

DOM morphing swap strategy — updates the DOM in-place rather than replacing it outright. Preserves focus, scroll position, form state, and element identity across swaps.

**CDN:**

```html
<script src="https://unpkg.com/idiomorph@0.7.4/dist/idiomorph-ext.min.js"
        integrity="sha384-SsScJKzATF/w6suEEdLbgYGsYFLzeKfOA6PY+/C5ZPxOSuA+ARquqtz/BZz9JWU8"
        crossorigin="anonymous"></script>
```

**Note:** Idiomorph uses a different CDN (`unpkg.com/idiomorph`) and a different extension name (`morph`, not `htmx-ext-idiomorph`).

**Usage:**

```html
<body hx-ext="morph">
  <!-- morph and morph:outerHTML both morph the element and its children -->
  <button hx-get="/data" hx-swap="morph">Morph</button>

  <!-- morph:innerHTML morphs only children, leaves the element itself unchanged -->
  <button hx-get="/data" hx-swap="morph:innerHTML">Morph Children</button>
</body>
```

**When to use morphing:**

- You need to preserve input focus or scroll position during swaps
- You have complex components (video players, canvas) that shouldn't be recreated
- You're using Alpine.js and need to preserve Alpine state
- You want smoother visual transitions by minimizing DOM mutations

**Tradeoff:** More CPU usage than a simple innerHTML swap.

### preload

Prefetch HTML fragments before the user clicks, making navigation feel instantaneous.

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-preload@2.1.2"
        integrity="sha384-PRIcY6hH1Y5784C76/Y8SqLyTanY9rnI3B8F3+hKZFNED55hsEqMJyqWhp95lgfk"
        crossorigin="anonymous"></script>
```

**Usage:**

```html
<body hx-ext="preload">
  <!-- Preload on mousedown (default: ~100-200ms head start) -->
  <a href="/page" preload>Instant link</a>
  <button hx-get="/fragment" preload>Instant button</button>

  <!-- Preload on hover (more aggressive, 100ms delay) -->
  <a href="/page" preload="mouseover">Hover preload</a>

  <!-- Preload immediately on page load -->
  <button hx-get="/data" preload="preload:init" hx-target="#result">Instant</button>

  <!-- Inherit preload on all children -->
  <ul preload>
    <li><a href="/page1">Page 1</a></li>
    <li><a href="/page2">Page 2</a></li>
  </ul>

  <!-- Also preload linked images -->
  <a href="/gallery" preload="mouseover" preload-images="true">Gallery</a>
</body>
```

**Limitations:**

- Only GET requests can be preloaded
- Preloaded responses only cache if server allows it (`Cache-Control`)
- All preloaded requests include `HX-Preloaded: true` header

### head-support

Merge `<head>` tag content (styles, scripts, meta) from htmx responses into the document head.

**CDN:**

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-head-support@2.0.5"
        crossorigin="anonymous"></script>
```

```html
<body hx-ext="head-support">
  <!-- Responses with <head> sections will have their content merged -->
  <a hx-get="/page-with-styles" hx-target="body">Go</a>
</body>
```

### htmx-1-compat

Rolls back htmx 2's behavioral changes to match htmx 1 defaults. Useful when migrating.

```html
<script src="https://cdn.jsdelivr.net/npm/htmx-ext-htmx-1-compat@2.0.1" crossorigin="anonymous"></script>
<body hx-ext="htmx-1-compat">
```

Key htmx 1→2 changes this extension reverts:

- `selfRequestsOnly` (htmx 2 default: `true`, htmx 1: `false`)
- Default swap style, settle delays, and more

## Notable Community Extensions

### debug

Log all htmx events to `console.debug` for elements with `hx-ext="debug"`:

```html
<!-- Debug a specific component -->
<div hx-ext="debug" hx-get="/data">...</div>
```

Simpler alternative: `htmx.logAll()` in the console.

### loading-states

Manage loading states declaratively during requests (disable elements, add/remove CSS classes):

```html
<body hx-ext="loading-states">
  <form hx-post="/submit">
    <button data-loading-disable>Submit</button>
    <div data-loading-class="opacity-50">Will fade during request</div>
    <div data-loading-class-remove="hidden">Hidden initially, shown during request</div>
    <div data-loading>Shown only during request</div>
    <div data-loading-target="#my-spinner" data-loading-class-remove="hidden">...</div>
  </form>
</body>
```

### class-tools

Animate CSS classes with timing control:

```html
<body hx-ext="class-tools">
  <!-- Add "active" class after 100ms -->
  <div classes="add active:100ms">...</div>

  <!-- Toggle "open" class -->
  <div classes="toggle open">...</div>

  <!-- Remove after 2 seconds -->
  <div class="alert" classes="remove alert:2000ms">...</div>
</body>
```

### remove-me

Remove an element from the DOM after a specified interval:

```html
<body hx-ext="remove-me">
  <!-- Automatically disappear after 2 seconds -->
  <div class="flash-message" remove-me="2s">Saved successfully!</div>
</body>
```

### path-params

Use request parameters to populate URL path variables:

```html
<body hx-ext="path-params">
  <!-- /items/{id} → /items/42 (id removed from query params) -->
  <form hx-get="/items/{id}">
    <input name="id" value="42">
    <button type="submit">Get</button>
  </form>
</body>
```

### multi-swap

Swap multiple elements from a response using different swap strategies:

```html
<body hx-ext="multi-swap">
  <!-- Swap #el1 with innerHTML and #el2 with outerHTML -->
  <button hx-get="/data" hx-swap="multi:#el1:innerHTML,#el2:outerHTML">Load</button>
</body>
```

## Creating Custom Extensions

```javascript
htmx.defineExtension('my-extension', {
    // Called when extension is initialized on an element
    onEvent: function(name, evt) {
        if (name === 'htmx:beforeRequest') {
            // modify request
            evt.detail.headers['X-My-Header'] = 'custom';
        }
    },

    // Modify a parameter set before it is sent
    encodeParameters: function(xhr, parameters, elt) {
        return null;  // return null to use default encoding
    },

    // Transform a response before it is swapped
    transformResponse: function(text, xhr, elt) {
        return text;  // return modified HTML
    },

    // Override the swap mechanism
    handleSwap: function(swapStyle, target, fragment, settleInfo) {
        return false;  // return false to use default swap
    },

    // Return the path for a request
    getSelectors: function() {
        return null;
    }
});
```
