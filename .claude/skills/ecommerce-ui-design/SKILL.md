---
name: ecommerce-ui-design
description: The single source of truth for how this Flask e-commerce site looks. Use this skill WHENEVER creating or editing ANY HTML template, CSS, or page in this project — product pages, forms, navbar, footer, admin pages, auth pages, cart, checkout, everything. Always apply these design tokens so every page looks consistent and feels like a premium boutique fashion brand (deep plum + champagne gold + warm cream), instead of looking like an unstyled prototype. Trigger this even when the user just says "make this page look better", "style this", "fix the design", or adds any new feature with a UI.
---

# E-Commerce UI Design System (Premium Boutique — Plum / Gold / Cream)

This project is a Flask + Jinja + **plain CSS** e-commerce site (no React, no Tailwind, no Bootstrap). The brand is an **elegant, premium fashion/boutique** brand (rose-gold "K" logo). Every page MUST follow the tokens and patterns below so the whole site feels like one polished, refined, high-end shopping website — NOT a bright mass-market marketplace.

## Aesthetic in one line
Warm cream backgrounds, deep plum structure, champagne-gold accents, elegant serif headings, generous whitespace, soft shadows. Think luxury boutique, not flea market.

## Golden rules

1. **Always use the CSS variables** defined below — never hardcode random colors or sizes.
2. **One global stylesheet**: put all shared styles in `static/css/style.css` and link it in `base.html`. Don't scatter `<style>` blocks across pages.
3. **Consistency beats cleverness** — a new page should reuse existing classes (`.btn`, `.product-card`, etc.), not invent new ones.
4. **Gold is an accent, not a flood** — use champagne gold for CTAs, borders, highlights. Don't paint whole sections gold.
5. **Mobile-friendly**: layouts must not break on a phone-width screen. Use the responsive grid pattern below.
6. When unsure, copy the look of an existing well-styled page rather than guessing.

---

## 1. Design tokens (paste into the top of `static/css/style.css`)

```css
:root {
  /* Brand palette */
  --color-plum:        #3D1A2B;   /* deep plum — navbar, footer, headings, structure */
  --color-plum-dark:   #2C1220;   /* darker plum — hover on plum buttons */
  --color-gold:        #E8C39E;   /* champagne gold — accents, CTAs, borders */
  --color-gold-dark:   #D4A877;   /* gold hover */
  --color-cream:       #F7EDE2;   /* warm cream — page background */
  --color-surface:     #FFFFFF;   /* cards, panels (slightly brighter than cream) */
  --color-text:        #2C2C2A;   /* main dark text */
  --color-text-soft:   #8a8378;   /* secondary text, captions */
  --color-border:      #e6dccb;   /* soft warm borders/dividers */

  /* Status colors (kept earthy to match palette) */
  --color-success:     #5a7d52;   /* in-stock / success (muted sage green) */
  --color-danger:      #b3443b;   /* errors / out-of-stock (muted brick red) */
  --color-star:        #c9952f;   /* rating stars (deep gold) */

  /* Typography */
  --font-head: 'Playfair Display', Georgia, 'Times New Roman', serif;  /* elegant headings */
  --font-body: 'Poppins', 'Segoe UI', Roboto, Arial, sans-serif;       /* clean body */
  --fs-xs: 12px;
  --fs-sm: 14px;
  --fs-base: 16px;
  --fs-lg: 20px;
  --fs-xl: 30px;
  --fs-hero: 44px;

  /* Spacing scale (use these, not random px) */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 40px;

  /* Shape & shadow (soft, premium) */
  --radius: 6px;
  --radius-lg: 12px;
  --shadow-sm: 0 2px 8px rgba(61,26,43,0.08);
  --shadow-md: 0 6px 20px rgba(61,26,43,0.12);
}

* { box-sizing: border-box; }
body {
  margin: 0;
  font-family: var(--font-body);
  font-size: var(--fs-base);
  color: var(--color-text);
  background: var(--color-cream);
  line-height: 1.55;
}
h1, h2, h3 { font-family: var(--font-head); color: var(--color-plum); font-weight: 700; letter-spacing: 0.3px; }
h1 { font-size: var(--fs-xl); margin: var(--space-4) 0 var(--space-3); }
a { color: var(--color-plum); text-decoration: none; }
a:hover { color: var(--color-gold-dark); }
.container { max-width: 1200px; margin: 0 auto; padding: 0 var(--space-3); }
```

### Fonts: add to `base.html` `<head>` (before style.css)
```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Poppins:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
```

---

## 2. Logo & Navbar (deep plum bar)

- Background `--color-plum`, cream/gold text, `--shadow-sm`. Sticky to top.
- Left: the rose-gold logo image + brand name (serif, gold). Center: search bar. Right: Account, Cart (gold count badge), My Orders, Admin (admin only).
- **Logo tip**: the logo has a black background — for the plum navbar, use a **transparent-background PNG** of the logo so it blends (or keep it inside a small dark circle). Store it at `static/img/logo.png`.

```css
.navbar {
  background: var(--color-plum);
  color: var(--color-cream);
  padding: var(--space-3) 0;
  box-shadow: var(--shadow-sm);
  position: sticky; top: 0; z-index: 100;
}
.navbar .container { display: flex; align-items: center; gap: var(--space-4); }
.navbar .brand { display: flex; align-items: center; gap: var(--space-2); }
.navbar .brand img { height: 38px; width: auto; }
.navbar .brand span { font-family: var(--font-head); font-size: var(--fs-lg); color: var(--color-gold); font-weight: 700; }
.navbar .search { flex: 1; }
.navbar .search input {
  width: 100%; padding: 11px var(--space-3);
  border: 1px solid var(--color-gold); border-radius: var(--radius);
  font-size: var(--fs-sm); background: #fff;
}
.navbar .nav-links { display: flex; align-items: center; gap: var(--space-4); }
.navbar .nav-links a { color: var(--color-cream); font-weight: 500; }
.navbar .nav-links a:hover { color: var(--color-gold); }
.cart-badge {
  background: var(--color-gold); color: var(--color-plum); font-size: var(--fs-xs);
  font-weight: 600; border-radius: 50%; padding: 2px 7px; margin-left: 4px;
}
```

---

## 3. Buttons

| Class | Use for | Look |
|-------|---------|------|
| `.btn` | base (always include) | — |
| `.btn-primary` | normal actions (Save, Login, Submit) | plum bg, cream text |
| `.btn-cart` | "Add to Cart" | gold bg, plum text |
| `.btn-buy` | "Buy Now" / Checkout | plum bg, gold border (strong) |
| `.btn-outline` | secondary (Cancel, Back) | transparent, plum border |

```css
.btn {
  display: inline-block; border: none; cursor: pointer;
  padding: 11px var(--space-4); border-radius: var(--radius);
  font-size: var(--fs-sm); font-weight: 600; letter-spacing: 0.3px;
  transition: all 0.18s ease;
}
.btn-primary { background: var(--color-plum); color: var(--color-cream); }
.btn-primary:hover { background: var(--color-plum-dark); color: #fff; }
.btn-cart { background: var(--color-gold); color: var(--color-plum); }
.btn-cart:hover { background: var(--color-gold-dark); }
.btn-buy { background: var(--color-plum); color: var(--color-gold); border: 1px solid var(--color-gold); }
.btn-buy:hover { background: var(--color-plum-dark); }
.btn-outline { background: transparent; color: var(--color-plum); border: 1px solid var(--color-plum); }
.btn-outline:hover { background: var(--color-plum); color: var(--color-cream); }
```

---

## 4. Product card & grid

- Cream/white card, soft warm border, gentle hover lift. Refined, airy.
- Image area fixed height, `object-fit: contain`. Title (serif-ish optional), price in plum bold, gold rating badge, stock status.

```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(230px, 1fr));
  gap: var(--space-4);
  padding: var(--space-4) 0;
}
.product-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-3);
  transition: transform 0.2s, box-shadow 0.2s;
}
.product-card:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }
.product-card img {
  width: 100%; height: 200px; object-fit: contain;
  background: #fff; margin-bottom: var(--space-2); border-radius: var(--radius);
}
.product-card .title {
  font-size: var(--fs-sm); color: var(--color-text); font-weight: 500;
  display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical;
  overflow: hidden; min-height: 40px;
}
.product-card .price {
  font-family: var(--font-head); font-size: var(--fs-lg);
  font-weight: 700; color: var(--color-plum); margin: var(--space-1) 0;
}
.rating-badge {
  display: inline-block; background: var(--color-star); color: #fff;
  font-size: var(--fs-xs); padding: 2px 7px; border-radius: var(--radius);
}
.in-stock { color: var(--color-success); font-size: var(--fs-xs); font-weight: 500; }
.out-stock { color: var(--color-danger); font-size: var(--fs-xs); font-weight: 500; }
```

---

## 5. Forms (login, signup, checkout, admin add/edit)

```css
.card {
  background: var(--color-surface); border: 1px solid var(--color-border);
  border-radius: var(--radius-lg); padding: var(--space-4); box-shadow: var(--shadow-sm);
}
.form-card { max-width: 440px; margin: var(--space-5) auto; }
.form-group { margin-bottom: var(--space-3); }
.form-group label { display: block; font-size: var(--fs-sm); font-weight: 600; margin-bottom: 6px; color: var(--color-plum); }
.form-group input, .form-group select, .form-group textarea {
  width: 100%; padding: 11px var(--space-3);
  border: 1px solid var(--color-border); border-radius: var(--radius);
  font-size: var(--fs-base); background: #fff;
}
.form-group input:focus { outline: 2px solid var(--color-gold); border-color: var(--color-gold); }
.error-msg { color: var(--color-danger); font-size: var(--fs-sm); margin-bottom: var(--space-2); }
.success-msg { color: var(--color-success); font-size: var(--fs-sm); margin-bottom: var(--space-2); }
```

---

## 6. Flash messages (Flask `flash()`)

```css
.flash { padding: var(--space-3); border-radius: var(--radius); margin: var(--space-3) 0; font-size: var(--fs-sm); }
.flash-success { background: #eef3ea; color: var(--color-success); border: 1px solid #cfe0c5; }
.flash-error   { background: #f7e9e7; color: var(--color-danger);  border: 1px solid #e8c5c0; }
.flash-info    { background: #f3ece2; color: var(--color-plum);    border: 1px solid var(--color-border); }
```

---

## 7. Page layout pattern (every content page)

```
[ navbar (from base.html) ]
[ flash messages ]
[ .container ]
   [ page heading (h1, serif, plum) ]
   [ main content: grid / card / form ]
[ footer ]
```

- Always wrap page content in `<div class="container">`.
- Headings use the serif `--font-head` in plum.
- Keep `base.html` owning the navbar + footer; child templates only fill the content block.
- Optional hero section on homepage: plum background, cream/gold text, serif headline at `--fs-hero`.

---

## 8. Footer

```css
.footer {
  background: var(--color-plum); color: var(--color-cream);
  padding: var(--space-5) 0; margin-top: var(--space-5); font-size: var(--fs-sm);
}
.footer a { color: var(--color-gold); }
.footer a:hover { color: #fff; }
```

---

## 9. Do / Don't checklist

**DO**
- Reuse `.btn`, `.product-card`, `.card`, `.form-group` everywhere.
- Use `--space-*` and `--fs-*` tokens for all spacing/sizes.
- Use serif `--font-head` for headings, sans `--font-body` for text.
- Use gold sparingly as an accent (CTAs, borders, highlights).
- Keep one `style.css` linked from `base.html`.

**DON'T**
- Don't hardcode hex colors in templates — use the variables.
- Don't flood pages with gold or use bright blue/orange (old marketplace look).
- Don't invent new button colors or new card styles per page.
- Don't put inline `style="..."` for things a class already covers.
- Don't break the responsive grid (always use `auto-fill, minmax`).

---

## 10. When applying this skill

1. If `static/css/style.css` doesn't exist yet, create it with the tokens + all component classes above, and add the Google Fonts links + stylesheet link in `base.html` `<head>` (see section 1).
2. Put the brand logo at `static/img/logo.png` (transparent background preferred) and show it in the navbar.
3. Refactor existing templates to use these classes (one page at a time).
4. For any NEW page/feature, build it directly with these classes from the start.
5. After styling a page, open it in the browser and confirm it looks consistent and premium before moving on.