# daisyUI Plugin Config Reference

Configuration lives in your CSS file inside `@plugin "daisyui" { }`.

## Default Config

```css
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
  root: ":root";
  include: ;
  exclude: ;
  prefix: ;
  logs: true;
}
```

## `themes`

**Default:** `light --default, dark --prefersdark`
**Type:** comma-separated list | `false` | `all`

Controls which built-in themes are compiled into your CSS. Unneeded themes add CSS weight.

Flags per theme name:

- `--default` — active when no `data-theme` attribute is present
- `--prefersdark` — active when `prefers-color-scheme: dark`

```css
/* enable specific themes */
@plugin "daisyui" {
  themes: nord --default, abyss --prefersdark, cupcake, dracula;
}

/* enable all 35 built-in themes */
@plugin "daisyui" {
  themes: all;
}

/* disable all built-in themes (use only custom themes) */
@plugin "daisyui" {
  themes: false;
}

/* single theme only */
@plugin "daisyui" {
  themes: dracula --default;
}
```

## `root`

**Default:** `":root"`
**Type:** CSS selector string

The selector that receives daisyUI's global CSS variables. Change this to scope daisyUI
to a specific part of the page (e.g. inside a web component or shadow DOM).

```css
@plugin "daisyui" {
  root: "#my-app";
}
```

## `include`

**Default:** (empty — include everything)
**Type:** comma-separated list of component file names

Allowlist — only compile the listed components. All others are excluded. Useful for minimal
builds where you only need a few components.

```css
@plugin "daisyui" {
  include: button, input, select, card, modal;
}
```

## `exclude`

**Default:** (empty — exclude nothing)
**Type:** comma-separated list of component file names

Denylist — compile everything except the listed items. Useful to opt out of a few things
you don't want.

```css
/* remove the scroll-lock gutter added when a modal is open */
@plugin "daisyui" {
  exclude: rootscrollgutter;
}

/* exclude several components */
@plugin "daisyui" {
  exclude: checkbox, footer, typography, glass, rootcolor, rootscrollgutter;
}
```

Notable excludable items beyond component names:

- `rootscrollgutter` — prevents layout shift when modals/drawers open (scrollbar gutter compensation)
- `rootcolor` — sets the base background/text colors on `:root`
- `typography` — the prose/typography styles
- `glass` — the `.glass` utility class

## `prefix`

**Default:** `""` (no prefix)
**Type:** string

Prefix all daisyUI class names to avoid conflicts with other CSS libraries.

```css
@plugin "daisyui" {
  prefix: "d-";
}
```

With prefix `d-`: `btn` → `d-btn`, `card` → `d-card`, etc.

### Using Both Tailwind and daisyUI Prefixes Together

```css
@import "tailwindcss" prefix(tw);
@plugin "daisyui" {
  prefix: "d-";
}
```

Result: `btn` → `tw:d-btn`, Tailwind's `p-4` → `tw:p-4`.
Exception: `theme-controller` only gets the daisyUI prefix → `d-theme-controller`.

## `logs`

**Default:** `true`
**Type:** boolean

daisyUI prints build info to the console during compilation. Set to `false` to silence it.

```css
@plugin "daisyui" {
  logs: false;
}
```

## Common Recipes

### Production-ready minimal build

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
  logs: false;
}
```

### Single custom theme, no built-ins

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: false;
}
@plugin "daisyui/theme" {
  name: "mybrand";
  default: true;
  --color-primary: oklch(55% 0.3 240);
  /* ...other variables */
}
```

### Conflict-free integration alongside another library

```css
@import "tailwindcss";
@plugin "daisyui" {
  prefix: "ui-";
  themes: light --default;
}
```

All daisyUI classes now require the `ui-` prefix: `ui-btn`, `ui-card`, etc.
