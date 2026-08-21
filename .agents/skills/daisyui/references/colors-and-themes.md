# daisyUI Colors and Themes Reference

## Semantic Color Names

Use these instead of hardcoded Tailwind colors. Each theme provides values for all of them.

| Color name | CSS variable | Purpose |
|---|---|---|
| `primary` | `--color-primary` | Primary brand color |
| `primary-content` | `--color-primary-content` | Foreground on `primary` |
| `secondary` | `--color-secondary` | Secondary brand color |
| `secondary-content` | `--color-secondary-content` | Foreground on `secondary` |
| `accent` | `--color-accent` | Accent brand color |
| `accent-content` | `--color-accent-content` | Foreground on `accent` |
| `neutral` | `--color-neutral` | Neutral dark color (unsaturated UI) |
| `neutral-content` | `--color-neutral-content` | Foreground on `neutral` |
| `base-100` | `--color-base-100` | Page background |
| `base-200` | `--color-base-200` | Slightly elevated surface |
| `base-300` | `--color-base-300` | More elevated surface |
| `base-content` | `--color-base-content` | Default text color |
| `info` | `--color-info` | Informational messages |
| `info-content` | `--color-info-content` | Foreground on `info` |
| `success` | `--color-success` | Success / safe |
| `success-content` | `--color-success-content` | Foreground on `success` |
| `warning` | `--color-warning` | Warning / caution |
| `warning-content` | `--color-warning-content` | Foreground on `warning` |
| `error` | `--color-error` | Error / danger / destructive |
| `error-content` | `--color-error-content` | Foreground on `error` |

## Using Colors in Utility Classes

Use the color names with any Tailwind color utility prefix:

```html
<div class="bg-primary text-primary-content p-4">Primary box</div>
<div class="bg-base-200 border border-base-300 rounded-box">Card surface</div>
<button class="btn bg-error text-error-content">Danger</button>
```

Available prefixes:

```text
bg-{COLOR}        text-{COLOR}       border-{COLOR}
ring-{COLOR}      fill-{COLOR}       stroke-{COLOR}
shadow-{COLOR}    outline-{COLOR}    from-{COLOR}
via-{COLOR}       to-{COLOR}         divide-{COLOR}
accent-{COLOR}    caret-{COLOR}      decoration-{COLOR}
placeholder-{COLOR}
```

### Opacity Modifier

Append `/N` for opacity (any 0–100 value when using the plugin; multiples of 10 on CDN):

```html
<p class="text-base-content/50">Muted text</p>
<div class="bg-error/20">Soft error background</div>
<div class="bg-primary/30">Tinted primary</div>
```

This is the recommended way to create muted text — it works consistently across all themes.

## Themes

### Enabling Themes

Configure in your CSS file. By default only `light` and `dark` are enabled:

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: light --default, dark --prefersdark;
}
```

Flags:

- `--default` — use this theme when no `data-theme` is set
- `--prefersdark` — use this theme when `prefers-color-scheme: dark`

Enable specific themes:

```css
@plugin "daisyui" {
  themes: nord --default, abyss --prefersdark, cupcake, dracula;
}
```

Enable all 35 themes:

```css
@plugin "daisyui" {
  themes: all;
}
```

Disable all themes (use only custom themes):

```css
@plugin "daisyui" {
  themes: false;
}
```

### Applying a Theme

Set `data-theme` on any element. Themes nest — inner `data-theme` overrides outer:

```html
<html data-theme="dark">
  <body>
    <!-- whole page is dark -->
    <div data-theme="light">
      <!-- this section is always light -->
      <span data-theme="retro">
        <!-- this span is always retro -->
      </span>
    </div>
  </body>
</html>
```

### All 35 Built-in Theme Names

```text
light        dark         cupcake      bumblebee    emerald
corporate    synthwave    retro        cyberpunk    valentine
halloween    garden       forest       aqua         lofi
pastel       fantasy      wireframe    black        luxury
dracula      cmyk         autumn       business     acid
lemonade     night        coffee       winter       dim
nord         sunset       caramellatte abyss        silk
```

## Custom Themes

### Adding a New Theme

```css
@import "tailwindcss";
@plugin "daisyui";

@plugin "daisyui/theme" {
  name: "mytheme";
  default: true;           /* set as default theme */
  prefersdark: false;      /* set as default dark mode theme */
  color-scheme: light;     /* browser UI color scheme */

  /* base colors */
  --color-base-100: oklch(98% 0.02 240);
  --color-base-200: oklch(95% 0.03 240);
  --color-base-300: oklch(92% 0.04 240);
  --color-base-content: oklch(20% 0.05 240);

  /* brand colors */
  --color-primary: oklch(55% 0.3 240);
  --color-primary-content: oklch(98% 0.01 240);
  --color-secondary: oklch(70% 0.25 200);
  --color-secondary-content: oklch(98% 0.01 200);
  --color-accent: oklch(65% 0.25 160);
  --color-accent-content: oklch(98% 0.01 160);
  --color-neutral: oklch(50% 0.05 240);
  --color-neutral-content: oklch(98% 0.01 240);

  /* semantic colors */
  --color-info: oklch(70% 0.2 220);
  --color-info-content: oklch(98% 0.01 220);
  --color-success: oklch(65% 0.25 140);
  --color-success-content: oklch(98% 0.01 140);
  --color-warning: oklch(80% 0.25 80);
  --color-warning-content: oklch(20% 0.05 80);
  --color-error: oklch(65% 0.3 30);
  --color-error-content: oklch(98% 0.01 30);

  /* shape */
  --radius-selector: 1rem;   /* radius for selectors (checkbox, toggle, badge, etc.) */
  --radius-field: 0.25rem;   /* radius for fields (input, select, etc.) */
  --radius-box: 0.5rem;      /* radius for boxes (card, modal, etc.) */

  /* size base */
  --size-selector: 0.25rem;
  --size-field: 0.25rem;

  /* border */
  --border: 1px;

  /* effects */
  --depth: 1;   /* 0 = flat, 1 = default depth effect */
  --noise: 0;   /* 0 = no noise texture, 1 = noise texture */
}
```

### Customizing an Existing Theme

Use the same name as a built-in theme — unspecified values are inherited:

```css
@plugin "daisyui/theme" {
  name: "light";
  default: true;
  --color-primary: blue;
  --color-secondary: teal;
}
```

### Custom Theme via CDN

If not using the plugin, use a CSS selector:

```css
:root:has(input.theme-controller[value=mytheme]:checked),
[data-theme="mytheme"] {
  color-scheme: light;
  --color-base-100: oklch(98% 0.02 240);
  /* ...rest of variables */
}
```

### Theme-Specific Styles

Apply styles only when a certain theme is active:

```css
[data-theme="light"] .my-btn {
  background-color: #1EA1F1;
}
```

### Using Tailwind `dark:` Prefix with a daisyUI Theme

```css
@import "tailwindcss";
@plugin "daisyui" {
  themes: winter --default, night --prefersdark;
}
/* map Tailwind's dark: variant to a specific daisyUI theme */
@custom-variant dark (&:where([data-theme=night], [data-theme=night] *));
```

```html
<div class="p-10 dark:p-20">
  10 padding on winter, 20 padding on night
</div>
```
