# Spec Document — Search & Filter

## 1. Overview

Implement **Search and Filtering** for the product catalog — the tools that help a shopper *find* the product they want instead of scrolling through everything.

Right now (after feature 03) the listing page just shows all products. This feature adds the controls every real e-commerce site has: a **search bar** to type what you're looking for, **category filters** to narrow down by type, **sorting** (price low-to-high, etc.), and **pagination** so the page doesn't become endless when there are many products.

**Why this matters:** A store with 6 products is fine to scroll. A real store with hundreds isn't. Search and filtering is what makes a catalog actually usable — it's the difference between "browsing" and "finding".

---

## 2. Depends on

- **Product Catalog** (feature 03) — this feature enhances the existing listing page.
- **Database Setup** (feature 01) — reads from the `products` table (which has `name`, `category`, `price`).

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As a shopper**, I want to type a word in a search bar and see matching products, so that I can quickly find what I want by name.
- **As a shopper**, I want to filter products by category (Electronics, Clothing, etc.), so that I only see the kind of thing I'm shopping for.
- **As a shopper**, I want to sort products by price (low-to-high or high-to-low), so that I can shop within my budget.
- **As a shopper**, I want the products split across pages instead of one giant list, so that the page loads cleanly.
- **As a shopper**, I want to combine search + category + sort together, so that I can narrow down precisely.
- **As a shopper**, I want a clear message when nothing matches my search, so that I'm not confused by a blank page.

---

## 4. Database Schema

> No changes needed. Reads from the existing `products` table using its `name`, `category`, and `price` columns.

---

## 5. Routes / Functions to Implement

> These enhance the existing `/products` listing route — they don't replace it.

### A. Enhanced listing route  (`GET /products`)
- Reads optional values from the URL query string:
    - `q` → the search keyword
    - `category` → which category to filter by
    - `sort` → how to sort (e.g. `price_asc`, `price_desc`, `newest`)
    - `page` → which page of results
- Applies these to the product query and returns the matching, sorted, paginated products.
- All of these are **optional** — if none are given, it behaves like the normal full listing.

### B. Search bar (in the listing template)
- A text box + search button at the top of the listing page.
- Submitting it reloads the listing with `q=<keyword>`.

### C. Category filter (in the listing template)
- Shows the fixed categories (Electronics, Clothing, Home, Books, Beauty, Sports, Other) as clickable links/buttons, plus an "All" option.
- Clicking one reloads the listing filtered to that category.

### D. Sort dropdown (in the listing template)
- A dropdown: "Price: Low to High", "Price: High to Low", "Newest".
- Changing it reloads the listing sorted accordingly.

### E. Pagination controls (in the listing template)
- Shows page numbers / Next-Previous at the bottom.
- A fixed number of products per page (e.g. 12).

### F. Helper function `search_products(q, category, sort, page)`
- Builds the filtered, sorted, paginated query and returns the products plus paging info (total count, current page, total pages).

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Search by name
- **Given** products exist with different names
- **When** the shopper searches for a word that appears in some product names
- **Then** only the matching products are shown.

### AC-2: Search is forgiving of case
- **Given** a product named "Wireless Earbuds"
- **When** the shopper searches "wireless" or "WIRELESS"
- **Then** the product still matches (case-insensitive).

### AC-3: Filter by category
- **Given** products across several categories
- **When** the shopper clicks the "Electronics" category
- **Then** only Electronics products are shown.

### AC-4: Sort by price
- **Given** products with different prices
- **When** the shopper chooses "Price: Low to High"
- **Then** products appear ordered from cheapest to most expensive (and the reverse for High to Low).

### AC-5: Combine search + category + sort
- **Given** the shopper applies a search term AND a category AND a sort
- **When** the listing loads
- **Then** all three are applied together correctly.

### AC-6: Pagination works
- **Given** more products than fit on one page
- **When** the shopper opens the listing
- **Then** only one page's worth is shown, with working Next/Previous (or page number) controls, and filters/search stay applied across pages.

### AC-7: No results message
- **Given** a search term that matches nothing
- **When** the listing loads
- **Then** a friendly "No products found" message is shown (not a blank or broken page), with an easy way to clear the search.

### AC-8: Empty search behaves normally
- **Given** the shopper submits an empty search or visits `/products` directly
- **When** the page loads
- **Then** all products are shown as the normal full listing.

### AC-9: Filters reflected in the URL
- **Given** a shopper has applied a search/category/sort
- **When** they copy the page URL and open it again
- **Then** the same filtered results load (the state is in the URL).

---

## 7. Files to Change

- The product listing route → accept and apply `q`, `category`, `sort`, `page`.
- `templates/products/list.html` → add the search bar, category filter, sort dropdown, and pagination controls.
- The products module → add the `search_products()` helper.

## 8. Files to Create

- None expected (this enhances existing files). A small reusable pagination snippet/template partial is optional.

---

## 9. Dependencies

- No new external services or libraries.
- Reuses the existing database helpers and listing template.

---

## 10. Rules for Implementation

- Use **parameterized queries only** — the search keyword and filters must never be pasted directly into SQL (this is the most common place for security bugs, so it matters here).
- Search must be **case-insensitive** and match partial words (e.g. "ear" finds "Earbuds").
- All filters (`q`, `category`, `sort`, `page`) must be **optional and combinable** — any mix should work, including none.
- Keep the current filter state in the **URL query string**, so links are shareable and the back button works.
- Pagination: a sensible fixed page size (e.g. 12) — don't load everything at once.
- Sorting and filtering happen in the **database query**, not by loading all products and filtering in memory (keeps it fast as the catalog grows).
- Out-of-stock products should still appear in results (just marked), unless a future rule says otherwise.

---

## 11. Error Handling Expectations

- No matching results → friendly "No products found" message + a "clear filters" link, not a blank page.
- Invalid `page` number (e.g. page 999 or a non-number) → safely fall back to a valid page, no crash.
- Unknown `category` or `sort` value in the URL → ignore it gracefully and show normal results, no crash.

---

## 12. Out of Scope (handled by other features / later)

- Advanced filters like price range sliders, brand, ratings → future enhancement.
- Search autocomplete / suggestions as you type → future enhancement.
- Search across description text (not just names) → can be added later; start with name + category.
- This feature only finds and arranges products; it does not change cart, checkout, or product data.

---

## 13. Definition of Done

- [ ] A search bar finds products by name (partial, case-insensitive).
- [ ] Category filter shows only the chosen category, with an "All" option.
- [ ] Sort by price (low-to-high and high-to-low) works.
- [ ] Search + category + sort can be combined together.
- [ ] Pagination splits products across pages with working controls, keeping filters applied.
- [ ] A "No products found" message shows when nothing matches, with a way to clear.
- [ ] Visiting `/products` with no filters shows the full normal listing.
- [ ] Applied filters are reflected in the URL and reload the same results.
- [ ] Invalid page/category/sort values are handled gracefully (no crash).
- [ ] All search/filter queries use parameterized SQL.