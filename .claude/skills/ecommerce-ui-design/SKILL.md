---
name: ecommerce-ui-design
description: The single source of truth for how the Karvii Spices React frontend looks. Use this skill WHENEVER creating or editing ANY React component, page, CSS, or UI in the frontend/ folder. Apply these design tokens so every page feels like a premium, fresh, natural Indian spice brand — think earthy greens, warm whites, terracotta accents — NOT bland beige, NOT dark fashion. Trigger this even when the user says "make it look better", "style this", "fix the design", "add a new page/component", or anything UI-related in the React frontend.
---

# Karvii Spices — React UI Design System

## Brand personality in one line
**Fresh, natural, earthy, trustworthy** — like a premium Indian spice shop that sources directly from farms. Think real herbs, terracotta pots, morning sunlight. NOT a fashion store. NOT a dark luxury brand. NOT a bland beige food delivery app.

## Stack
React + Vite + plain CSS (no Tailwind, no Bootstrap). All styles in `frontend/src/index.css` (global tokens + components) and scoped component CSS files. Import Google Fonts in `index.html`.

---

## 1. Design Tokens — paste into `frontend/src/index.css`

```css
/* =============================================
   KARVII SPICES — Design Tokens
   ============================================= */

@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

:root {
  /* === Brand Colors === */
  --color-primary:      #2D6A4F;   /* deep forest green — navbar, headings, CTAs */
  --color-primary-dark: #1B4332;   /* hover on green buttons */
  --color-primary-light:#40916C;   /* secondary green — tags, badges */
  --color-accent:       #D4580A;   /* terracotta/spice orange — "Add to Cart", highlights */
  --color-accent-dark:  #B84A06;   /* hover on orange */
  --color-accent-soft:  #FDEBD0;   /* very light orange — tag backgrounds */
  --color-gold:         #B7860B;   /* turmeric gold — star ratings, premium label */

  /* === Neutrals === */
  --color-bg:           #FAFAF7;   /* off-white — page background (NOT pure white, NOT beige) */
  --color-surface:      #FFFFFF;   /* cards, panels */
  --color-surface-warm: #F4F1EB;   /* warm light — hero, section backgrounds */
  --color-text:         #1C1C1A;   /* main text (almost black, warm) */
  --color-text-soft:    #6B6B5E;   /* secondary text, captions */
  --color-border:       #E2DDD5;   /* card borders, dividers */
  --color-border-green: #B7D5C4;   /* green-tinted borders for tags/badges */

  /* === Status === */
  --color-success:      #2D6A4F;   /* same as primary — in-stock (consistent) */
  --color-danger:       #C0392B;   /* out of stock, errors */
  --color-star:         #B7860B;   /* rating stars (turmeric gold) */

  /* === Typography === */
  --font-head: 'Playfair Display', Georgia, serif;   /* headings — elegant, premium */
  --font-body: 'Inter', system-ui, sans-serif;        /* body — clean, readable */
  --fs-xs:   12px;
  --fs-sm:   14px;
  --fs-base: 16px;
  --fs-lg:   20px;
  --fs-xl:   28px;
  --fs-hero: 48px;

  /* === Spacing === */
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
  --space-5: 40px;
  --space-6: 64px;

  /* === Shape & Shadow === */
  --radius:    8px;
  --radius-lg: 16px;
  --radius-pill: 100px;
  --shadow-sm: 0 1px 4px rgba(44, 62, 40, 0.08);
  --shadow-md: 0 4px 16px rgba(44, 62, 40, 0.12);
  --shadow-lg: 0 8px 32px rgba(44, 62, 40, 0.15);
}

/* === Reset + Base === */
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: var(--font-body);
  font-size: var(--fs-base);
  color: var(--color-text);
  background: var(--color-bg);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4 {
  font-family: var(--font-head);
  color: var(--color-text);
  line-height: 1.2;
}
a { color: var(--color-primary); text-decoration: none; }
a:hover { color: var(--color-primary-dark); }
img { max-width: 100%; display: block; }
.container { max-width: 1200px; margin: 0 auto; padding: 0 var(--space-4); }
```

---

## 2. Navbar

- Background: `--color-primary` (deep green), white text/links.
- Left: logo (leaf icon or brand mark) + "Karvii Spices" in Inter 600 white.
- Center/Right: Shop, Wishlist ♡, Orders, Cart (with count badge), Account avatar.
- Cart badge: `--color-accent` (terracotta), white text.
- Height: ~64px. Sticky. `--shadow-sm`.
- Mobile: hamburger menu.

```css
.navbar {
  background: var(--color-primary);
  padding: 0 var(--space-4);
  height: 64px;
  display: flex; align-items: center;
  position: sticky; top: 0; z-index: 100;
  box-shadow: var(--shadow-sm);
}
.navbar-brand {
  font-family: var(--font-body);
  font-weight: 700; font-size: var(--fs-lg);
  color: #fff; display: flex; align-items: center; gap: var(--space-2);
}
.navbar-links { display: flex; align-items: center; gap: var(--space-4); margin-left: auto; }
.navbar-links a { color: rgba(255,255,255,0.88); font-size: var(--fs-sm); font-weight: 500; }
.navbar-links a:hover { color: #fff; }
.cart-badge {
  background: var(--color-accent); color: #fff;
  font-size: 10px; font-weight: 700;
  border-radius: 50%; padding: 2px 6px; margin-left: 2px;
}
.avatar-circle {
  width: 34px; height: 34px; border-radius: 50%;
  background: var(--color-primary-light); color: #fff;
  font-weight: 700; font-size: var(--fs-sm);
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
}
```

---

## 3. Buttons

| Class | Use | Look |
|-------|-----|------|
| `.btn` | base (always add) | — |
| `.btn-primary` | main CTAs (Shop Now, Login, Save) | green bg, white text |
| `.btn-cart` | "Add to Cart" | terracotta `--color-accent`, white |
| `.btn-buy` | "Buy Now" | dark green, white |
| `.btn-outline` | secondary (Cancel, Back) | white bg, green border |
| `.btn-outline-accent` | secondary orange option | white bg, orange border |

```css
.btn {
  display: inline-flex; align-items: center; justify-content: center;
  gap: var(--space-1); border: none; cursor: pointer;
  padding: 11px var(--space-4); border-radius: var(--radius);
  font-family: var(--font-body); font-size: var(--fs-sm);
  font-weight: 600; transition: all 0.18s ease;
  white-space: nowrap;
}
.btn-primary { background: var(--color-primary); color: #fff; }
.btn-primary:hover { background: var(--color-primary-dark); }
.btn-cart { background: var(--color-accent); color: #fff; }
.btn-cart:hover { background: var(--color-accent-dark); }
.btn-buy { background: var(--color-primary-dark); color: #fff; }
.btn-outline { background: #fff; color: var(--color-primary); border: 1.5px solid var(--color-primary); }
.btn-outline:hover { background: var(--color-primary); color: #fff; }
.btn-outline-accent { background: #fff; color: var(--color-accent); border: 1.5px solid var(--color-accent); }
.btn-sm { padding: 7px var(--space-3); font-size: var(--fs-xs); }
.btn-lg { padding: 14px var(--space-5); font-size: var(--fs-base); }
```

---

## 4. Product Card (the heart of the catalog)

- White card, warm border, hover: lift + green border glow.
- Image: white/warm bg, `object-fit: contain` (masala packets must never stretch).
- Category tag: small green pill. Price: bold terracotta. Rating: gold stars.
- "Add to Cart" button full width at bottom.
- Weight selector (if variants exist): small pill buttons below price.

```css
.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: var(--space-4);
}
.product-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  display: flex; flex-direction: column;
}
.product-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-md);
  border-color: var(--color-border-green);
}
.product-card-img {
  width: 100%; height: 180px;
  object-fit: contain; background: var(--color-surface-warm);
  padding: var(--space-3);
}
.product-card-body { padding: var(--space-3); flex: 1; display: flex; flex-direction: column; }
.product-category-tag {
  display: inline-block;
  background: var(--color-accent-soft); color: var(--color-accent);
  font-size: var(--fs-xs); font-weight: 600;
  padding: 2px 10px; border-radius: var(--radius-pill);
  text-transform: uppercase; letter-spacing: 0.4px;
  margin-bottom: var(--space-2);
}
.product-title { font-size: var(--fs-sm); font-weight: 500; color: var(--color-text); flex: 1; }
.product-price {
  font-size: var(--fs-lg); font-weight: 700;
  color: var(--color-primary-dark); margin: var(--space-2) 0;
}
.rating-row { display: flex; align-items: center; gap: var(--space-1); margin-bottom: var(--space-2); }
.star { color: var(--color-star); font-size: var(--fs-sm); }
.rating-count { font-size: var(--fs-xs); color: var(--color-text-soft); }
.in-stock { color: var(--color-success); font-size: var(--fs-xs); font-weight: 500; }
.out-stock { color: var(--color-danger); font-size: var(--fs-xs); font-weight: 500; }

/* Weight variant pills */
.weight-pills { display: flex; gap: var(--space-1); flex-wrap: wrap; margin-bottom: var(--space-2); }
.weight-pill {
  padding: 3px 10px; border-radius: var(--radius-pill);
  border: 1px solid var(--color-border);
  font-size: var(--fs-xs); cursor: pointer; background: #fff;
  transition: all 0.15s;
}
.weight-pill.active, .weight-pill:hover {
  background: var(--color-primary); color: #fff; border-color: var(--color-primary);
}
```

---

## 5. Category Cards (homepage grid)

- White card, centered icon (emoji or illustration, ~48px), name, short description.
- Hover: green border + light green background tint.

```css
.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
  gap: var(--space-3);
}
.category-card {
  background: var(--color-surface);
  border: 1.5px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-4) var(--space-3);
  text-align: center; cursor: pointer;
  transition: all 0.18s;
}
.category-card:hover {
  border-color: var(--color-primary-light);
  background: #F0F7F3;
}
.category-icon { font-size: 40px; margin-bottom: var(--space-2); }
.category-name { font-weight: 600; font-size: var(--fs-sm); color: var(--color-text); }
.category-desc { font-size: var(--fs-xs); color: var(--color-text-soft); margin-top: 4px; }
```

---

## 6. Offer/Promo Banner

Horizontal scrolling banner at top of page: green bg, white text, marquee-style.

```css
.offer-banner {
  background: var(--color-primary);
  color: #fff; text-align: center;
  padding: var(--space-2) var(--space-3);
  font-size: var(--fs-xs); font-weight: 500;
  letter-spacing: 0.3px;
}
.offer-banner span { margin: 0 var(--space-4); opacity: 0.9; }
```

---

## 7. Hero Section

- Background: `--color-surface-warm` OR a high-quality masala/farm image.
- Left: headline (Playfair, `--fs-hero`), subtext, 2 CTA buttons (primary + outline).
- Right: hero product image (masala pack, spice bowl, farm).
- NO pure brown background (that's what's there now — too dull). Go light + fresh.

```css
.hero {
  background: var(--color-surface-warm);
  min-height: 520px;
  display: flex; align-items: center;
}
.hero-content { max-width: 560px; }
.hero-eyebrow {
  font-size: var(--fs-xs); font-weight: 700;
  color: var(--color-primary-light); letter-spacing: 1.5px;
  text-transform: uppercase; margin-bottom: var(--space-2);
}
.hero-title {
  font-size: var(--fs-hero); font-family: var(--font-head);
  color: var(--color-primary-dark); line-height: 1.1;
  margin-bottom: var(--space-3);
}
.hero-subtitle { font-size: var(--fs-base); color: var(--color-text-soft); margin-bottom: var(--space-4); }
.hero-actions { display: flex; gap: var(--space-3); flex-wrap: wrap; }
```

---

## 8. Forms (login, signup, checkout, address)

```css
.form-card {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-lg);
  padding: var(--space-5);
  max-width: 440px; margin: var(--space-5) auto;
  box-shadow: var(--shadow-sm);
}
.form-group { margin-bottom: var(--space-3); }
.form-label { display: block; font-size: var(--fs-sm); font-weight: 600; margin-bottom: 6px; }
.form-input {
  width: 100%; padding: 11px var(--space-3);
  border: 1.5px solid var(--color-border); border-radius: var(--radius);
  font-family: var(--font-body); font-size: var(--fs-base);
  transition: border-color 0.15s;
}
.form-input:focus { outline: none; border-color: var(--color-primary); box-shadow: 0 0 0 3px rgba(45,106,79,0.12); }
.form-error { color: var(--color-danger); font-size: var(--fs-xs); margin-top: 4px; }
```

---

## 9. Footer

- Background: `--color-primary-dark` (dark green), cream/white text, gold links.
- 3-4 columns: About Karvii, Shop (categories), Account links, Social + Contact.
- Bottom bar: copyright.

```css
.footer {
  background: var(--color-primary-dark); color: #e8f5e9;
  padding: var(--space-6) 0 var(--space-4);
}
.footer h4 { color: #fff; font-family: var(--font-body); font-weight: 700; margin-bottom: var(--space-3); }
.footer a { color: rgba(255,255,255,0.7); font-size: var(--fs-sm); line-height: 2; }
.footer a:hover { color: #fff; }
.footer-bottom {
  border-top: 1px solid rgba(255,255,255,0.1);
  margin-top: var(--space-4); padding-top: var(--space-3);
  text-align: center; color: rgba(255,255,255,0.5);
  font-size: var(--fs-xs);
}
```

---

## 10. Flash / Toast Messages

```css
.toast { padding: var(--space-3) var(--space-4); border-radius: var(--radius); font-size: var(--fs-sm); font-weight: 500; }
.toast-success { background: #D1FAE5; color: var(--color-success); border: 1px solid var(--color-border-green); }
.toast-error   { background: #FEE2E2; color: var(--color-danger); border: 1px solid #FECACA; }
.toast-info    { background: var(--color-accent-soft); color: var(--color-accent); border: 1px solid #FDDBB4; }
```

---

## 11. Section layout pattern (every page)

```
[ Navbar ]
[ Offer Banner (optional, homepage + catalog) ]
[ Page content inside .container ]
[ Footer ]
```

---

## 12. Do / Don't

**DO**
- Use `--color-primary` (green) for main structure, CTAs, headings
- Use `--color-accent` (terracotta) for Add to Cart, highlights, tags
- Use `--color-surface-warm` for section backgrounds (not heavy brown)
- Keep product images on WHITE or `--color-surface-warm` bg (object-fit: contain)
- Use weight pills for masala size variants
- Keep the hero LIGHT and FRESH (not dark brown)

**DON'T**
- Don't use heavy dark brown (#5C3D11 type) as page/section background
- Don't use the old plum/fashion colors (#3D1A2B etc.) — this is a FOOD brand
- Don't hardcode hex colors in JSX inline styles — use CSS variables
- Don't use `object-fit: cover` on masala product images (packets will crop)
- Don't make everything terracotta — green is primary, terracotta is accent only

---

## 13. When applying this skill

1. This is a **React frontend** — all styles go in `frontend/src/index.css` (global tokens + shared classes) or component `.css` files.
2. Use CSS classes in JSX (`className="btn btn-cart"`), not inline styles.
3. For a NEW component: read this skill → use the tokens → reuse existing classes.
4. For RESTYLING: replace old brown/beige with the new tokens above.
5. After styling, open the browser (npm run dev) and confirm it looks fresh, natural, and food-brand-appropriate.