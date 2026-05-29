# Spec Document — Checkout Process

## 1. Overview

Implement the **Checkout process** for the e-commerce website.

Checkout is the bridge between the shopping cart and a confirmed order. It takes the items a logged-in user has in their cart, collects the information needed to fulfil the order (shipping address, contact details), shows the user a final summary with the total cost, and — on confirmation — creates a pending **order** in the database.

This feature does **not** handle the actual money transfer. It prepares a valid order and hands it off to the Payment feature (next step). The goal of checkout is: turn a cart into a confirmed, payable order safely and clearly.

**Why this matters:** This is the highest-stakes screen in the whole site. Mistakes here (wrong total, lost items, double orders) directly cost money and trust. So correctness and clear validation are more important than fancy UI.

---

## 2. Depends on

- **Database Setup** (orders & order_items tables must exist)
- **User Authentication** (user must be logged in to checkout)
- **Product Catalog** (product price & stock come from here)
- **Shopping Cart** (the items being checked out)

Checkout is **handed off to**: Payment feature (created separately, after this).

---

## 3. User Stories

- **As a logged-in shopper**, I want to review all items in my cart with their prices before I pay, so that I can confirm my order is correct.
- **As a shopper**, I want to enter or select a shipping address, so that my order can be delivered to the right place.
- **As a shopper**, I want to see a clear breakdown of subtotal, shipping, and final total, so that I know exactly how much I will be charged.
- **As a shopper**, I want to be warned if an item in my cart is out of stock or its price changed, so that I am not charged for something unavailable or at the wrong price.
- **As a shopper**, I want my cart to become an order only once when I confirm, so that I am never accidentally charged twice.
- **As a store owner**, I want every checkout to create a complete, accurate order record, so that I can fulfil and track it later.

---

## 4. Database Schema

> These tables are created during Database Setup. Listed here so the checkout logic is clear.

### A. orders

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| status | TEXT | Not null, default `'pending'` |
| subtotal | REAL | Not null |
| shipping_fee | REAL | Not null, default 0 |
| total | REAL | Not null |
| shipping_name | TEXT | Not null |
| shipping_phone | TEXT | Not null |
| shipping_address | TEXT | Not null |
| created_at | TEXT | Default datetime('now') |

### B. order_items

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| order_id | INTEGER | Foreign key → orders.id, not null |
| product_id | INTEGER | Foreign key → products.id, not null |
| product_name | TEXT | Not null (snapshot of name at purchase time) |
| unit_price | REAL | Not null (snapshot of price at purchase time) |
| quantity | INTEGER | Not null, > 0 |
| line_total | REAL | Not null (unit_price × quantity) |

> **Important:** order_items store a **snapshot** of name and price. If the product price changes later, past orders must not change.

---

## 5. Routes / Functions to Implement

> Exact names depend on the chosen stack. Behaviour described below is the contract.

### A. Show checkout page  (`GET /checkout`)
- Requires logged-in user.
- Loads the user's current cart items.
- Recalculates each line from the **current** product price and stock.
- Displays: item list, subtotal, shipping fee, total, and an address form.
- If cart is empty → redirect to cart page with a message.

### B. Place order  (`POST /checkout`)
- Requires logged-in user.
- Validates the address form.
- Re-checks stock and price for every item **at the moment of placing** (not trusting the page).
- If valid → creates one `orders` row + one `order_items` row per item, sets status `pending`, clears/locks the cart, and returns the new `order_id`.
- Hands the user off to the Payment feature with this `order_id`.

### C. `calculate_totals(cart_items)`
- Computes subtotal, shipping fee, and total.
- Single source of truth for money math (used by both GET and POST).

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: View checkout with valid cart
- **Given** a logged-in user with 2 in-stock items in their cart
- **When** they open the checkout page
- **Then** both items are listed with correct unit price and quantity, and the subtotal, shipping, and total are shown correctly.

### AC-2: Empty cart cannot checkout
- **Given** a logged-in user with an empty cart
- **When** they try to open the checkout page
- **Then** they are redirected to the cart page with a "Your cart is empty" message and no order is created.

### AC-3: Must be logged in
- **Given** a user who is NOT logged in
- **When** they try to access checkout
- **Then** they are redirected to the login page.

### AC-4: Address is required
- **Given** a logged-in user on the checkout page
- **When** they submit with a missing or invalid name / phone / address
- **Then** the order is NOT created and a clear validation error is shown for the missing field.

### AC-5: Out-of-stock item blocks order
- **Given** a user whose cart contains an item that went out of stock
- **When** they try to place the order
- **Then** the order is NOT created, and they are told which item is unavailable and asked to update their cart.

### AC-6: Price change is detected
- **Given** a cart item whose product price changed since it was added
- **When** the user opens checkout or places the order
- **Then** the total reflects the **current** price, and the user is shown the updated total before confirming.

### AC-7: Successful order creation
- **Given** a logged-in user with a valid cart and valid address
- **When** they place the order
- **Then** exactly one `orders` row and matching `order_items` rows are created with status `pending`, the totals match `calculate_totals`, and the user is handed to payment with the new order id.

### AC-8: No double orders
- **Given** a user who clicks "Place Order" twice quickly (double submit)
- **When** the requests reach the server
- **Then** only ONE order is created.

### AC-9: Price snapshot is permanent
- **Given** a placed order containing product X at ₹100
- **When** product X's price later changes to ₹150
- **Then** the existing order still shows ₹100 for that line.

### AC-10: All-or-nothing creation
- **Given** order creation is in progress
- **When** an error occurs while inserting order_items
- **Then** the whole order is rolled back (no half-created order remains in the database).

---

## 7. Files to Change

- Cart module → expose a function to read the current user's cart items.
- Main app/routes file → add the checkout GET and POST routes.

## 8. Files to Create

- A checkout handler/module (logic for showing checkout + placing the order).
- A checkout page template/component (item review + address form + totals).

---

## 9. Dependencies

- No new external services for this feature (payment is separate).
- Reuses existing auth (login check) and database connection helpers.

---

## 10. Rules for Implementation

- **Never trust the price/total sent from the browser.** Always recalculate from the database at place-order time.
- **Re-check stock at place-order time**, not just on page load.
- Wrap order + order_items creation in a **single transaction** (all-or-nothing).
- Store **snapshots** of product name and price in order_items.
- Use **parameterized queries only** — never string-format values into SQL.
- `calculate_totals()` is the only place money math happens — no duplicate calculations elsewhere.
- Guard against **double submission** (e.g. disable button + server-side check).
- Money stored as REAL (float) consistently; round to 2 decimals on display.

---

## 11. Error Handling Expectations

- Empty cart at checkout → friendly redirect, no crash.
- Invalid address fields → field-level validation messages, order not created.
- Out-of-stock item → clear message naming the item, order not created.
- Database error mid-creation → full rollback, user sees a "could not place order, try again" message, no partial data saved.

---

## 12. Out of Scope (handled by other features)

- Actual payment / card processing → **Payment feature**.
- Order tracking & history screen → **Order Management feature**.
- Discount codes / coupons → future feature (not now).
- Shipping fee calculation by location/weight → start with a flat fee; advanced rules later.

---

## 13. Definition of Done

- [ ] Logged-out users are redirected to login from checkout.
- [ ] Empty cart redirects to cart with a message.
- [ ] Checkout page shows correct items, prices, subtotal, shipping, and total.
- [ ] Address validation works for name, phone, and address.
- [ ] Out-of-stock items block order creation with a clear message.
- [ ] Totals always recalculated from current DB prices, never from the browser.
- [ ] Placing an order creates exactly one order + correct order_items in a single transaction.
- [ ] Double-submit creates only one order.
- [ ] order_items keep a permanent price/name snapshot.
- [ ] On DB error, the whole order rolls back (no partial order).
- [ ] After success, user is handed to the Payment feature with the new order id.