---
name: daisyui
description: Reference for building UIs with daisyUI components. Use whenever writing or reviewing HTML that uses daisyUI classes like btn, card, modal, table, alert, badge, input, select, navbar, menu, drawer, toast, or any other daisyUI component. Also triggers for questions about daisyUI semantic colors (primary, base-100, etc.), themes (data-theme), customizing components, or configuring the daisyUI plugin. Make sure to use this skill whenever daisyUI components, class names, or theming are involved.
---

# daisyUI Reference Skill

daisyUI 5 is a CSS plugin for Tailwind CSS 4. It provides semantic class names for 65 UI components.
The core idea: use `btn`, `card`, `modal`, etc. instead of dozens of raw Tailwind utility classes.

## Reference Files

| File | When to load |
|---|---|
| `references/components.md` | Class names, HTML syntax, and rules for any specific component |
| `references/colors-and-themes.md` | Color names, CSS variables, theme list, custom themes |
| `references/config.md` | Plugin config options (themes, prefix, include/exclude, etc.) |

## Installation

**Node (recommended):**

```css
/* app.css */
@import "tailwindcss";
@plugin "daisyui";
```

```sh
npm i -D daisyui@latest
```

**CDN (no build step):**

```html
<link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
<script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
```

## Core Usage Pattern

Build up styles by layering class types on elements:

```text
component  →  part  →  style/modifier  →  color  →  size
```

```html
<!-- component only -->
<button class="btn">Button</button>

<!-- component + color -->
<button class="btn btn-primary">Primary</button>

<!-- component + style + color + size -->
<button class="btn btn-outline btn-secondary btn-sm">Small outline</button>

<!-- component + part -->
<div class="card">
  <div class="card-body">
    <h2 class="card-title">Title</h2>
    <p>Content</p>
    <div class="card-actions">
      <button class="btn btn-primary">Action</button>
    </div>
  </div>
</div>
```

Class type definitions:

- `component` — the required base class (e.g. `btn`, `card`, `input`)
- `part` — a child element of a component (e.g. `card-body`, `modal-box`)
- `style` — visual variant (e.g. `btn-outline`, `btn-dash`, `btn-soft`, `btn-ghost`)
- `color` — semantic color (e.g. `btn-primary`, `badge-error`)
- `size` — size variant (e.g. `btn-sm`, `btn-lg`, `input-xs`)
- `modifier` — behavioral change (e.g. `modal-open`, `table-zebra`)
- `placement` — position (e.g. `toast-top`, `toast-end`)

## Semantic Color System

**Use daisyUI semantic colors, not hardcoded Tailwind colors.** This enables automatic theme switching.

```html
<!-- BAD: hardcoded, breaks theme switching -->
<div class="bg-zinc-100 text-zinc-800">...</div>

<!-- GOOD: semantic, works with all themes -->
<div class="bg-base-100 text-base-content">...</div>
```

### Color Names

| Color | CSS Variable | Purpose |
|---|---|---|
| `primary` | `--color-primary` | Main brand color |
| `primary-content` | `--color-primary-content` | Text on primary |
| `secondary` | `--color-secondary` | Secondary brand color |
| `secondary-content` | `--color-secondary-content` | Text on secondary |
| `accent` | `--color-accent` | Accent color |
| `accent-content` | `--color-accent-content` | Text on accent |
| `neutral` | `--color-neutral` | Neutral dark color |
| `neutral-content` | `--color-neutral-content` | Text on neutral |
| `base-100` | `--color-base-100` | Page background |
| `base-200` | `--color-base-200` | Slightly darker surface |
| `base-300` | `--color-base-300` | Even darker surface |
| `base-content` | `--color-base-content` | Default text color |
| `info` | `--color-info` | Informational |
| `info-content` | `--color-info-content` | Text on info |
| `success` | `--color-success` | Success/safe |
| `success-content` | `--color-success-content` | Text on success |
| `warning` | `--color-warning` | Warning/caution |
| `warning-content` | `--color-warning-content` | Text on warning |
| `error` | `--color-error` | Error/danger |
| `error-content` | `--color-error-content` | Text on error |

### Using Colors in Utility Classes

```html
<div class="bg-primary text-primary-content">Primary box</div>
<div class="bg-base-200 border border-base-300">Card surface</div>
<p class="text-base-content/50">Muted text (50% opacity)</p>
<div class="bg-error/20">Soft error background</div>
```

Available prefixes: `bg-`, `text-`, `border-`, `ring-`, `fill-`, `stroke-`, `shadow-`, `outline-`, `from-`, `via-`, `to-`

## Themes

Set the active theme with `data-theme` on any element (usually `<html>`):

```html
<html data-theme="cupcake">...</html>
```

Themes nest — you can force a section to a specific theme:

```html
<html data-theme="dark">
  <div data-theme="light">Always light</div>
</html>
```

**35 built-in themes:**
`light` `dark` `cupcake` `bumblebee` `emerald` `corporate` `synthwave` `retro` `cyberpunk` `valentine` `halloween` `garden` `forest` `aqua` `lofi` `pastel` `fantasy` `wireframe` `black` `luxury` `dracula` `cmyk` `autumn` `business` `acid` `lemonade` `night` `coffee` `winter` `dim` `nord` `sunset` `caramellatte` `abyss` `silk`

Enable themes in config (see `references/config.md` and `references/colors-and-themes.md`):

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark, cupcake;
}
```

## Customization Approaches

**1. daisyUI modifier classes (always try first):**

```html
<button class="btn btn-primary btn-outline btn-sm">...</button>
```

**2. Tailwind utility classes (for layout/spacing not covered by daisyUI):**

```html
<button class="btn w-64 rounded-full">...</button>
```

**3. Force override with `!` suffix (last resort — CSS specificity issues):**

```html
<button class="btn bg-red-500!">...</button>
```

**4. Redefine component in CSS with `@utility` (for global changes):**

```css
@utility btn {
  @apply rounded-full;
}
```

## Key Rules

- Don't hardcode Tailwind color values (`bg-zinc-500`) — use daisyUI semantic colors
- Don't add `bg-base-100 text-base-content` to `<body>` unless necessary
- Layout (flexbox, grid, spacing, typography) is still handled by Tailwind CSS utilities
- If a component doesn't exist in daisyUI, build it with plain Tailwind CSS utilities
- Responsive layouts use Tailwind responsive prefixes (`sm:`, `md:`, `lg:`, etc.)
- All 65 components with class names and HTML syntax are in `references/components.md`
