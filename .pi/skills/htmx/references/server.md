# HTMX Server Integration Reference

How htmx communicates with the server: request headers sent, response headers understood, error handling, CSRF, CORS.

## Request Headers (htmx sends these)

| Header | Description |
|---|---|
| `HX-Boosted` | `"true"` if request is via `hx-boost` element |
| `HX-Current-URL` | Current URL of the browser |
| `HX-History-Restore-Request` | `"true"` if restoring from history cache miss |
| `HX-Prompt` | User's response to `hx-prompt` dialog |
| `HX-Request` | Always `"true"` (except history restores if `historyRestoreAsHxRequest=false`) |
| `HX-Target` | The `id` of the target element (if it has one) |
| `HX-Trigger` | The `id` of the triggering element (if it has one) |
| `HX-Trigger-Name` | The `name` of the triggering element (if it has one) |

**Use `HX-Request` on the server to detect htmx requests and return partials:**

```python
# FastAPI example
@app.get("/blog")
async def blog(request: Request):
    if request.headers.get("HX-Request"):
        return templates.TemplateResponse("_blog_partial.html", {"request": request})
    return templates.TemplateResponse("blog.html", {"request": request})
```

> **Important:** Set `htmx.config.historyRestoreAsHxRequest = false` if you use `HX-Request` to conditionally return partials. Otherwise history restoration will get a partial instead of a full page.

## Response Headers (htmx understands these)

| Header | Description |
|---|---|
| `HX-Location` | Client-side redirect without full page reload. Value: URL string or JSON `{path, target, swap, ...}` |
| `HX-Push-Url` | Push a URL into browser history |
| `HX-Replace-Url` | Replace current URL in browser bar |
| `HX-Redirect` | Client-side redirect (full page reload behavior) |
| `HX-Refresh` | If `"true"`, trigger a full page refresh |
| `HX-Retarget` | CSS selector — override the swap target for this response |
| `HX-Reswap` | Override the swap method for this response (any `hx-swap` value) |
| `HX-Reselect` | CSS selector — pick a subset of the response to swap in |
| `HX-Trigger` | Trigger client-side events after the response is received |
| `HX-Trigger-After-Settle` | Trigger client-side events after settle phase |
| `HX-Trigger-After-Swap` | Trigger client-side events after swap phase |

**Examples:**

```python
from fastapi.responses import HTMLResponse

# Redirect without page reload
response.headers["HX-Redirect"] = "/dashboard"

# Push a URL into history
response.headers["HX-Push-Url"] = "/items/42"

# Trigger a client-side event
response.headers["HX-Trigger"] = "itemCreated"

# Trigger multiple events with data (JSON string)
response.headers["HX-Trigger"] = '{"showMessage": {"level": "info", "message": "Saved!"}}'

# Override target and swap for this response
response.headers["HX-Retarget"] = "#error-banner"
response.headers["HX-Reswap"] = "innerHTML"
```

## Response Status Code Handling

Default behavior:

- **204 No Content** — do nothing (no swap), not an error
- **2xx, 3xx** — swap the response into the DOM
- **4xx, 5xx** — do NOT swap, treat as error, fire `htmx:responseError`

### Customizing Response Handling

```javascript
htmx.config.responseHandling = [
    {code: "204", swap: false},             // 204: no swap, not an error
    {code: "[23]..", swap: true},           // 2xx/3xx: swap
    {code: "422", swap: true},             // 422: swap (for validation errors)
    {code: "[45]..", swap: false, error: true},  // other 4xx/5xx: error
    {code: "...", swap: false}              // catch-all
];
```

Via meta tag (recommended for server-side configuration):

```html
<meta name="htmx-config" content='{
    "responseHandling": [
        {"code": "204", "swap": false},
        {"code": "[23]..", "swap": true},
        {"code": "422", "swap": true},
        {"code": "[45]..", "swap": false, "error": true},
        {"code": "...", "swap": true}
    ]
}'>
```

Swap everything regardless of status code:

```html
<meta name="htmx-config" content='{"responseHandling": [{"code":".*", "swap": true}]}'>
```

Response handling entry fields:

- `code` — regex matched against HTTP status code
- `swap` — whether to swap the response
- `error` — whether to treat as an error
- `ignoreTitle` — ignore `<title>` in response
- `select` — CSS selector to filter response content
- `target` — CSS selector for alternative target
- `swapOverride` — alternative swap method

## The 422 Pattern (Validation Errors)

The most common pattern for server-side form validation with htmx is to return `422 Unprocessable Entity` with the re-rendered form (including error messages). By default htmx won't swap 422s, so you need to configure it.

**Option 1: `htmx.config.responseHandling`** (shown above) — configure globally.

**Option 2: `response-targets` extension** — declarative per-element targeting:

```html
<body hx-ext="response-targets">
  <form hx-post="/register" hx-target="#response" hx-target-422="#error-div">
    ...
  </form>
  <div id="response"></div>
  <div id="error-div"></div>
</body>
```

**Option 3: `htmx:beforeSwap` event** — programmatic, fine-grained:

```javascript
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }
});
```

## CSRF

Return CSRF tokens with every htmx request using `hx-headers` on a parent element:

```html
<!-- Jinja2 template -->
<body hx-headers='{"X-CSRF-TOKEN": "{{ csrf_token }}"}'>
  ...
</body>
```

> Note: `hx-boost` does not update `<html>` or `<body>` — put the CSRF token on an element that gets replaced, or use a persistent parent container.

## CORS

When htmx makes cross-origin requests, you must configure CORS headers on your server:

```http
Access-Control-Allow-Headers: HX-Boosted, HX-Current-URL, HX-History-Restore-Request, HX-Prompt, HX-Request, HX-Target, HX-Trigger-Name, HX-Trigger
Access-Control-Expose-Headers: HX-Location, HX-Push-Url, HX-Redirect, HX-Refresh, HX-Replace-Url, HX-Reswap, HX-Retarget, HX-Reselect, HX-Trigger, HX-Trigger-After-Settle, HX-Trigger-After-Swap
```

## Caching

If you serve both full pages and partials at the same URL (based on `HX-Request`), use `Vary`:

```http
Vary: HX-Request
```

Alternatively, enable the cache-buster param:

```javascript
htmx.config.getCacheBusterParam = true
// Adds: ?org.htmx.cache-buster=<targetId> to GET requests
```

## Request Lifecycle (Order of Operations)

1. Element triggered → gather parameter values
2. `htmx-request` class applied to indicator element
3. AJAX request sent asynchronously
4. Response received → `htmx-swapping` class applied to target
5. Optional `swap` delay (see `hx-swap`)
6. Content swapped
7. `htmx-swapping` removed, `htmx-added` added to new content, `htmx-settling` applied
8. Optional `settle` delay (default: 20ms)
9. DOM settled → `htmx-settling` and `htmx-added` removed

Use `htmx-swapping` and `htmx-settling` classes in CSS for transition effects.

## Validation

htmx integrates with the HTML5 Validation API. Requests are not issued if form inputs are invalid.

**Enable browser validation reporting** (recommended — matches default browser behavior):

```javascript
htmx.config.reportValidityOfForms = true
```

Non-form elements don't validate by default. Opt in:

```html
<input hx-post="/check" hx-validate="true">
```

Events:

- `htmx:validation:validate` — before `checkValidity()` is called
- `htmx:validation:failed` — when `checkValidity()` returns false
- `htmx:validation:halted` — when request is blocked by validation errors

Custom validation:

```html
<form id="my-form" hx-post="/submit">
    <input name="code"
           onkeyup="this.setCustomValidity('')"
           hx-on:htmx:validation:validate="if(this.value.length < 4) {
               this.setCustomValidity('Must be at least 4 chars');
               htmx.find('#my-form').reportValidity();
           }">
</form>
```

## No Post/Redirect/Get Required

With htmx you don't need the PRG pattern. After a successful POST, return the updated HTML directly (200 OK) rather than a redirect. Response headers like `HX-Push-Url` can update the browser URL without a redirect.

> Note: Response headers (HX-Trigger, etc.) are NOT forwarded through 3xx redirects. The browser intercepts the redirect internally. Use 200 responses when you need htmx response headers to be processed.
