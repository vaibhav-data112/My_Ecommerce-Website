# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

**Python 3 + Flask + SQLite** (decided in feature `01-database-setup`).

Dependencies in `requirements.txt`:
- `flask>=3.0.0` — web framework
- `flask-login>=0.6.3` — session/authentication management
- `authlib>=1.3.0` — Google OAuth
- `python-dotenv>=1.0.0` — `.env` loading
- `requests>=2.31.0` — HTTP client
- `werkzeug` (bundled with Flask) — password hashing via `generate_password_hash` / `check_password_hash`
- `sqlite3` — Python stdlib database driver; database file is `ecommerce.db` in the project root

## Commands

```bash
# Install dependencies
python -m pip install -r requirements.txt

# Run the development server (auto-creates and seeds ecommerce.db on first run)
python app.py

# Run acceptance-criteria tests for a feature (uses a temp DB, safe to run anytime)
python test_auth.py
```

Test files follow the pattern `test_{feature-name}.py` — one per feature.

**Environment variables** (put in `.env`, never commit):
```
SECRET_KEY=<random string>
GOOGLE_CLIENT_ID=<from Google Cloud Console>
GOOGLE_CLIENT_SECRET=<from Google Cloud Console>
```

## Architecture

```
app.py      — Flask entry point: calls init_db(), migrate_db(), seed_db(), registers blueprints
db.py       — Database helpers: get_db(), init_db(), migrate_db(), seed_db()
auth.py     — Auth blueprint: signup/login/logout routes, User model, Flask-Login, Google OAuth
ecommerce.db — SQLite database file (auto-created; not committed)
templates/  — Jinja2 templates; all pages extend templates/base.html
```

**Startup sequence in `app.py`:** `init_db()` → `migrate_db()` → `seed_db()`. Schema changes added after the initial release go in `migrate_db()` (not `init_db()`), using `PRAGMA table_info` to check if a column already exists before `ALTER TABLE`.

**Blueprint pattern:** New features are implemented as Flask Blueprints (see `auth.py`). Each blueprint is created in its own module and registered in `app.py` via `app.register_blueprint(...)`.

**`db.py` patterns to follow in all future features:**
- `get_db()` opens `ecommerce.db`, sets `row_factory = sqlite3.Row`, and enables `PRAGMA foreign_keys = ON` on every connection.
- All SQL uses parameterised `?` placeholders — never string interpolation.
- Passwords are always stored via `generate_password_hash()`; checked via `check_password_hash()`.

**Auth patterns:**
- Import `login_required` from `auth.py` to protect routes.
- `current_user` from `flask_login` is available in all Jinja2 templates (injected by Flask-Login) — used in `base.html` for nav state.
- The `User` class (in `auth.py`) wraps a `sqlite3.Row` and implements `UserMixin`.

## Database Schema

Five tables (all created by `init_db()` in `db.py`):

| Table | Purpose |
|-------|---------|
| `users` | Registered accounts; has `google_id` column added via `migrate_db()` |
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
| 02 | `user-auth` | Signup, login, logout, password security, Google OAuth ✅ |
| 03 | `product-catalog` | Product list + detail page |
| 04 | `search-filter` | Search bar, category filters, pagination |
| 05 | `shopping-cart` | Add/remove items, quantity update |
| 06 | `checkout-flow` | Address, order summary, confirm order |
| 07 | `payment` | Razorpay / Stripe integration |
| 08 | `order-management` | Order history, status tracking |
| 09 | `admin-dashboard` | Manage products and orders |
| 10 | `reviews-ratings` | Product reviews and star ratings |
