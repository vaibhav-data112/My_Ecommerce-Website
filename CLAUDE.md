# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Tech Stack

**Backend:** Python 3 + Flask + SQLite  
**Frontend:** React 19 + Vite + Axios (plain CSS in `frontend/src/index.css` — no Tailwind, no Bootstrap)

Backend dependencies (`requirements.txt`): `flask>=3.0.0`, `flask-login>=0.6.3`, `flask-cors`, `authlib>=1.3.0`, `python-dotenv>=1.0.0`, `requests>=2.31.0`, `razorpay>=1.4.1`, `werkzeug`.

Frontend dependencies: `react`, `react-dom`, `react-router-dom`, `axios`.

## Commands

```bash
# ── Backend ───────────────────────────────────────────────────
python -m pip install -r requirements.txt   # install Python deps
python app.py                                # run Flask on port 5000 (auto-creates ecommerce.db)

# Run a feature's acceptance tests (temp DB, safe anytime)
python test_auth.py
python test_order_management.py
# Pattern: test_{feature-name}.py

# ── Frontend ──────────────────────────────────────────────────
cd frontend
npm install        # install JS deps
npm run dev        # Vite dev server at http://localhost:5173 (live reload)
npm run build      # compile React → frontend/dist/ (required for Flask to serve it)
npm run lint       # ESLint
```

**Critical:** Flask at port 5000 serves `frontend/dist/` — a static build snapshot. Frontend changes are invisible to Flask until `npm run build` is re-run. Use `localhost:5173` during development; build once when done to verify at `127.0.0.1:5000`.

**Environment variables** (put in `.env`, never commit):
```
SECRET_KEY=
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
```

## Architecture

### Two-Server Setup

```
localhost:5173  ← Vite dev server (React source, hot reload)
                   proxies /api/*, /login/google, /static/* → localhost:5000

127.0.0.1:5000  ← Flask API + serves frontend/dist/ for all non-API routes
```

Vite proxy is configured in `frontend/vite.config.js`. Flask CORS is enabled for `localhost:5173` and `localhost:5174` (in `app.py`). React always calls axios with `baseURL: '/api'` and `withCredentials: true` (session cookies).

### Backend (Flask)

```
app.py       — entry point: init_db → migrate_db → seed_db, CORS, registers blueprints,
               catch-all route serves frontend/dist/index.html for client-side routing
db.py        — get_db(), init_db(), migrate_db(), seed_db(), all shared SQL helpers
auth.py      — signup / login / logout / Google OAuth; User model (UserMixin)
catalog.py   — product list, detail, search/filter API
cart.py      — cart add / remove / update API
checkout.py  — shipping form, place_order() API
payment.py   — Razorpay order creation and verification API
orders.py    — order history and detail API
wishlist.py  — wishlist toggle / list API
reviews.py   — product reviews and star ratings API
account.py   — user profile, avatar upload API
admin.py     — admin: product CRUD, order status management API
```

**Startup sequence:** `init_db()` → `migrate_db()` → `seed_db()` on every Flask start.  
**Schema migrations:** new columns go in `migrate_db()` with a `PRAGMA table_info` guard before `ALTER TABLE` — never in `init_db()`.  
**DB patterns:** `get_db()` sets `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`. All SQL uses `?` placeholders — never f-strings or string interpolation.  
**Auth patterns:** protect routes with `login_required` from `flask_login`. `is_admin` column on `users` gates admin routes. The `User` class in `auth.py` wraps a `sqlite3.Row` and implements `UserMixin`.

### Frontend (React)

```
frontend/src/
  main.jsx              — React root
  App.jsx               — BrowserRouter → AuthProvider → CartProvider → Navbar + Routes + Footer
  index.css             — ALL styles: tokens, components, responsive breakpoints
  api/
    client.js           — axios instance (baseURL='/api', withCredentials: true)
    auth.js / cart.js / products.js / orders.js / wishlist.js / account.js / admin.js
  context/
    AuthContext.jsx     — useAuth(): user, login, signup, logout
    CartContext.jsx     — useCart(): cartItems, cartCount, fetchCart, addToCart, …
  components/
    Navbar.jsx          — sticky navbar + hamburger mobile drawer (mobileOpen state)
    AuthGuard.jsx       — redirects unauthenticated users to /login
    AdminGuard.jsx      — redirects non-admin users
    ProductCard.jsx / Footer.jsx / Spinner.jsx
  pages/
    HomePage / ProductsPage / ProductDetailPage / CartPage / CheckoutPage /
    PaymentPage / OrdersPage / OrderDetailPage / LoginPage / SignupPage /
    WishlistPage / AccountPage / NotFoundPage
    admin/  AdminDashboard / AdminProducts / AdminOrders
```

**Context pattern:** `AuthProvider` and `CartProvider` wrap the whole app in `App.jsx`. Access only via `useAuth()` and `useCart()` hooks — never import context objects directly.  
**API module pattern:** each `api/*.js` file imports `client` from `api/client.js` and exports named async functions. Components call these — never call axios directly from pages.  
**Route guards:** wrap protected `<Route>` elements with `<AuthGuard>` or `<AdminGuard>` in `App.jsx`.

### CSS / Design System

All styles live in `frontend/src/index.css`. No scoped CSS files, no CSS modules.

Two skills govern frontend work — read them before creating or editing any React component:
- `.claude/skills/ecommerce-ui-design/SKILL.md` — brand tokens, typography, component classes (`.btn`, `.card`, `.form-input`, etc.)
- `.claude/skills/responsive-page/SKILL.md` — breakpoints (480 / 768 / 1024px), hamburger pattern, grid rules, table wrapping, touch targets, pre-ship checklist

Key CSS rules:
- CSS Grid items need `min-width: 0` to prevent overflow beyond their `1fr` track.
- All `<table>` elements must be wrapped in `<div className="table-wrap">`.
- Mobile nav uses `.hamburger` / `.mobile-nav` / `.mobile-nav-link` classes (already in `index.css`).
- Never use inline `style` for `width`, `minWidth`, or `gridTemplateColumns` in JSX — put those in CSS classes with media query overrides.

## Database Schema

| Table | Key columns |
|-------|-------------|
| `users` | `id, name, email, password_hash, is_admin, google_id, phone, avatar` |
| `products` | `id, name, description, price, stock, category, image_url` |
| `cart_items` | `id, user_id, product_id, quantity` |
| `orders` | `id, user_id, status, shipping_name, shipping_phone, subtotal, shipping_fee, payment_id, payment_order_id` |
| `order_items` | `id, order_id, product_id, product_name, unit_price, quantity, line_total` |
| `wishlist` | `id, user_id, product_id` |
| `reviews` | `id, product_id, user_id, rating, comment, created_at` |

Seed data (inserted once on first run): demo user `demo@example.com` / `demo1234` and sample spice products.

## Development Methodology

**Spec-Driven Development (SDD)** — full workflow in `.claude/SDD-Instructions-Ecommerce.md`.

- Every feature: spec → plan → implement → validate → commit → PR → merge (16-step loop).
- Never implement before a spec and plan exist.
- Specs in `.claude/specs/NN-feature-name.md`; plans in `.claude/plans/NN-feature-name.md`.
- Each feature gets its own branch `feature/{feature-name}`. Never commit directly to `main`.

## Planned Feature Order

| NN | Branch | What it builds |
|----|--------|----------------|
| 01 | `database-setup` | Database schema ✅ |
| 02 | `user-auth` | Signup, login, logout, Google OAuth ✅ |
| 03 | `product-catalog` | Product list + detail ✅ |
| 04 | `search-filter` | Search, category filters, pagination ✅ |
| 05 | `shopping-cart` | Add / remove / update cart ✅ |
| 06 | `checkout-flow` | Address, order summary ✅ |
| 07 | `payment` | Razorpay integration ✅ |
| 08 | `order-management` | Order history, status tracking ✅ |
| 09 | `admin-dashboard` | Product CRUD, order status management ✅ |
| 10 | `reviews-ratings` | Product reviews and star ratings ✅ |
| 11 | `product-image-upload` | File upload to `static/uploads/products/` ✅ |
