# Spec Document — Database Setup

## 1. Overview

Set up the **database foundation** for the e-commerce website.

This is the very first feature. It creates the database file and all the tables where the website will store its data — users, products, the shopping cart, orders, and order items.

Think of this step as building the **shelves and registers of the shop** before any customer arrives. Nothing is sold yet; we are just making the storage ready.

**Why this matters:** Every future feature (login, product listing, cart, checkout, payment) reads from and writes to this database. If the foundation is wrong here, every feature built on top will break. So this must be correct and stable before anything else.

---

## 2. Depends on

Nothing — this is the first step. It must be built before all other features.

---

## 3. User Stories

- **As the store owner**, I want a reliable place to store all my users, products, and orders, so that no data is lost.
- **As a developer (or Claude) building later features**, I want all tables ready with the correct structure, so that login, cart, and checkout features just work without redoing the database.
- **As the store owner**, I want some demo data to exist on first run, so that I can see the website working immediately without manually adding everything.

---

## 4. Database Schema

> These are the "registers" of the shop. Each table stores one kind of thing.

### A. users (who shops here)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| name | TEXT | Not null |
| email | TEXT | Unique, not null |
| password_hash | TEXT | Not null |
| created_at | TEXT | Default datetime('now') |

### B. products (what is for sale)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| name | TEXT | Not null |
| description | TEXT | Nullable |
| price | REAL | Not null |
| stock | INTEGER | Not null, default 0 |
| category | TEXT | Not null |
| image_url | TEXT | Nullable |
| created_at | TEXT | Default datetime('now') |

### C. cart_items (what a user is about to buy)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| product_id | INTEGER | Foreign key → products.id, not null |
| quantity | INTEGER | Not null, > 0 |
| created_at | TEXT | Default datetime('now') |

### D. orders (a confirmed purchase — the bill header)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| user_id | INTEGER | Foreign key → users.id, not null |
| status | TEXT | Not null, default `'pending'` |
| total | REAL | Not null |
| shipping_address | TEXT | Not null |
| created_at | TEXT | Default datetime('now') |

### E. order_items (the lines inside one bill)

| Column | Type | Constraints |
| --- | --- | --- |
| id | INTEGER | Primary key, autoincrement |
| order_id | INTEGER | Foreign key → orders.id, not null |
| product_id | INTEGER | Foreign key → products.id, not null |
| product_name | TEXT | Not null (snapshot of name at purchase time) |
| unit_price | REAL | Not null (snapshot of price at purchase time) |
| quantity | INTEGER | Not null, > 0 |

---

## 5. Functions to Implement

> Three small helper functions that set up and prepare the database.

### A. `get_db()`
- Opens a connection to the database file (e.g. `ecommerce.db`) in the project root.
- Configures it so rows can be read like a dictionary (by column name).
- Enables foreign key enforcement on every connection.
- Returns the connection.

### B. `init_db()`
- Creates ALL five tables using "create only if it does not already exist".
- Safe to run many times — never crashes on the second run.
- Makes sure the schema is ready before the app is used.

### C. `seed_db()`
- Checks if data already exists — if yes, do nothing (no duplicates).
- Inserts **one demo user** (with a properly hashed password, not plain text).
- Inserts **6 sample products** across different categories so the catalog isn't empty on first run.

---

## 6. Acceptance Criteria (Given / When / Then)

### AC-1: Database is created on startup
- **Given** a fresh project with no database file
- **When** the app starts for the first time
- **Then** the database file is created with all five tables.

### AC-2: Safe to run repeatedly
- **Given** the database already exists
- **When** the app starts again
- **Then** it starts without errors and does not break the existing tables.

### AC-3: Demo data appears once
- **Given** an empty database
- **When** `seed_db()` runs
- **Then** one demo user and six sample products are inserted.

### AC-4: No duplicate seed data
- **Given** the database already has the demo data
- **When** the app restarts and `seed_db()` runs again
- **Then** no duplicate user or products are added.

### AC-5: Passwords are never stored as plain text
- **Given** the demo user is created
- **When** you look at the stored password
- **Then** it is a hashed value, not the readable password.

### AC-6: Email must be unique
- **Given** a user already exists with an email
- **When** another user is added with the same email
- **Then** the database rejects it.

### AC-7: Relationships are enforced
- **Given** foreign keys are on
- **When** something tries to add an order for a user that doesn't exist
- **Then** the database rejects it.

---

## 7. Files to Change

- The main app file → import and call `init_db()` and `seed_db()` once on startup, so the database is ready before any page loads.

## 8. Files to Create

- A database helper file (containing `get_db`, `init_db`, `seed_db`).

---

## 9. Dependencies

- No new external services or accounts needed.
- Uses the database tool that comes with the chosen stack and a standard password-hashing helper.

---

## 10. Categories (Fixed List)

Use exactly these product categories so the catalog stays consistent:

- Electronics
- Clothing
- Home
- Books
- Beauty
- Sports
- Other

---

## 11. Rules for Implementation

- **Passwords must always be hashed**, never stored as plain text.
- Use **parameterized queries only** — never paste values directly into SQL (prevents hacking).
- Turn on **foreign key enforcement** on every connection (keeps data relationships valid).
- `seed_db()` must **never create duplicate** data on repeated runs.
- Prices stored as REAL (decimal), stock and quantity as whole numbers.
- `init_db()` must be **safe to run multiple times**.

---

## 12. Error Handling Expectations

- Adding a duplicate email → should be rejected with a clear error.
- Adding an order/cart item for a non-existent user or product → should be rejected.
- Any bad query → should raise a clear, understandable error (so problems are easy to debug later).

---

## 13. Out of Scope (handled by other features)

- The actual login/signup logic → **User Authentication feature**.
- Showing products on a page → **Product Catalog feature**.
- Cart, checkout, payment behaviour → their own features later.
- This feature ONLY sets up the storage; it does not build any user-facing pages.

---

## 14. Definition of Done

- [ ] Database file is created automatically on app startup.
- [ ] All five tables exist with the correct columns and constraints.
- [ ] The app starts again without errors (safe to re-run).
- [ ] One demo user exists with a hashed password.
- [ ] Six sample products exist across categories.
- [ ] No duplicate data is created on repeated runs.
- [ ] Duplicate email is rejected.
- [ ] Foreign key relationships are enforced.
- [ ] All queries use safe (parameterized) SQL.