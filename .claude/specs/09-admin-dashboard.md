# Spec Document — Admin Dashboard

## 1. Overview

Implement the **Admin Dashboard** — the private control panel where the **store owner** (admin) manages the shop: add/edit/remove products, and update order statuses as they get fulfilled.

So far the site works for customers, but the products were only the demo ones seeded in feature 01, and order statuses never change. This feature gives the owner the tools to actually run the store: put up new products, fix prices/stock, and move orders along (paid → shipped → delivered).

This is **admin-only** — normal customers must never reach it. So the first job of this feature is a clear separation between a normal user and an admin user.

**Why this matters:** Without this, the owner can't manage the store without editing the database by hand. This is what turns the project from a demo into a runnable shop. Because it has powerful abilities (changing products and orders), access control here is critical.

---

## 2. Depends on

- **User Authentication** (feature 02) — admin is a special logged-in user; needs the login system + a way to mark a user as admin.
- **Product Catalog** (feature 03) — admin manages the products this displays.
- **Order Management** (feature 08) — admin updates the statuses this displays.
- **Database Setup** (feature 01) — reads/writes `products` and `orders`.

Built on the existing **Flask + HTML templates** stack (same as previous features — no React).

---

## 3. User Stories

- **As the store owner**, I want a private admin area only I can access, so that customers can't change my products or orders.
- **As the admin**, I want to see all products in one place, so that I can manage my catalog.
- **As the admin**, I want to add a new product (name, description, price, stock, category, image), so that I can grow my store.
- **As the admin**, I want to edit an existing product, so that I can fix prices, stock, or details.
- **As the admin**, I want to delete a product, so that I can remove discontinued items.
- **As the admin**, I want to see all customer orders, so that I can fulfil them.
- **As the admin**, I want to update an order's status (paid → shipped → delivered), so that customers can see progress.
- **As a normal customer**, I want to be blocked from the admin area, so that the store stays secure.

---

## 4. Database Schema

> One small addition to the existing `users` table to mark who is an admin.

### users (updated)

| Column | Type | Note |
| --- | --- | --- |
| ... | | existing columns |
| is_admin | INTEGER | **new** — 0 for normal users (default), 1 for admin |

> The demo/first user (or a chosen email) is made admin. The plan should explain how to mark a user as admin safely (e.g. a one-time setup, not a public signup option — nobody should be able to make themselves admin).

> `products` and `orders` tables are used as-is (admin edits products, updates order `status`).

---

## 5. Routes / Functions to Implement

> All routes here are protected by an **admin-only** guard. Actions that change data are POST.

### A. Admin guard
- A check (like the existing "login required", but stricter) that allows only users with `is_admin = 1`.
- Normal logged-in users and logged-out visitors → blocked (redirected, friendly "not authorised").

### B. Admin home / dashboard  (`GET /admin`)
- Admin-only.
- A simple landing page with links to "Manage Products" and "Manage Orders", and maybe quick counts (total products, total orders).

### C. Manage products  (`GET /admin/products`)
- Lists all products with edit/delete buttons and an "Add product" button.

### D. Add product  (`GET` form + `POST /admin/products/add`)
- Form: name, description, price, stock, category (from the fixed list), image url.
- On submit → validates and inserts the new product.

### E. Edit product  (`GET` form + `POST /admin/products/<id>/edit`)
- Pre-filled form with the product's current values.
- On submit → validates and updates the product.

### F. Delete product  (`POST /admin/products/<id>/delete`)
- Removes the product (with a confirmation step in the UI).

### G. Manage orders  (`GET /admin/orders`)
- Lists ALL orders (all users), newest first, with customer, total, current status.

### H. Update order status  (`POST /admin/orders/<id>/status`)
- Changes an order's status to the next stage (e.g. a dropdown: paid → shipped → delivered).

### I. Helper functions
- `is_admin(user)` → true/false.
- Standard create/update/delete product helpers and an update-order-status helper.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Only admins can enter
- **Given** a normal (non-admin) logged-in user
- **When** they try to open any `/admin` page
- **Then** they are blocked with a friendly "not authorised" message.

### AC-2: Logged-out users blocked
- **Given** a logged-out visitor
- **When** they try to open an `/admin` page
- **Then** they are redirected to login.

### AC-3: Admin can view the dashboard
- **Given** a logged-in admin user
- **When** they open `/admin`
- **Then** they see the dashboard with links to manage products and orders.

### AC-4: Add a product
- **Given** an admin on the add-product form
- **When** they submit valid details
- **Then** the new product is saved and appears in both the admin product list and the public catalog.

### AC-5: Add product validation
- **Given** the add-product form
- **When** required fields are missing or price/stock are invalid (e.g. negative)
- **Then** the product is NOT saved and a clear validation message is shown.

### AC-6: Edit a product
- **Given** an existing product
- **When** the admin edits its price (or other field) and saves
- **Then** the change is reflected in the catalog and product page.

### AC-7: Delete a product
- **Given** an existing product
- **When** the admin confirms delete
- **Then** the product is removed from the catalog.

### AC-8: View all orders
- **Given** orders placed by multiple customers
- **When** the admin opens manage-orders
- **Then** all orders (across all users) are listed, newest first, with customer and status.

### AC-9: Update order status
- **Given** an order with status `paid`
- **When** the admin sets it to `shipped`
- **Then** the order's status updates, and the customer sees `shipped` on their own orders page.

### AC-10: Nobody can self-promote to admin
- **Given** the signup/profile flows
- **When** a normal user tries to make themselves admin
- **Then** there is no way to do so through the public site (admin is set only via the controlled setup).

---

## 7. Files to Change

- The `users` table / database helper → add `is_admin` column (safe migration) and a way to mark the chosen user as admin.
- The auth module → add the `is_admin` check / admin guard.
- The base template/nav bar → show an "Admin" link only to admin users.
- The product helpers → add create/update/delete.
- The orders helper → add update-status.

## 8. Files to Create

- An admin module/blueprint with all the admin routes and the admin guard.
- `templates/admin/dashboard.html` → the admin landing page.
- `templates/admin/products.html` → manage products list.
- `templates/admin/product_form.html` → add/edit product form (shared).
- `templates/admin/orders.html` → manage orders list.

---

## 9. Dependencies

- No new external services or libraries.
- Reuses existing auth, database helpers, and base template.

---

## 10. Rules for Implementation

- **Every** admin route must be behind the admin-only guard — no admin page or action reachable by a normal user.
- There must be **no public way to become admin** — `is_admin` is set only through a controlled, one-time setup (explained in the plan), never via signup or a form a user can reach.
- Destructive actions (delete product) require a **confirmation** step in the UI.
- Validate product input: price and stock must be non-negative numbers; category must be from the fixed list.
- Use **parameterized queries only** for all inserts/updates/deletes.
- Order status changes follow the agreed list (e.g. paid → shipped → delivered, and possibly cancelled).
- Deleting a product should not break existing orders — orders keep their stored snapshot of name/price (from feature 06), so old orders still display correctly even if the product is gone.

---

## 11. Error Handling Expectations

- Non-admin or logged-out access to any admin route → friendly block / redirect, never the admin content.
- Invalid product input → clear validation messages, nothing saved.
- Editing/deleting a non-existent product → handled gracefully, no crash.
- Updating status of a non-existent order → handled gracefully, no crash.

---

## 12. Out of Scope (handled by other features / later)

- Customer-facing features (cart, checkout, payment) → already done.
- Sales analytics / charts / revenue reports → future feature.
- Multiple admin roles / permission levels (e.g. manager vs super-admin) → future feature; for now a single admin flag is enough.
- Bulk product upload (CSV) → future feature.
- Image file uploads from the computer → for now use an image URL field; real file upload is a future enhancement.
- This feature gives the owner control over products and order statuses; it does not add analytics or advanced roles.

---

## 13. Definition of Done

- [ ] A `is_admin` flag exists on users, set only via a controlled setup (no public way to self-promote).
- [ ] Normal users and logged-out visitors are blocked from all `/admin` pages.
- [ ] An admin can open the dashboard with links to manage products and orders.
- [ ] An admin can add a product; it appears in the public catalog.
- [ ] Add/edit forms validate input (no negative price/stock, category from the list).
- [ ] An admin can edit a product and the change shows in the catalog.
- [ ] An admin can delete a product (with confirmation) without breaking past orders.
- [ ] An admin can view all customers' orders, newest first.
- [ ] An admin can update an order's status, and the customer sees the new status.
- [ ] All admin routes are behind the admin guard and use parameterized SQL.