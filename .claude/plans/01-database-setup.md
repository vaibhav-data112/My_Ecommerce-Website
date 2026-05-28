# Implementation Plan — 01 Database Setup

## Context

This is the first feature of the e-commerce project. No application code existed. The goal is to create the SQLite database foundation with five tables and helper functions so that every future feature (auth, catalog, cart, checkout, payments) has a correct, stable data layer to build on.

Tech stack chosen: **Python 3 + Flask + SQLite**. The spec's schema uses SQLite-specific types (`INTEGER`, `TEXT`, `REAL`, `datetime('now')`) and Python-style function names (`get_db`, `init_db`, `seed_db`), confirming this choice. `sqlite3` is part of the Python standard library; `werkzeug` (bundled with Flask) provides password hashing.

---

## Files Created

### `requirements.txt`
```
flask>=3.0.0
```

### `db.py` — Database helper module
Three functions:

**`get_db()`** — Opens `ecommerce.db`, sets `row_factory = sqlite3.Row`, enables `PRAGMA foreign_keys = ON`, returns connection.

**`init_db()`** — Creates all five tables with `CREATE TABLE IF NOT EXISTS` using `executescript()`. Table order: `users` → `products` → `cart_items` → `orders` → `order_items` (respects FK dependencies). `quantity` columns have `CHECK (quantity > 0)`.

**`seed_db()`** — Guards with `SELECT COUNT(*) FROM users`; if > 0, returns immediately. Otherwise inserts one demo user (`demo@example.com` / `demo1234` hashed via `generate_password_hash`) and 6 sample products via `executemany`.

Sample products:
| Name | Price | Stock | Category |
|------|-------|-------|----------|
| Wireless Earbuds | 29.99 | 50 | Electronics |
| Cotton T-Shirt | 9.99 | 100 | Clothing |
| Yoga Mat | 24.99 | 40 | Sports |
| Python Programming Book | 39.99 | 20 | Books |
| Face Moisturizer | 14.99 | 60 | Beauty |
| Ceramic Mug Set | 12.99 | 75 | Home |

### `app.py` — Flask entry point
Creates Flask app, calls `init_db()` and `seed_db()` at module level, runs dev server when executed directly.

---

## Security Rules Applied

- Passwords: `generate_password_hash(plain)` only.
- All SQL: parameterised `?` placeholders only.
- FK enforcement: `PRAGMA foreign_keys = ON` in every `get_db()` call.

---

## Verification (7 Acceptance Criteria)

```bash
pip install -r requirements.txt
python app.py          # AC-1: ecommerce.db created; AC-2: second run clean

# AC-3 & AC-4
python -c "import sqlite3; conn=sqlite3.connect('ecommerce.db'); conn.row_factory=sqlite3.Row; print([r[0] for r in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()]); print(conn.execute('SELECT COUNT(*) FROM users').fetchone()[0], 'users,', conn.execute('SELECT COUNT(*) FROM products').fetchone()[0], 'products')"

# AC-5: password is hashed
python -c "import sqlite3; conn=sqlite3.connect('ecommerce.db'); print(conn.execute('SELECT password_hash FROM users').fetchone()[0])"

# AC-6: duplicate email rejected
python -c "import sqlite3; conn=sqlite3.connect('ecommerce.db'); conn.execute('PRAGMA foreign_keys=ON'); [conn.execute(\"INSERT INTO users(name,email,password_hash)VALUES('X','demo@example.com','x')\") for _ in [0]]" 2>&1

# AC-7: FK enforced
python -c "import sqlite3; conn=sqlite3.connect('ecommerce.db'); conn.execute('PRAGMA foreign_keys=ON'); conn.execute(\"INSERT INTO orders(user_id,status,total,shipping_address)VALUES(9999,'pending',0,'x')\")" 2>&1
```
