# Spec Document — Order Management

## 1. Overview

Implement **Order Management** — the part of the website where a logged-in customer can see all the orders they've placed and check the details and status of each one.

After a customer pays (feature 07), the order exists in the system. This feature gives them a place to look back at it: an **order history page** listing all their past orders, and an **order detail page** showing everything about one order — items, amounts, delivery address, payment status, and current order status (e.g. pending, paid, shipped, delivered).

Real e-commerce sites all have this: Amazon's "Your Orders", Flipkart's "My Orders". It's where customers go to confirm what they bought and track it.

**Why this matters:** Customers need to trust that their purchase is recorded and visible. After paying, "where did my order go?" is the first question — this feature answers it. It also sets up the status field that the Admin Dashboard (next) will update as orders are fulfilled.

---

## 2. Depends on

- **User Authentication** (feature 02) — orders belong to a logged-in user.
- **Checkout** (feature 06) — created the orders and order_items.
- **Payment** (feature 07) — sets the `paid` status this feature displays.
- **Database Setup** (feature 01) — reads from `orders` and `order_items`.

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As a customer**, I want to see a list of all my past orders, so that I can keep track of what I've bought.
- **As a customer**, I want to click an order and see its full details, so that I can review the items, amounts, and delivery address.
- **As a customer**, I want to see the current status of each order (e.g. paid, shipped, delivered), so that I know where it is.
- **As a customer**, I want my most recent order shown first, so that I find it quickly.
- **As a customer**, I want to only ever see my own orders, so that my purchase history stays private.
- **As a customer with no orders yet**, I want a friendly message instead of a blank page, so that I'm not confused.

---

## 4. Database Schema

> No changes strictly required. Reads from the existing `orders` and `order_items` tables.

> Optional nice-to-have: the `status` field already exists on `orders`. This feature displays it. Recognised status values (a simple agreed list):
> `pending` → `paid` → `shipped` → `delivered` (and possibly `cancelled`).
> The Admin Dashboard (next feature) will be the one that moves an order from `paid` to `shipped`/`delivered`.

---

## 5. Routes / Functions to Implement

> Flask routes + Jinja templates, same pattern as previous features.

### A. Order history page  (`GET /orders`)
- Requires login.
- Lists all orders belonging to the current user, **most recent first**.
- Each row shows: order id (or a friendly order number), date, total, status, and a link to its detail page.
- If the user has no orders → friendly "You haven't placed any orders yet" message with a link to products.

### B. Order detail page  (`GET /orders/<order_id>`)
- Requires login and **ownership** (the order must belong to the current user).
- Shows: the items in the order (name, unit price, quantity, line total — from the snapshot stored at purchase time), the order subtotal/total, the delivery address, the payment status, and the order status.
- If the order doesn't exist or doesn't belong to the user → friendly "Order not found" page (don't reveal other users' orders).

### C. "My Orders" link in the nav bar
- A link visible to logged-in users that goes to their order history.

### D. Helper functions
- `get_user_orders(user_id)` → the user's orders, newest first.
- `get_order_detail(order_id, user_id)` → one order with its items, only if owned by that user.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Order history lists the user's orders
- **Given** a logged-in user who has placed 3 orders
- **When** they open the order history page
- **Then** all 3 orders are listed, newest first, each showing date, total, and status.

### AC-2: Newest order appears first
- **Given** a user with multiple orders placed on different dates
- **When** they view their history
- **Then** the most recent order is at the top.

### AC-3: Order detail shows full info
- **Given** a user opens one of their orders
- **When** the detail page loads
- **Then** it shows the items (with the prices saved at purchase time), the total, the delivery address, payment status, and order status.

### AC-4: Prices reflect purchase-time snapshot
- **Given** an order placed when a product cost ₹100, and the product's price later changed
- **When** the user views that old order
- **Then** it still shows ₹100 for that item (uses the stored snapshot, not the current price).

### AC-5: Users see only their own orders
- **Given** order X belongs to user A
- **When** user B tries to open order X's detail page
- **Then** they get a friendly "Order not found" page and cannot see it.

### AC-6: Login required
- **Given** a logged-out visitor
- **When** they try to open the orders page
- **Then** they are redirected to login first.

### AC-7: No orders message
- **Given** a logged-in user who has never ordered
- **When** they open the order history page
- **Then** a friendly "no orders yet" message is shown with a link to products (not a blank page).

### AC-8: Status is shown clearly
- **Given** orders with different statuses (paid, shipped, delivered)
- **When** the user views their history and details
- **Then** each status is shown clearly and readably.

### AC-9: "My Orders" link works
- **Given** a logged-in user on any page
- **When** they click "My Orders" in the nav
- **Then** they reach their order history.

---

## 7. Files to Change

- Main app/routes file → register the orders routes.
- The shared base template/nav bar → add a "My Orders" link for logged-in users.
- The database helper → add the order history/detail helper functions.
- (Optional) the payment success page → add a link to "View my orders".

## 8. Files to Create

- An orders module/blueprint with the routes and helper functions.
- `templates/orders/history.html` → the order list page.
- `templates/orders/detail.html` → the single order page.
- An "order not found" message/template (can be simple).

---

## 9. Dependencies

- No new external services or libraries.
- Reuses existing auth (login guard), database helpers, and base template.

---

## 10. Rules for Implementation

- All order pages require **login** — use the existing "login required" guard.
- Always filter orders by the **current user's id**; never show one user another user's orders.
- Order detail must use the **snapshot** prices/names stored in `order_items` (not current product prices).
- Orders listed **newest first**.
- Use **parameterized queries only**.
- Amounts shown formatted nicely (₹, 2 decimals).
- Status values come from the agreed simple list; display them in a readable way (e.g. a coloured label).
- "Order not found" and "not your order" should look the same to the user (don't reveal that an order exists but belongs to someone else).

---

## 11. Error Handling Expectations

- Non-existent or not-owned order id → friendly "Order not found" page, no crash, no leaking other users' data.
- User with no orders → friendly empty-state message, not a blank/broken page.
- Logged-out access → smooth redirect to login.

---

## 12. Out of Scope (handled by other features / later)

- **Admin updating order status** (paid → shipped → delivered) → **Admin Dashboard feature** (next). This feature only *displays* status.
- Cancelling or returning an order → future feature.
- Refunds → future feature.
- Live delivery tracking with a courier → future feature.
- Invoices/receipts download → future feature.
- This feature only lets a customer **view** their own orders; it doesn't change orders or statuses.

---

## 13. Definition of Done

- [ ] A logged-in user can see a list of all their orders, newest first.
- [ ] Each order in the list shows date, total, and status.
- [ ] Clicking an order opens its detail page with items, total, delivery address, and statuses.
- [ ] Order details use the purchase-time price snapshot, not current prices.
- [ ] A user can never see another user's orders (friendly "not found" instead).
- [ ] Logged-out users are redirected to login.
- [ ] A user with no orders sees a friendly empty-state message.
- [ ] Order status is displayed clearly.
- [ ] A "My Orders" link in the nav reaches the history page.
- [ ] All order queries are filtered by the current user and use parameterized SQL.