## Context

HTMX out-of-band (OOB) swaps allow a single response to update multiple DOM elements. The server includes multiple HTML fragments, each with `hx-swap-oob` attribute specifying where to swap. HTMX expects `hx-swap-oob` to be baked into the response markup.

Currently, three fragile patterns exist across the codebase:

1. **String replace on ID** — Render template, then inject `hx-swap-oob` into the ID attribute
2. **Hand-constructed HTML** — Build HTML strings directly in Python with OOB attributes embedded
3. **String replace on CSS class** — Replace a CSS class string to inject OOB attributes

All three use post-render manipulation, causing silent failures (no errors, just no swap) when templates change. This violates HTMX's design model and creates maintenance burden.

## Goals / Non-Goals

**Goals:**
- Eliminate all string-based OOB injection
- Make OOB logic declarative and template-owned
- Achieve 100% behavioral equivalence (no user-facing changes)
- Reduce maintenance burden by centralizing template logic
- Align with HTMX design philosophy

**Non-Goals:**
- Change HTMX behavior or response structure
- Modify database or data model
- Refactor how primary (non-OOB) swaps work
- Add new OOB swap capabilities

## Decisions

### Decision 1: Always Include `hx-swap-oob` in Templates

**Chosen:** Templates always include `hx-swap-oob` attribute. No conditional parameter.

**Rationale:**
- Simplest approach: template owns the OOB behavior, period
- HTMX ignores `hx-swap-oob` on initial page load (only processes it from responses)
- No `oob=True` parameter to pass or remember
- Routes just render templates normally, no special handling
- OOB logic centralized in template, not scattered across route + template

**How it works:**
- Initial page load: Template includes `hx-swap-oob`, HTMX ignores it (it's not a response swap)
- HTMX response: Template includes `hx-swap-oob`, HTMX processes it normally

**Alternative considered:** Conditional `oob` parameter
- Rejected: Added complexity without benefit. HTMX handles unconditional OOB correctly

---

### Decision 2: Reusable Templates for Hand-Constructed Fragments

**Chosen:** Extract hand-constructed fragments (toast, badge) into templates (`_toast.html`, `_badge.html`).

**Rationale:**
- Centralizes design (styling, structure) in templates, not Python strings
- Easier to maintain and test
- Reduces Python line count
- Eliminates HTML strings from Python code

**Alternative considered:** Keep inline strings, add helper function
- Rejected: Still mixes HTML into Python; still hard to style or change

---

## Patterns: Before and After

### Pattern 1: String Replace on ID Attribute

**Before (inbox.py):**
```python
pagination = templates.get_template("_pagination.html").render({
    "pagination_url": "/inbox",
    "page": page,
    "total_pages": total_pages,
})
pagination_oob = pagination.replace(
    '<div class="flex items-center justify-between mt-4">',
    '<div id="inbox-pagination" hx-swap-oob="outerHTML:#inbox-pagination" class="flex items-center justify-between mt-4">',
    1,
)
return pagination_oob
```

**After (inbox.py):**
```python
pagination = templates.get_template("_pagination.html").render({
    "pagination_url": "/inbox",
    "page": page,
    "total_pages": total_pages,
})
return pagination
```

**Template (_pagination.html):**
```html
<div id="inbox-pagination" 
     hx-swap-oob="outerHTML:#inbox-pagination"
     class="flex items-center justify-between mt-4">
  <!-- pagination buttons and controls -->
</div>
```

**Why better:**
- No string replace logic; template owns the structure
- CSS class changes don't break OOB swap
- Single place to change when design updates
- No special parameters or conditionals needed

---

### Pattern 2: Hand-Constructed HTML Strings

**Before (inbox.py):**
```python
badge_oob = f'<span id="inbox-badge" hx-swap-oob="innerHTML:#inbox-badge">{badge_html}</span>'
toast = f'<div id="toast-container" hx-swap-oob="innerHTML:#toast-container"><div class="alert alert-success"><span>Committed {committed_count} transaction{"s" if committed_count != 1 else ""}.</span></div></div>'

return badge_oob + toast + primary_html
```

**After (inbox.py):**
```python
badge = render_template("_badge.html", count=remaining_count)
toast = render_template("_toast.html", 
    message=f"Committed {committed_count} transaction{'s' if committed_count != 1 else ''}.",
    type="success"
)
return badge + toast + primary_html
```

**New template (_toast.html):**
```html
<div id="toast-container" hx-swap-oob="innerHTML:#toast-container">
  <div class="alert alert-{{ type }}">
    <span>{{ message }}</span>
  </div>
</div>
```

**New template (_badge.html):**
```html
<span id="inbox-badge" hx-swap-oob="innerHTML:#inbox-badge">
  {% if count > 0 %}
    <span class="badge badge-sm badge-primary">{{ count }}</span>
  {% endif %}
</span>
```

**Why better:**
- Design lives in templates, not Python f-strings
- Easy to change styling (edit template, not hunt Python strings)
- Reusable: same `_toast.html` for all toast messages
- Testable: render template with different inputs

---

### Pattern 3: String Replace on CSS Class

**Before (explore.py):**
```python
date_range_oob = templates.get_template("_explore_date_range.html").render({...})
date_range_oob = date_range_oob.replace(
    'id="explore-date-range"',
    'id="explore-date-range" hx-swap-oob="outerHTML:#explore-date-range"',
    1,
)
```

**After (explore.py):**
```python
date_range_oob = templates.get_template("_explore_date_range.html").render({...})
```

**Template (_explore_date_range.html):**
```html
<div id="explore-date-range" 
     hx-swap-oob="outerHTML:#explore-date-range">
  <!-- date range content -->
</div>
```

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|-----------|
| **Developers forget `oob=True` parameter** | Code review checklist; linting rule to catch missing parameter. Pattern becomes muscle memory quickly. |
| **Template parameter pollution** | Templates only accept `oob` parameter; keep uncluttered. Document in template comments if needed. |
| **Regression if OOB behavior changes unexpectedly** | Add integration tests for OOB responses (verify `hx-swap-oob` attributes are present in HTML output). |
| **Performance:** Jinja2 conditional rendering overhead | Negligible; Jinja2 optimizes conditionals. No measurable impact expected. |

## Migration Plan

**Approach:** Refactor routes in phases, route by route.

1. **Phase 1**: Fix Pattern 2 (hand-constructed fragments) first
   - Create `_toast.html` and `_badge.html`
   - Update `inbox.py` to render templates instead of f-strings
   - Test commit, retrain, and notification flows

2. **Phase 2**: Fix Pattern 1 (ID attribute replace)
   - Update `_pagination.html` to use `oob` parameter
   - Update `inbox.py` to pass `oob=True`
   - Update `_transaction_row.html` and `transactions.py`
   - Test pagination and transaction editing

3. **Phase 3**: Fix Pattern 3 (CSS class replace)
   - Update `_explore_date_range.html` to use `oob` parameter
   - Update `explore.py` to pass `oob=True`
   - Test date range filtering

**Rollback:** Each phase is independent. If a phase breaks, revert that route and templates.

## Open Questions

None. Design is clear and aligned with HTMX philosophy.
