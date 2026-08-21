# HTMX UI Patterns Reference

Common patterns implemented with htmx + server-side HTML (FastAPI/Jinja2 examples).

## Active Search

Trigger a search request on keyup, debounced, only when value changes.

```html
<!-- Template -->
<input type="text" name="q"
       hx-get="/search"
       hx-trigger="keyup changed delay:500ms"
       hx-target="#results"
       placeholder="Search...">
<div id="results"></div>
```

```python
# FastAPI
@app.get("/search")
async def search(q: str = "", request: Request):
    results = await db.search(q)
    return templates.TemplateResponse("_search_results.html", {
        "request": request, "results": results
    })
```

Progressive enhancement — wrap in a form so it works without JS:

```html
<form action="/search" method="GET">
  <input type="text" name="q"
         hx-get="/search"
         hx-trigger="keyup changed delay:500ms, search"
         hx-target="#results">
  <button type="submit">Search</button>
</form>
<div id="results"></div>
```

## Click to Load More / Infinite Scroll

**Click to load:**

```html
<table>
  <tbody id="rows">
    {% for item in items %}
    <tr>...</tr>
    {% endfor %}
  </tbody>
</table>

<button hx-get="/items?page={{ next_page }}"
        hx-target="#rows"
        hx-swap="beforeend"
        hx-indicator=".spinner">
  Load More
  <img class="htmx-indicator spinner" src="/spinner.gif">
</button>
```

**Infinite scroll** (trigger on last row scrolling into view):

```html
{% for item in items %}
<tr>
  <!-- only the last row has the trigger -->
  {% if loop.last %}
  <td hx-get="/items?page={{ next_page }}"
      hx-trigger="revealed"
      hx-target="closest tbody"
      hx-swap="beforeend">{{ item.name }}</td>
  {% else %}
  <td>{{ item.name }}</td>
  {% endif %}
</tr>
{% endfor %}
```

Server returns just `<tr>` rows (no wrapping element needed for `beforeend`).

## Polling

**Fixed interval polling** — poll every N seconds, server returns 286 to stop:

```html
<div hx-get="/job-status/{{ job_id }}"
     hx-trigger="every 2s"
     hx-target="this"
     hx-swap="outerHTML">
  Checking status...
</div>
```

```python
@app.get("/job-status/{job_id}")
async def job_status(job_id: int):
    job = await db.get_job(job_id)
    if job.done:
        # Return 286 to stop polling, replace with final state
        return HTMLResponse(
            content=render("_job_complete.html", job=job),
            status_code=286
        )
    return templates.TemplateResponse("_job_status.html", {"job": job})
```

**Load polling** (element replaces itself with a version that polls again):

```html
<div hx-get="/progress"
     hx-trigger="load delay:1s"
     hx-swap="outerHTML">
  Loading...
</div>
```

Server returns the same template until done, then returns a different (non-polling) template.

## Progress Bar

```html
<!-- _progress.html -->
<div id="progress-container">
  <div id="progress-bar"
       hx-get="/job/{{ job_id }}/progress"
       hx-trigger="every 500ms"
       hx-target="#progress-container"
       hx-swap="outerHTML"
       style="width: {{ progress }}%">
    {{ progress }}%
  </div>
</div>
```

Server returns the entire `#progress-container` (with updated width) until 100%, then swaps in a completion message with HTTP 286 to stop polling.

## Inline Editing (Click to Edit)

```html
<!-- _item_view.html (read mode) -->
<div id="item-{{ item.id }}" hx-swap-oob="outerHTML:#item-{{ item.id }}">
  <span>{{ item.name }}</span>
  <button hx-get="/items/{{ item.id }}/edit"
          hx-target="#item-{{ item.id }}"
          hx-swap="outerHTML">Edit</button>
</div>
```

```html
<!-- _item_edit.html (edit mode) -->
<form id="item-{{ item.id }}"
      hx-patch="/items/{{ item.id }}"
      hx-target="#item-{{ item.id }}"
      hx-swap="outerHTML">
  <input name="name" value="{{ item.name }}">
  <button type="submit">Save</button>
  <button hx-get="/items/{{ item.id }}"
          hx-target="#item-{{ item.id }}"
          hx-swap="outerHTML"
          type="button">Cancel</button>
</form>
```

```python
@app.patch("/items/{item_id}")
async def update_item(item_id: int, name: str = Form(...)):
    item = await db.update_item(item_id, name=name)
    return templates.TemplateResponse("_item_view.html", {"item": item})
```

## Delete Row

```html
<!-- _row.html -->
<tr id="row-{{ item.id }}" hx-swap-oob="outerHTML:#row-{{ item.id }}">
  <td>{{ item.name }}</td>
  <td>
    <button hx-delete="/items/{{ item.id }}"
            hx-target="closest tr"
            hx-swap="outerHTML"
            hx-confirm="Delete {{ item.name }}?">
      Delete
    </button>
  </td>
</tr>
```

```python
@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    await db.delete_item(item_id)
    return HTMLResponse("")  # empty response → swap outerHTML → row removed
```

## Form Validation (Inline)

**Pattern:** Server returns 422 with the re-rendered form containing error messages.

```html
<!-- form.html -->
<form hx-post="/register"
      hx-target="this"
      hx-swap="outerHTML">
  <div class="form-group">
    <label>Email</label>
    <input type="email" name="email" value="{{ form.email }}">
    {% if form.errors.email %}
    <span class="error">{{ form.errors.email }}</span>
    {% endif %}
  </div>
  <button type="submit">Register</button>
</form>
```

```python
@app.post("/register")
async def register(email: str = Form(...)):
    errors = {}
    if await db.email_exists(email):
        errors["email"] = "Email already registered"
    if errors:
        return templates.TemplateResponse(
            "form.html",
            {"form": {"email": email, "errors": errors}},
            status_code=422
        )
    user = await db.create_user(email=email)
    return HTMLResponse('<p class="success">Registered! Check your email.</p>')
```

Server config needed to swap 422 responses (one of these approaches):

```html
<!-- Meta config approach -->
<meta name="htmx-config" content='{"responseHandling":[
  {"code":"204","swap":false},
  {"code":"[23]..","swap":true},
  {"code":"422","swap":true},
  {"code":"[45]..","swap":false,"error":true},
  {"code":"...","swap":true}
]}'>
```

## OOB Swaps Pattern (Toasts, Badges, Multiple Updates)

Update multiple parts of the page from a single request without the primary response needing to target all of them.

```html
<!-- toast template: _toast.html -->
<div id="toast" hx-swap-oob="true" class="alert alert-{{ level }}">
  {{ message }}
</div>

<!-- badge template: _badge.html -->
<span id="inbox-count" hx-swap-oob="true">{{ count }}</span>
```

```python
@app.post("/approve/{item_id}")
async def approve_item(item_id: int, request: Request):
    item = await db.approve_item(item_id)
    count = await db.pending_count()

    # Render the primary response + OOB fragments
    row = templates.get_template("_item_row.html").render({"item": item})
    toast = templates.get_template("_toast.html").render({
        "level": "success", "message": f"Approved {item.name}"
    })
    badge = templates.get_template("_badge.html").render({"count": count})

    return HTMLResponse(row + toast + badge)
```

Triggering element uses `hx-target="none" hx-swap="none"` when it shouldn't swap anything itself:

```html
<button hx-post="/approve/{{ item.id }}" hx-target="none" hx-swap="none">Approve</button>
```

## Tabs

```html
<!-- tabs.html -->
<div>
  <div role="tablist">
    <a hx-get="/tabs/overview"
       hx-target="#tab-content"
       hx-push-url="/dashboard/overview"
       class="tab {{ 'tab-active' if active_tab == 'overview' }}">Overview</a>
    <a hx-get="/tabs/details"
       hx-target="#tab-content"
       hx-push-url="/dashboard/details"
       class="tab {{ 'tab-active' if active_tab == 'details' }}">Details</a>
  </div>
  <div id="tab-content">
    {{ tab_content | safe }}
  </div>
</div>
```

```python
@app.get("/tabs/{tab_name}")
async def tab(tab_name: str, request: Request):
    content = templates.get_template(f"_tab_{tab_name}.html").render({"request": request})
    if request.headers.get("HX-Request"):
        return HTMLResponse(content)
    # Full page render
    return templates.TemplateResponse("tabs.html", {
        "request": request,
        "active_tab": tab_name,
        "tab_content": content
    })
```

## Keyboard Shortcuts

```html
<!-- Listen on body, trigger on keyup with filter -->
<div hx-get="/search-modal"
     hx-trigger="keyup[key=='/'] from:body"
     hx-target="#modal-container"
     hx-swap="innerHTML">
</div>

<!-- Close modal on Escape -->
<div id="modal-container"
     hx-get="/empty"
     hx-trigger="keyup[key=='Escape'] from:body"
     hx-target="this"
     hx-swap="innerHTML">
  <!-- modal content -->
</div>
```

## Dependent Dropdowns (Cascading Selects)

```html
<form>
  <select name="country"
          hx-get="/states"
          hx-trigger="change"
          hx-target="#state-select">
    <option value="">Select country...</option>
    <option value="US">United States</option>
    <option value="CA">Canada</option>
  </select>

  <select id="state-select" name="state">
    <option value="">Select state...</option>
  </select>
</form>
```

```python
@app.get("/states")
async def states(country: str, request: Request):
    states = get_states_for_country(country)
    return templates.TemplateResponse("_state_options.html", {"states": states})
```

## Modal Dialogs

```html
<!-- modal container (always present in DOM) -->
<div id="modal-container"></div>

<!-- trigger -->
<button hx-get="/items/new"
        hx-target="#modal-container"
        hx-swap="innerHTML">
  New Item
</button>
```

```html
<!-- _modal.html (returned by server) -->
<dialog id="my-modal" open>
  <form hx-post="/items" hx-target="#items-list" hx-swap="beforeend">
    <input name="name" placeholder="Item name">
    <button type="submit"
            hx-on:htmx:after-request="document.getElementById('my-modal').close()">
      Create
    </button>
  </form>
  <button onclick="this.closest('dialog').close()">Cancel</button>
</dialog>
<script>document.getElementById('my-modal').showModal()</script>
```

## File Upload with Progress

```html
<form hx-post="/upload"
      hx-encoding="multipart/form-data"
      hx-target="#upload-result">
  <input type="file" name="file">
  <button type="submit">Upload</button>
  <div id="upload-progress" class="htmx-indicator">
    <progress id="progress-bar" value="0" max="100"></progress>
  </div>
</form>
<div id="upload-result"></div>

<script>
htmx.on('htmx:xhr:progress', function(evt) {
    if (evt.detail.lengthComputable) {
        const pct = Math.round((evt.detail.loaded / evt.detail.total) * 100);
        document.querySelector('#progress-bar').value = pct;
    }
});
</script>
```

## Async Confirmation Dialog

Replace the browser's `confirm()` with a custom dialog using `htmx:confirm`:

```javascript
document.body.addEventListener('htmx:confirm', function(evt) {
    if (!evt.target.hasAttribute('hx-confirm')) return;
    evt.preventDefault();
    // Show your custom dialog
    myDialog.show(evt.target.getAttribute('hx-confirm')).then(confirmed => {
        if (confirmed) evt.detail.issueRequest();
    });
});
```

```html
<button hx-delete="/item/42" hx-confirm="Delete this item?">Delete</button>
```

## Integrating 3rd Party JS Libraries

The key insight: initialize libraries on new htmx content using `htmx.onLoad`, not `$(document).ready`.

```javascript
// Wrong: doesn't catch htmx-loaded content
$(document).ready(function() {
    $('.datepicker').datepicker();
});

// Right: runs on initial page AND on every htmx swap
htmx.onLoad(function(target) {
    target.querySelectorAll('.datepicker').forEach(elt => $(elt).datepicker());
});
```

**Sortable.js integration:**

```html
<form class="sortable" hx-post="/reorder" hx-trigger="end">
  <div><input type="hidden" name="id" value="1">Item 1</div>
  <div><input type="hidden" name="id" value="2">Item 2</div>
  <div><input type="hidden" name="id" value="3">Item 3</div>
</form>
```

```javascript
htmx.onLoad(function(target) {
    target.querySelectorAll('.sortable').forEach(elt => {
        new Sortable(elt, {animation: 150, ghostClass: 'dragging'});
    });
});
```

The `end` event is fired by Sortable when drag ends — htmx picks it up via `hx-trigger="end"`.

## History with Partials

Serve full pages on direct navigation, partials on htmx requests:

```python
@app.get("/dashboard")
async def dashboard(request: Request):
    data = await get_dashboard_data()

    # htmx request: return only the page content
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("_dashboard_content.html", {
            "request": request, **data
        })

    # Full page request: include layout
    return templates.TemplateResponse("dashboard.html", {
        "request": request, **data
    })
```

**Critical:** `htmx.config.historyRestoreAsHxRequest` defaults to `true` in htmx 2. This means history restoration also sends `HX-Request: true`, which would get a partial instead of a full page. Disable it:

```html
<meta name="htmx-config" content='{"historyRestoreAsHxRequest": false}'>
```

Then use `HX-History-Restore-Request` to detect history restores specifically if needed.

## HTMX + Alpine.js Integration

HTMX and Alpine.js are designed to complement each other: **HTMX handles server communication** (fetching and swapping HTML), **Alpine handles local UI state** (open/closed, active tab, form validation feedback, etc.). Keep the boundary clean — don't use Alpine to make fetch calls, and don't use HTMX `hx-on` for complex stateful logic.

### The Division of Responsibility

```text
HTMX  → server requests, HTML swaps, history, form submission
Alpine → dropdowns, modals, tabs, inline toggles, transient UI state
```

Rule of thumb: if it needs a round trip to the server, it's HTMX. If it's purely visual state, it's Alpine.

### Alpine State + HTMX Request on Same Element

Alpine and HTMX attributes coexist on the same element. Alpine manages `open`; HTMX loads the content.

```html
<div x-data="{ open: false }">
    <button @click="open = !open"
            hx-get="/menu-items"
            hx-target="#menu"
            hx-trigger="click[!open]">
        Menu
    </button>
    <div id="menu" x-show="open" @click.outside="open = false"></div>
</div>
```

Here `hx-trigger="click[!open]"` only fires the request when the menu is currently closed (first open). Alpine handles subsequent open/close without network traffic.

### Initializing Alpine on HTMX-Swapped Content

Alpine automatically initializes on newly injected DOM nodes via a `MutationObserver` — no extra setup needed. However, if you use `x-cloak` on swapped partials, ensure the CSS rule is already in the main page's `<head>`:

```html
<style>[x-cloak] { display: none !important; }</style>
```

### Passing Server Data to Alpine State

Jinja2 renders the initial Alpine data object server-side:

```html
<!-- Server renders the initial state inline -->
<div x-data="{ items: {{ items | tojson }}, selected: null }">
    <template x-for="item in items" :key="item.id">
        <div @click="selected = item" :class="{ 'bg-base-200': selected?.id === item.id }">
            <span x-text="item.name"></span>
        </div>
    </template>
</div>
```

For reactive updates, let HTMX swap in a fresh partial that re-declares `x-data` with new server state.

### Reacting to HTMX Events in Alpine

HTMX fires DOM events at lifecycle points. Alpine's `x-on`/`@` can listen to them:

```html
<!-- Reset Alpine state after HTMX swaps content into this element -->
<div x-data="{ loading: false }"
     @htmx:before-request="loading = true"
     @htmx:after-request="loading = false"
     hx-get="/data"
     hx-trigger="load">
    <span x-show="loading">Loading...</span>
    <div id="data-container"></div>
</div>
```

Common HTMX events useful in Alpine:

- `htmx:before-request` — just before a request fires
- `htmx:after-request` — after response received (whether success or error)
- `htmx:after-swap` — after HTML has been swapped into the DOM
- `htmx:before-swap` — before the swap, can cancel it

### Triggering HTMX Requests from Alpine

Use `htmx.trigger()` to fire an htmx-enabled element programmatically from Alpine JS:

```html
<div x-data="{ confirmed: false }">
    <button @click="confirmed = true; htmx.trigger($refs.deleteBtn, 'confirmed')">
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

### Dispatching Custom Events Across the Alpine/HTMX Boundary

Alpine's `$dispatch` fires bubbling DOM events, which htmx can listen to via `hx-trigger`:

```html
<!-- Alpine dispatches; HTMX listens -->
<div x-data hx-get="/refresh" hx-trigger="refresh-list">
    ...
</div>

<button x-data @click="$dispatch('refresh-list')">Refresh</button>
```

And vice versa — htmx's `HX-Trigger` response header can fire events that Alpine catches:

```python
# Server sets header: HX-Trigger: {"showToast": {"message": "Saved!"}}
return HTMLResponse(content, headers={"HX-Trigger": '{"showToast": {"message": "Saved!"}}'})
```

```html
<div x-data="{ toast: null }"
     @show-toast.window="toast = $event.detail.message; setTimeout(() => toast = null, 3000)">
    <div x-show="toast" x-text="toast" class="alert alert-success"></div>
</div>
```

Note: HTMX fires `HX-Trigger` events in camelCase on the DOM but Alpine hears them as kebab-case (use `@show-toast` for an event named `showToast`).

### Preserving Alpine State Across HTMX Swaps (Idiomorph)

Normal HTMX swaps (`innerHTML`/`outerHTML`) destroy and recreate DOM nodes, which resets Alpine state. Use the **Idiomorph** morph extension when you need to preserve Alpine component state across a swap:

```html
<body hx-ext="morph">
    <div x-data="{ count: 0 }">
        <button @click="count++">+</button>
        <span x-text="count"></span>
        <!-- HTMX swaps this div's content; Alpine state (count) is preserved -->
        <div hx-get="/refresh" hx-swap="morph:innerHTML" hx-trigger="every 5s">
            <!-- server-rendered content -->
        </div>
    </div>
</body>
```

Without morph, every swap resets `count` to 0. With morph, the DOM is patched in-place.

### Inline Alpine Script in HTMX Partials

When Alpine needs to run JS that can't be expressed inline (e.g., arrow key navigation, third-party init), embed a self-contained IIFE in the partial. Bridge back to HTMX by triggering clicks on elements with `hx-*` attributes rather than making fetch calls directly.

```html
<!-- _autocomplete_results.html -->
<ul id="results" role="listbox">
    {% for item in items %}
    <li role="option"
        hx-get="/select/{{ item.id }}"
        hx-target="#selected"
        x-data
        @click="$el.dispatchEvent(new Event('result:selected', {bubbles:true}))">
        {{ item.name }}
    </li>
    {% endfor %}
</ul>

<script>
(function() {
    const list = document.getElementById('results');
    if (!list) return;
    list.addEventListener('keydown', function(e) {
        const items = list.querySelectorAll('[role=option]');
        const active = list.querySelector('[aria-selected=true]');
        const idx = Array.from(items).indexOf(active);
        if (e.key === 'ArrowDown') items[Math.min(idx + 1, items.length - 1)]?.focus();
        if (e.key === 'ArrowUp')   items[Math.max(idx - 1, 0)]?.focus();
        if (e.key === 'Enter')     active?.click();
    });
})();
</script>
```
