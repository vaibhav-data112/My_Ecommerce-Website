# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

**Python 3 + Flask + SQLite** (decided in feature `01-database-setup`).

- `flask>=3.0.0` is the only external dependency (declared in `requirements.txt`).
- `werkzeug` (bundled with Flask) provides password hashing via `generate_password_hash` / `check_password_hash`.
- `sqlite3` is Python's stdlib database driver; the database file is `ecommerce.db` in the project root.

## Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run the development server (auto-creates and seeds ecommerce.db on first run)
python app.py

# Run acceptance-criteria tests (uses a temp DB, safe to run anytime)
python test_auth.py
```

**Environment variables** (put in `.env`, never commit):
```
SECRET_KEY=<random string>
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
```

## Architecture

```
app.py      — Flask application entry point; calls init_db() and seed_db() at startup
db.py       — Database helper module: get_db(), init_db(), seed_db()
ecommerce.db — SQLite database file (created automatically; not committed)
```

**`db.py` patterns to follow in all future features:**
- `get_db()` opens `ecommerce.db`, sets `row_factory = sqlite3.Row`, and enables `PRAGMA foreign_keys = ON` on every connection.
- All SQL uses parameterised `?` placeholders — never string interpolation.
- Passwords are always stored via `generate_password_hash()`; checked via `check_password_hash()`.

## Database Schema

Five tables (all created by `init_db()` in `db.py`):

| Table | Purpose |
|-------|---------|
| `users` | Registered accounts |
| `products` | Product catalogue with stock |
| `cart_items` | Per-user shopping cart (FK → users, products) |
| `orders` | Confirmed order header (FK → users) |
| `order_items` | Line items inside an order — snapshots `product_name` and `unit_price` at purchase time |

Seed data (inserted once on first run): 1 demo user (`demo@example.com` / `demo1234`) and 6 products across the fixed category list: Electronics, Clothing, Home, Books, Beauty, Sports, Other.

## Development Methodology

This project uses **Spec-Driven Development (SDD)**. The full workflow is in `.claude/SDD-Instructions-Ecommerce.md`. Key rules:

- Every feature follows a **16-step loop**: spec → plan → implement → validate → commit → PR → merge.
- **Never implement before a spec and plan exist** for that feature.
- Specs live in `.claude/specs/NN-feature-name.md`; plans live in `.claude/plans/NN-feature-name.md`. Both are committed.
- Each feature gets its own branch: `feature/{feature-name}`. Never work directly on `main`.
- Merge to `main` only after the feature is fully validated against its spec.

## Planned Feature Order

| NN | Branch | What it builds |
|----|--------|----------------|
| 01 | `database-setup` | Database schema — users, products, orders tables ✅ |
| 02 | `user-auth` | Signup, login, logout, password security |
| 03 | `product-catalog` | Product list + detail page |
| 04 | `search-filter` | Search bar, category filters, pagination |
| 05 | `shopping-cart` | Add/remove items, quantity update |
| 06 | `checkout-flow` | Address, order summary, confirm order |
| 07 | `payment` | Razorpay / Stripe integration |
| 08 | `order-management` | Order history, status tracking |
| 09 | `admin-dashboard` | Manage products and orders |
| 10 | `reviews-ratings` | Product reviews and star ratings |
