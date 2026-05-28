# Spec Document — Product Catalog

## 1. Overview

Implement the **Product Catalog** — the part of the website where customers actually *see* the products and look at them.

This is the "shop floor" of the store. Real e-commerce sites (Amazon, Flipkart, Myntra) all have this: a page that lists all products in a grid, and a separate page for each single product with its full details and an "Add to Cart" button.

This feature has **two pages**:
1. **Product Listing page** — a grid of all products (image, name, price).
2. **Product Detail page** — one product shown big, with full description, price, stock status, and an "Add to Cart" button.

**Why this matters:** This is the first thing a shopper does — browse. Without a catalog there is nothing to buy. The cart and checkout features (next) depend on the user being able to click products here.

---

## 2. Depends on

- **Database Setup** (the `products` table already exists, with 6 demo products seeded — feature 01).
- **User Authentication** (feature 02) — not strictly required to *view* products, but the nav bar should show login/logout state on these pages too.

Built on the existing **Flask + HTML templates** stack (same as features 01 and 02 — no React).

---

## 3. User Stories

- **As a shopper**, I want to see all available products on one page, so that I can browse what the store offers.
- **As a shopper**, I want to see each product's image, name, and price at a glance, so that I can quickly decide what interests me.
- **As a shopper**, I want to click a product and open its own page, so that I can read the full description and details before buying.
- **As a shopper**, I want to clearly see if a product is in stock or out of stock, so that I don't try to buy something unavailable.
- **As a shopper**, I want a clear "Add to Cart" button on the product page, so that I can move toward buying it.
- **As any visitor**, I want to browse products even without logging in, so that I can explore before creating an account.

---

## 4. Database Schema

> No changes needed. Reads from the existing `products` table created in feature 01.

### products (existing — for reference)

| Column | Type | Note |
| --- | --- | --- |
| id | INTEGER | product id |
| name | TEXT | product name |
| description | TEXT | full description |
| price | REAL | price |
| stock | INTEGER | how many are available (0 = out of stock) |
| category | TEXT | one of the fixed categories |
| image_url | TEXT | link/path to product image |

---

## 5. Routes / Functions to Implement

> Flask routes + Jinja templates, same pattern as the existing pages.

### A. Product listing page  (`GET /products` — and ideally the home page `/` too)
- Reads all products from the database.
- Shows them in a responsive grid: image, name, price.
- Each card links to that product's detail page.
- If a product is out of stock, show a small "Out of stock" label on its card.

### B. Product detail page  (`GET /products/<id>`)
- Reads one product by its id.
- Shows: large image, name, full description, price, and stock status.
- Shows an **"Add to Cart"** button (the button can exist now; the actual cart logic comes in the Cart feature — for now it can be a placeholder that doesn't error).
- If the product id does not exist → show a friendly "Product not found" page (not a crash).

### C. `get_all_products()` helper
- Returns the list of products from the database.

### D. `get_product_by_id(id)` helper
- Returns a single product, or nothing if it doesn't exist.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Listing shows all products
- **Given** the database has the 6 demo products
- **When** a visitor opens the product listing page
- **Then** all 6 products appear in a grid, each showing image, name, and price.

### AC-2: Browse without login
- **Given** a visitor who is NOT logged in
- **When** they open the listing or a product detail page
- **Then** they can view products normally (no forced login).

### AC-3: Card links to detail page
- **Given** the listing page
- **When** the visitor clicks a product card
- **Then** that product's detail page opens with the correct product.

### AC-4: Detail page shows full info
- **Given** a valid product
- **When** its detail page opens
- **Then** the name, full description, price, image, and stock status are all shown correctly.

### AC-5: Out-of-stock is clearly shown
- **Given** a product with stock = 0
- **When** it appears on the listing or detail page
- **Then** it is clearly marked "Out of stock" and the Add to Cart button is disabled (or hidden).

### AC-6: Invalid product id handled
- **Given** a product id that does not exist
- **When** someone opens that detail URL
- **Then** a friendly "Product not found" page is shown, not an error/crash.

### AC-7: Add to Cart button present
- **Given** an in-stock product's detail page
- **When** it loads
- **Then** an "Add to Cart" button is visible (cart logic itself comes in the next feature).

### AC-8: Nav bar stays consistent
- **Given** the user is logged in or logged out
- **When** they view catalog pages
- **Then** the nav bar correctly shows their login/logout state (same as other pages).

---

## 7. Files to Change

- Main app/routes file → add the listing and detail routes (and point `/` to the listing if desired).
- The shared base template → catalog pages should extend it so the nav bar is consistent.

## 8. Files to Create

- A products module/blueprint with the routes and the two helper functions.
- `templates/products/list.html` → the grid listing page.
- `templates/products/detail.html` → the single product page.
- A "product not found" message/template (can be a simple page).

---

## 9. Dependencies

- No new external services or libraries.
- Reuses the existing database helpers and base template.

---

## 10. Rules for Implementation

- Reuse the existing **base template** so the nav bar and login/logout state stay consistent everywhere.
- Use **parameterized queries only** when reading a product by id (never paste the id directly into SQL).
- The grid must be **responsive** — look fine on both mobile and desktop (simple CSS grid/flex is enough; no React).
- Out-of-stock products must be visually distinct and not addable to cart.
- Prices shown formatted nicely (e.g. with a currency symbol, 2 decimals).
- If a product has no image_url, show a simple placeholder instead of a broken image.
- The "Add to Cart" button should not crash even though cart logic isn't built yet (placeholder is fine).

---

## 11. Error Handling Expectations

- Non-existent product id → friendly "Product not found" page, no crash.
- Missing product image → placeholder image, not a broken-image icon.
- Empty product table (edge case) → listing shows a friendly "No products yet" message instead of a blank/broken page.

---

## 12. Out of Scope (handled by other features)

- Search and category filtering → **Search & Filter feature** (next after this).
- Actual cart logic (adding/removing items) → **Shopping Cart feature**.
- Admin adding/editing products → **Admin Dashboard feature**.
- Product reviews and ratings → **Reviews feature**.
- This feature only **displays** products and links them; it does not change cart or product data.

---

## 13. Definition of Done

- [ ] A listing page shows all products in a responsive grid (image, name, price).
- [ ] Products can be browsed without logging in.
- [ ] Clicking a product opens its correct detail page.
- [ ] The detail page shows name, full description, price, image, and stock status.
- [ ] Out-of-stock products are clearly marked and not addable to cart.
- [ ] An invalid product id shows a friendly "Product not found" page (no crash).
- [ ] An "Add to Cart" button is present on in-stock product pages (placeholder is fine).
- [ ] The nav bar shows correct login/logout state on catalog pages.
- [ ] Missing images show a placeholder, not a broken image.
- [ ] All product reads use parameterized SQL.