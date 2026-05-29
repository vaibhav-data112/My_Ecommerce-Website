# Plan: Feature 08 — Order Management

## Context

After a user pays (feature 07), their order exists in the DB but there is no UI to view it. This feature adds an **order history page** (`/orders`) and an **order detail page** (`/orders/<id>`) so customers can review past purchases and track status. It also adds a "My Orders" nav link and a "View My Orders" button on the payment success page.

No new DB tables or columns are needed — the `orders` and `order_items` tables (with all migration columns) already hold everything required.

---

## Files Created

### `orders.py` — Blueprint

- `get_user_orders(user_id)` — SELECT from orders WHERE user_id = ? ORDER BY created_at DESC
- `get_order_detail(order_id, user_id)` — uses `get_order_by_id` + `get_order_items` from db.py, checks ownership
- `GET /orders` → `order_history()` [login_required]
- `GET /orders/<int:order_id>` → `order_detail(order_id)` [login_required]

### `templates/orders/list.html`
Order history table with status badges (colour-coded), empty-state message with "Browse Products" link.

### `templates/orders/detail.html`
Full order detail: delivery info, items table (snapshot prices), totals, status badge, paid/unpaid badge.

### `templates/orders/not_found.html`
404 page for non-existent or not-owned orders (no information leakage).

### `test_order_management.py`
9 acceptance-criteria tests covering AC-1 through AC-9.

---

## Files Modified

### `app.py`
- Added `from orders import orders`
- Added `app.register_blueprint(orders)`

### `templates/base.html`
- Added "My Orders" nav link inside `{% if current_user.is_authenticated %}` block

### `templates/payment/success.html`
- Added "View My Orders" button in the actions section

---

## Reused Utilities

| Utility | File | Purpose |
|---------|------|---------|
| `get_db()` | `db.py` | DB connection |
| `get_order_by_id(order_id)` | `db.py` | Fetch single order |
| `get_order_items(order_id)` | `db.py` | Fetch line items |
| `login_required` | `flask_login` | Route guard |
| `current_user` | `flask_login` | Logged-in user id |
