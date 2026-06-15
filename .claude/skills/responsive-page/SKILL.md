---
name: responsive-page
description: Responsive design rules for every new React page or component in the Karvii Spices frontend. Read this before creating or editing any page/component to ensure it works at 375px (mobile), 768px (tablet), and 1280px (desktop). Apply these patterns so no new page introduces horizontal scroll, cramped layouts, or inaccessible touch targets on mobile.
---

# Karvii Spices — Responsive Page Guidelines

## 1. Breakpoints

Always use these four breakpoints, top-down (desktop-first):

| Breakpoint | Width | Target devices |
|---|---|---|
| Default (no media query) | > 1024px | Desktop |
| `@media (max-width: 1024px)` | 769–1024px | Large tablet / small laptop |
| `@media (max-width: 768px)` | 481–768px | Tablet / landscape phone |
| `@media (max-width: 480px)` | ≤ 480px | Portrait phone (375px iPhone SE is the critical target) |

Add these to `index.css` inside the existing breakpoint blocks — **never create isolated one-off media queries**.

---

## 2. Navbar — Hamburger Pattern (REQUIRED)

The Navbar already has a hamburger. **Never add new nav items without testing at 375px.**

On mobile (≤768px) the `.navbar-links` is `display: none` and `.hamburger` shows. The mobile nav drawer (`.mobile-nav`) lists all links vertically. When adding new nav links:

1. Add the `<Link>` to **both** `.navbar-links` (desktop) AND the `.mobile-nav` block (mobile) in `Navbar.jsx`.
2. Always pass `onClick={closeMobile}` on mobile nav links so the drawer closes on navigation.

CSS classes available (already in `index.css`):
- `.hamburger` — the toggle button
- `.mobile-nav` / `.mobile-nav.open` — the drawer
- `.mobile-nav-link` — individual link/button inside the drawer

---

## 3. Layout Grids — Sidebar Layouts

Any layout that has a sidebar (fixed or fractional column on one side) **must** collapse to a single column at ≤768px.

**Pattern:**
```css
.my-layout { display: grid; grid-template-columns: 240px 1fr; gap: 28px; }

@media (max-width: 768px) {
  .my-layout { grid-template-columns: 1fr; }
}
```

Existing responsive sidebar classes (already handled — do NOT redeclare):
- `.cart-layout` — collapses at 768px
- `.checkout-layout` — collapses at 768px
- `.detail-layout` — collapses at 768px
- `.account-layout` — collapses at 768px
- `.admin-layout` — collapses at 768px

---

## 4. Product / Content Grids

Use `auto-fill` with `minmax` so columns appear and disappear naturally:

```css
/* Good — auto-adjusts at any width */
.my-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 16px; }

/* Bad — fixed column count with no breakpoints */
.my-grid { display: grid; grid-template-columns: repeat(4, 1fr); }
```

If you must use a fixed column count, add explicit breakpoints for 768px and 480px.

---

## 5. Tables — Always Wrap

Every `<table>` must be wrapped in `<div className="table-wrap">` to allow horizontal scrolling on mobile:

```jsx
<div className="table-wrap">
  <table className="data-table">
    ...
  </table>
</div>
```

The `.table-wrap` class is in `index.css`:
```css
.table-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }
```

---

## 6. Buttons — Touch Target Minimums

| Class | Min height | Use for |
|---|---|---|
| `.btn` | 44px natural (11px padding × 2 + 16px line) | Primary actions |
| `.btn-sm` | 36px (enforced via `min-height`) | Secondary / inline actions |
| `.btn-lg` | ~50px | Hero CTAs |

**Never use smaller padding than `.btn-sm` provides.** If you need a tiny icon-only button, still give it `min-width: 36px; min-height: 36px`.

---

## 7. Container & Spacing

`.container` provides `0 24px` padding at desktop and auto-shrinks to `0 12px` at ≤480px (handled globally). Use `.container` on every page root — never set a fixed `width` on page wrappers.

```jsx
<div className="page">
  <div className="container">
    {/* page content */}
  </div>
</div>
```

---

## 8. Inline Styles — Forbidden on Layout Properties

Do not use inline `style` for layout sizing. Move these to CSS classes:

| Forbidden in JSX | Use instead |
|---|---|
| `style={{ width: 340 }}` | CSS class with `@media` override |
| `style={{ minWidth: 70 }}` | CSS class or remove |
| `style={{ gridTemplateColumns: '1fr 1fr' }}` | `.form-grid-2` class (already in `index.css`) |
| `style={{ fontSize: 13 }}` | CSS variable `var(--fs-xs)` or `var(--fs-sm)` |

Inline styles for **color, margin, padding** (non-layout) are acceptable.

---

## 9. Font Sizes

Use CSS custom properties — never hardcode `px` values for font sizes in JSX:

| Variable | Size | Use |
|---|---|---|
| `var(--fs-xs)` | 12px | Captions, badges, labels |
| `var(--fs-sm)` | 14px | Secondary body text, table cells |
| `var(--fs-base)` | 16px | Body text |
| `var(--fs-lg)` | 20px | Section headings |
| `var(--fs-xl)` | 28px | Page titles |
| `var(--fs-hero)` | 48px (→ 32px →26px) | Hero headline only |

`--fs-hero` scales down automatically via the breakpoint rules in `index.css`.

---

## 10. Pre-ship Checklist

Before marking any new page as done, verify each item in browser DevTools device emulation:

- [ ] **375px** — No horizontal scrollbar. All text readable without zooming.
- [ ] **375px** — Navbar shows hamburger; tapping it opens the mobile nav drawer.
- [ ] **375px** — Buttons are large enough to tap (≥ 36px height).
- [ ] **375px** — Any sidebars have stacked to single column.
- [ ] **375px** — Any tables scroll horizontally (wrapped in `.table-wrap`).
- [ ] **768px** — Desktop nav is visible; hamburger is hidden.
- [ ] **1280px** — Layout looks correct; no unnecessary stretching.
- [ ] **No inline `style` with `width`, `minWidth`, or `gridTemplateColumns` px values** in JSX.
