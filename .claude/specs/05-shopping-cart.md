# Spec Document — Shopping Cart

## 1. Overview

Implement the **Shopping Cart** — the place where a logged-in user collects the products they intend to buy before checking out.

This is where the "Add to Cart" button (placed in feature 03) finally comes to life. The cart lets a user add products, see everything they've added in one place, change quantities, remove items, and see the running total — exactly like the cart on Amazon or Flipkart.

This feature has **one main page** (the cart page) plus the actions that change the cart (add, update quantity, remove).

**Why this matters:** The cart is the step right before buying. It's where the user reviews their choices and decides to proceed. Checkout (next feature) takes whatever is in this cart and turns it into an order — so the cart must be accurate and reliable.

---

## 2. Depends on

- **Database Setup** (feature 01) — the `cart_items` table already exists.
- **User Authentication** (feature 02) — a cart belongs to a logged-in user.
- **Product Catalog** (feature 03) — the "Add to Cart" button lives on the product detail page.

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As a logged-in shopper**, I want to add a product to my cart from its page, so that I can collect it for buying later.
- **As a shopper**, I want to see all items in my cart on one page, with their prices and a total, so that I can review my order.
- **As a shopper**, I want to change the quantity of an item in my cart, so that I can buy more or fewer without re-adding.
- **As a shopper**, I want to remove an item from my cart, so that I can change my mind.
- **As a shopper**, I want to see how many items are in my cart from any page (a cart icon with a count), so that I always know my cart status.
- **As a shopper**, I want my cart to be saved to my account, so that it's still there when I log in again later.
- **As a logged-out visitor**, I want to be asked to log in when I try to add to cart, so that my cart can be saved to my account.

---

## 4. Database Schema

> No changes needed. Uses the existing `cart_items` table from feature 01.

### cart_items (existing — for reference)

| Column | Type | Note |
| --- | --- | --- |
| id | INTEGER | cart row id |
| user_id | INTEGER | which user owns this cart row |
| product_id | INTEGER | which product |
| quantity | INTEGER | how many of this product |
| created_at | TEXT | when added |

> Rule: one row per (user + product). Adding the same product again should **increase the quantity** of the existing row, not create a duplicate row.

---

## 5. Routes / Functions to Implement

> Flask routes + Jinja templates, same pattern as previous features. Actions that change the cart should be POST.

### A. Add to cart  (`POST /cart/add`)
- Requires login (if logged out → redirect to login, then back).
- Takes a product id (and optional quantity, default 1).
- If the product is already in the cart → increase its quantity.
- If not → add a new cart row.
- Don't allow quantity above available stock.
- Redirect back to the product (or to the cart) with a "Added to cart" confirmation.

### B. View cart  (`GET /cart`)
- Requires login.
- Shows all the user's cart items: product name, image, unit price, quantity, line total.
- Shows the cart subtotal (sum of all line totals).
- Each item has quantity controls and a remove button.
- Shows a "Proceed to Checkout" button (checkout logic comes in the next feature; button can link to a placeholder for now).
- If the cart is empty → show a friendly "Your cart is empty" message with a link back to products.

### C. Update quantity  (`POST /cart/update`)
- Requires login.
- Changes the quantity of one cart item.
- If quantity is set to 0 → remove the item.
- Don't allow quantity above available stock.

### D. Remove item  (`POST /cart/remove`)
- Requires login.
- Removes one item from the cart.

### E. Cart count helper (for the nav bar)
- Returns the number of items in the current user's cart, so the nav bar can show a badge (e.g. 🛒 3) on every page.

### F. Helper functions
- `get_cart_items(user_id)` → the user's cart with product details and line totals.
- `add_to_cart(user_id, product_id, qty)` → add or increment.
- `calculate_cart_total(items)` → the subtotal (single source of truth for the math).

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Add a product to cart
- **Given** a logged-in user on a product page
- **When** they click "Add to Cart"
- **Then** that product appears in their cart with quantity 1 and a confirmation is shown.

### AC-2: Adding same product increases quantity
- **Given** a product already in the cart with quantity 1
- **When** the user adds the same product again
- **Then** the quantity becomes 2 (no duplicate row is created).

### AC-3: Logged-out user is asked to log in
- **Given** a logged-out visitor on a product page
- **When** they click "Add to Cart"
- **Then** they are redirected to login, and after logging in they can add to cart.

### AC-4: View cart shows correct items and total
- **Given** a user with 2 different products in their cart
- **When** they open the cart page
- **Then** both items show with correct unit price, quantity, and line total, and the subtotal equals the sum of the line totals.

### AC-5: Update quantity
- **Given** an item in the cart with quantity 2
- **When** the user changes it to 5
- **Then** the quantity updates to 5 and the line total and subtotal recalculate.

### AC-6: Setting quantity to zero removes the item
- **Given** an item in the cart
- **When** the user sets its quantity to 0
- **Then** the item is removed from the cart.

### AC-7: Remove an item
- **Given** an item in the cart
- **When** the user clicks remove
- **Then** the item disappears and the subtotal updates.

### AC-8: Cannot exceed stock
- **Given** a product with stock 3
- **When** the user tries to add or set quantity to 5
- **Then** the quantity is capped at the available stock and the user is informed.

### AC-9: Empty cart message
- **Given** a user with nothing in their cart
- **When** they open the cart page
- **Then** a friendly "Your cart is empty" message is shown with a link to browse products.

### AC-10: Cart count badge in nav
- **Given** a logged-in user with items in their cart
- **When** they view any page
- **Then** the nav bar shows the correct number of items.

### AC-11: Cart persists across sessions
- **Given** a user added items, then logged out
- **When** they log back in later
- **Then** their cart items are still there (saved to their account).

### AC-12: Each user sees only their own cart
- **Given** two different users
- **When** each views their cart
- **Then** they each see only their own items, never the other's.

---

## 7. Files to Change

- Main app/routes file → register the cart routes.
- The product detail template → wire the "Add to Cart" button to actually POST to `/cart/add`.
- The shared base template/nav bar → add the cart icon with the item count.
- The database helper → add the cart helper functions.

## 8. Files to Create

- A cart module/blueprint with the routes and helper functions.
- `templates/cart/cart.html` → the cart page.

---

## 9. Dependencies

- No new external services or libraries.
- Reuses existing auth (login guard), database helpers, and base template.

---

## 10. Rules for Implementation

- All cart pages and actions require **login** — use the existing "login required" guard from feature 02.
- A cart always belongs to **one user**; never mix users' carts. Always filter cart rows by the current `user_id`.
- **One row per (user + product)** — adding an existing product increments quantity, never duplicates.
- **Never let quantity exceed available stock.**
- Cart actions that change data (add, update, remove) must be **POST**, not GET.
- `calculate_cart_total()` is the **only** place the total is computed — no duplicate math.
- Use **parameterized queries only**.
- Prices/totals shown formatted nicely (₹, 2 decimals).
- The "Proceed to Checkout" button can be a placeholder link for now (checkout is the next feature) — it must not crash.

---

## 11. Error Handling Expectations

- Adding a non-existent product id → handled gracefully, no crash.
- Updating/removing an item that isn't in the user's cart → ignored gracefully, no crash.
- Quantity above stock → capped, with a clear message (not an error page).
- Logged-out access to any cart page/action → smooth redirect to login.
- Empty cart → friendly message, not a blank/broken page.

---

## 12. Out of Scope (handled by other features / later)

- Turning the cart into an order, address, payment → **Checkout** and **Payment** features (next).
- "Save for later" / wishlist → future feature.
- Guest cart (cart without logging in) → for now, login is required to add to cart; guest cart is a future enhancement.
- Discount codes applied to the cart → future feature.
- This feature only manages what's in the cart; it does not create orders or take payment.

---

## 13. Definition of Done

- [ ] A logged-in user can add a product to the cart from its page.
- [ ] Adding the same product again increases its quantity (no duplicate rows).
- [ ] A logged-out user is redirected to login when adding, then can add after logging in.
- [ ] The cart page shows all items with unit price, quantity, line total, and a correct subtotal.
- [ ] Quantity can be updated, and totals recalculate.
- [ ] Setting quantity to 0 removes the item.
- [ ] An item can be removed, and the subtotal updates.
- [ ] Quantity can never exceed available stock (capped + message).
- [ ] An empty cart shows a friendly message with a link to products.
- [ ] The nav bar shows the correct cart item count on every page.
- [ ] The cart persists after logging out and back in.
- [ ] Each user sees only their own cart.
- [ ] All cart queries use parameterized SQL and filter by the current user.