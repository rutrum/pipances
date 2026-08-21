# HTMX Events & JavaScript API Reference

## JavaScript API

### Core Methods

```javascript
// Issue an htmx-style AJAX request programmatically
htmx.ajax('GET', '/api/items', '#target-div')
htmx.ajax('POST', '/api/items', {target: '#output', swap: 'outerHTML', values: {name: 'foo'}})

// Process htmx attributes on dynamically added content
htmx.process(document.querySelector('#new-content'))

// Trigger an event on an element
htmx.trigger('#my-element', 'htmx:abort')
htmx.trigger('#my-element', 'myCustomEvent', {detail: {value: 42}})

// DOM helpers
htmx.find('#my-id')                        // querySelector
htmx.find(elt, '.child-selector')          // scoped find
htmx.findAll('.my-class')                  // querySelectorAll
htmx.findAll(elt, '.child-selector')       // scoped findAll
htmx.closest(elt, '.ancestor')             // closest ancestor

// Class manipulation
htmx.addClass(elt, 'my-class')
htmx.removeClass(elt, 'my-class')
htmx.toggleClass(elt, 'my-class')
htmx.takeClass(elt, 'active')              // add to elt, remove from siblings

// Event helpers
htmx.on('htmx:load', function(evt) { ... })           // add event listener, returns listener
htmx.on('#my-elt', 'htmx:load', function(evt) { ... }) // scoped to element
htmx.off('htmx:load', myListener)                      // remove listener
htmx.onLoad(function(target) { ... })                  // shorthand for htmx:load

// DOM manipulation
htmx.remove(elt)                           // remove element from DOM
htmx.remove(elt, 500)                      // remove after delay (ms)

// Swap content programmatically
htmx.swap('#target', '<div>New content</div>', {swapStyle: 'innerHTML'})

// Logging
htmx.logAll()                              // log all htmx events to console
htmx.logger = function(elt, event, data) { console.log(event, elt, data) }

// Values
htmx.values(elt)                           // get all input values associated with element
htmx.values(elt, 'post')                   // include method-specific values

// Extensions
htmx.defineExtension('my-ext', { ... })
htmx.removeExtension('my-ext')
```

### Initialize 3rd Party Libraries on New Content

```javascript
// Called every time htmx loads new content into the DOM
htmx.onLoad(function(target) {
    // target is the newly added element
    target.querySelectorAll('.select2').forEach(elt => $(elt).select2());
    target.querySelectorAll('.sortable').forEach(elt => new Sortable(elt, {animation: 150}));
});
```

### Process Dynamically Injected HTML

If JS adds content with `hx-*` attributes (e.g. from `fetch()` or a template library):

```javascript
let container = document.getElementById('my-container');
fetch('/fragment').then(r => r.text()).then(html => {
    container.innerHTML = html;
    htmx.process(container);  // required to activate htmx on new content
});
```

## Lifecycle Events

Events fire in this order for a typical request:

1. `htmx:confirm` — after trigger, before request; call `evt.preventDefault()` to cancel
2. `htmx:configRequest` — before sending; modify params/headers here
3. `htmx:beforeRequest` — request about to be sent
4. `htmx:beforeSend` — just before XHR send
5. `htmx:xhr:loadstart` — XHR started
6. `htmx:xhr:progress` — upload/download progress
7. `htmx:xhr:loadend` — XHR finished
8. `htmx:beforeOnLoad` — response received, before processing
9. `htmx:beforeSwap` — before DOM swap; configure swap behavior here
10. `htmx:beforeTransition` — before View Transition swap (if enabled)
11. `htmx:afterSwap` — after content is swapped in
12. `htmx:afterOnLoad` — after response fully processed
13. `htmx:afterSettle` — after DOM has settled
14. `htmx:afterRequest` — request complete (fires for both success and error)

All events fire in both camelCase and kebab-case:

```javascript
// Both of these work:
htmx.on('htmx:afterSwap', handler)
htmx.on('htmx:after-swap', handler)   // Alpine.js requires kebab-case
```

## Event Reference

### htmx:load

Fired every time an element is loaded into the DOM by htmx. Equivalent to `DOMContentLoaded` for htmx content.

```javascript
htmx.on('htmx:load', function(evt) {
    myLib.init(evt.detail.elt);  // evt.detail.elt = the loaded element
});
```

### htmx:configRequest

Fired before a request; modify parameters and headers here.

```javascript
document.body.addEventListener('htmx:configRequest', function(evt) {
    evt.detail.parameters['auth_token'] = getAuthToken();
    evt.detail.headers['X-Custom-Header'] = 'value';
    // evt.detail.verb — HTTP method
    // evt.detail.path — URL
    // evt.detail.elt — triggering element
    // evt.detail.target — target element
});
```

### htmx:confirm

Fired on every trigger before the request. Use for async confirmation dialogs.

```javascript
document.body.addEventListener('htmx:confirm', function(evt) {
    if (evt.target.matches('[data-confirm]')) {
        evt.preventDefault();
        myDialog.show(evt.target.dataset.confirm).then(confirmed => {
            if (confirmed) evt.detail.issueRequest();
        });
    }
});
```

### htmx:beforeSwap

Fired before content is swapped in. Use to modify swap behavior based on response.

```javascript
document.body.addEventListener('htmx:beforeSwap', function(evt) {
    // evt.detail.xhr — the XHR object
    // evt.detail.target — target element
    // evt.detail.shouldSwap — set to true/false to override
    // evt.detail.isError — set to false to suppress error logging

    if (evt.detail.xhr.status === 422) {
        evt.detail.shouldSwap = true;
        evt.detail.isError = false;
    }
    if (evt.detail.xhr.status === 418) {
        evt.detail.shouldSwap = true;
        evt.detail.target = htmx.find('#teapot');
    }
});
```

### htmx:afterSwap

Fired after new content is swapped in.

```javascript
htmx.on('htmx:afterSwap', function(evt) {
    // evt.detail.elt — triggering element
    // evt.detail.target — element that was swapped
    // evt.detail.xhr — the XHR response
});
```

### htmx:afterSettle

Fired after the DOM has finished settling (CSS transitions complete).

### htmx:afterRequest

Fired after every request completes (success or error).

```javascript
htmx.on('htmx:afterRequest', function(evt) {
    if (evt.detail.successful) {
        showSuccessNotification();
    } else {
        showErrorNotification(evt.detail.xhr.status);
    }
    // evt.detail.successful — boolean
    // evt.detail.failed — boolean
    // evt.detail.error — error message (if any)
});
```

### htmx:responseError

Fired on non-2xx/3xx response codes (per `responseHandling` config).

```javascript
htmx.on('htmx:responseError', function(evt) {
    console.error('Request failed:', evt.detail.xhr.status, evt.detail.xhr.responseText);
});
```

### htmx:sendError

Fired on network error (no response received — connection failed, CORS blocked, etc.).

```javascript
htmx.on('htmx:sendError', function(evt) {
    console.error('Network error for request to:', evt.detail.requestConfig.path);
});
```

### htmx:timeout

Fired when a request times out (requires `htmx.config.timeout` to be set).

### htmx:validateUrl

Fired before a request to validate the URL. Cancel to block the request.

```javascript
document.body.addEventListener('htmx:validateUrl', function(evt) {
    if (!evt.detail.sameHost && evt.detail.url.hostname !== 'trusted.example.com') {
        evt.preventDefault();
    }
});
```

### htmx:abort

Send to an element to cancel its in-flight request:

```javascript
htmx.trigger('#my-button', 'htmx:abort');
```

Or in HTML:

```html
<button onclick="htmx.trigger('#request-btn', 'htmx:abort')">Cancel</button>
```

## History Events

| Event | Fired when |
|---|---|
| `htmx:pushedIntoHistory` | URL pushed into history |
| `htmx:replacedInHistory` | URL replaced in history |
| `htmx:historyRestore` | History restoration starts |
| `htmx:beforeHistorySave` | Before snapshot is saved to localStorage |
| `htmx:historyCacheHit` | History cache hit |
| `htmx:historyCacheMiss` | History cache miss (remote load needed) |
| `htmx:historyCacheMissLoad` | Remote history load succeeded |
| `htmx:historyCacheMissLoadError` | Remote history load failed |
| `htmx:historyCacheError` | Error writing to history cache |

**Clean up 3rd party mutations before history snapshot:**

```javascript
htmx.on('htmx:beforeHistorySave', function() {
    // destroy any library-mutated DOM before snapshotting
    document.querySelectorAll('.tom-select').forEach(elt => elt.tomselect.destroy());
});
```

## OOB Swap Events

| Event | Fired when |
|---|---|
| `htmx:oobBeforeSwap` | Before OOB element swap; configure swap |
| `htmx:oobAfterSwap` | After OOB element is swapped in |
| `htmx:oobErrorNoTarget` | OOB element has no matching ID in DOM |

## XHR Progress Events

```javascript
htmx.on('htmx:xhr:progress', function(evt) {
    if (evt.detail.lengthComputable) {
        const percent = (evt.detail.loaded / evt.detail.total) * 100;
        document.querySelector('#progress').style.width = percent + '%';
    }
});
```

## Debugging

```javascript
// Log every htmx event
htmx.logAll();

// Custom logger
htmx.logger = function(elt, event, data) {
    if (console) console.log(event, elt, data);
}

// Monitor all events on a specific element (browser console only)
monitorEvents(htmx.find('#my-element'));
```

For deep debugging, load the unminified `htmx.js` (~2500 lines) and set breakpoints in `issueAjaxRequest()` and `handleAjaxResponse()`.
