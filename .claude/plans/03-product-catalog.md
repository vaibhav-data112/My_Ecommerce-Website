# Implementation Plan — 03 Product Catalog

## Context

Features 01 and 02 established the foundation:
- `db.py` — `get_db()`, `init_db()`, `migrate_db()`, `seed_db()`; `products` table has `id`, `name`, `description`, `price`, `stock`, `category`, `image_url`, `created_at`; all 6 seed products have `image_url = NULL`
- `app.py` — Flask + Flask-Login + Authlib; `auth` Blueprint registered; `/` renders `index.html`
- `templates/base.html` — nav bar with login/logout state, flash messages, shared CSS (card, btn, form styles)

**No new external libraries** — pure Flask + Jinja2 + CSS.

---

## Database Changes

None. Reads from the existing `products` table.

---

## New Helper Functions in `db.py`

```python
def get_all_products():
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM products ORDER BY created_at DESC").fetchall()
    finally:
        conn.close()

def get_product_by_id(product_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    finally:
        conn.close()
```

Both use parameterised queries. `get_product_by_id` returns `None` if the id doesn't exist (caller handles it).

---

## Files to Create

### `catalog.py` — Products Blueprint

`url_prefix` not set (routes are `/products` and `/products/<id>`).

**Routes:**

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/products` | Product listing grid |
| GET | `/products/<int:product_id>` | Product detail page |
| POST | `/cart/add` | Placeholder — flashes "coming soon", redirects back |

**Route logic:**

`GET /products`:
- Call `get_all_products()`.
- If list is empty render the template with an empty list (template shows "No products yet").
- Render `products/list.html` with `products=rows`.

`GET /products/<int:product_id>`:
- Call `get_product_by_id(product_id)`.
- If `None` → `abort(404)` (handled by a registered 404 handler).
- Render `products/detail.html` with `product=row`.

`POST /cart/add`:
- Read `product_id` from form.
- Flash `'Shopping cart coming soon!'`, `'info'`.
- Redirect back to `url_for('catalog.product_detail', product_id=product_id)`.

**404 handler** (registered on the blueprint):

```python
@catalog.app_errorhandler(404)
def not_found(e):
    return render_template('products/not_found.html'), 404
```

---

### `templates/products/list.html`

Extends `base.html`. Title: "Shop — My Shop".

Layout:
```
<h1>All Products</h1>
[if products empty]
  <p class="empty-state">No products yet — check back soon.</p>
[else]
  <div class="product-grid">
    [for each product]
      <a class="product-card" href="/products/{{ product.id }}">
        [image or placeholder]
        [if stock == 0] <span class="badge-oos">Out of stock</span> [endif]
        <div class="card-body">
          <p class="product-name">{{ product.name }}</p>
          <p class="product-price">₹{{ "%.2f"|format(product.price) }}</p>
        </div>
      </a>
```

Image logic: `{% if product.image_url %}` → `<img src="{{ product.image_url }}">` else → `<div class="img-placeholder"><span>{{ product.category[0] }}</span></div>` (first letter of category as placeholder).

CSS (inline in the block or in `<style>`):
- `product-grid`: CSS Grid, `repeat(auto-fill, minmax(200px, 1fr))`, `gap: 1.25rem`
- `product-card`: white card, border-radius, hover shadow, text-decoration none
- `product-image` / `img-placeholder`: fixed height 180px, object-fit cover; placeholder is `#e8e8e8` bg with centered letter
- `badge-oos`: red badge overlay in top-right corner
- `product-name`: bold, 1-line truncation
- `product-price`: primary color, font-weight 600

---

### `templates/products/detail.html`

Extends `base.html`. Title: `{{ product.name }} — My Shop`.

Layout (two-column on desktop, stacked on mobile):
```
[left] image (or placeholder, larger — 360px tall)
[right]
  category badge
  h1: product.name
  price (large)
  description
  stock: "In stock (N left)" or "Out of stock" badge
  [if stock > 0]
    <form method="post" action="/cart/add">
      <input type="hidden" name="product_id" value="{{ product.id }}">
      <button type="submit" class="btn btn-primary">Add to Cart</button>
    </form>
  [else]
    <button class="btn btn-disabled" disabled>Out of Stock</button>
  [endif]
  <a href="/products">← Back to all products</a>
```

CSS: two-column flex layout (`flex-wrap: wrap`); image col `min-width: 280px, flex: 1`; details col `flex: 2, padding-left: 2rem`.

---

### `templates/products/not_found.html`

Extends `base.html`. Title: "Product Not Found".

Simple centred card:
```
<h2>Product not found</h2>
<p>We couldn't find that product.</p>
<a href="/products" class="btn btn-primary">Browse all products</a>
```

---

## Files to Change

### `db.py`
Add `get_all_products()` and `get_product_by_id(product_id)` (see above).

### `app.py`
- Import and register `catalog` Blueprint.
- Update `/` route to redirect to `/products` (or call `get_all_products()` directly and render the listing — redirect is simpler and avoids duplication).

```python
from catalog import catalog
app.register_blueprint(catalog)

@app.route('/')
def index():
    return redirect(url_for('catalog.product_list'))
```

---

## CSS additions in `base.html`

Add to the existing `<style>` block in `base.html`:

```css
.flash.info { background: #e8f4fd; color: #2471a3; border: 1px solid #3498db; }
.btn-disabled { background: #ccc; color: #666; cursor: not-allowed; width: 100%; text-align: center; }
```

(The `info` flash category is needed for the "cart coming soon" message.)

---

## Verification (Acceptance Criteria)

```bash
python app.py   # server starts

# AC-1: listing shows 6 products
curl http://127.0.0.1:5000/products  # 6 product names appear

# AC-2: browse without login — no redirect to /login
# AC-3: product card links → /products/1 shows "Wireless Earbuds"
# AC-4: detail shows name, description, price, stock
# AC-5: seed a stock=0 product and verify "Out of stock" badge + disabled button
# AC-6: /products/9999 → friendly not-found page, HTTP 404
# AC-7: in-stock detail has "Add to Cart" button; POST /cart/add flashes info msg
# AC-8: nav shows login/logout state on catalog pages

python test_catalog.py   # automated AC tests
```

---

## Test file: `test_catalog.py`

Inline test script (same pattern as `test_auth.py`):

- AC-1: `GET /products` returns 200 and all 6 product names
- AC-2: `GET /products` and `GET /products/1` work without a session cookie
- AC-3: `GET /products` response contains `/products/1` link
- AC-4: `GET /products/1` contains "Wireless Earbuds", price, description
- AC-5: Temporarily set a product's stock to 0 in test DB, verify "Out of stock" text
- AC-6: `GET /products/9999` returns 404 and "not found" text
- AC-7: `POST /cart/add` with `product_id=1` returns redirect, follow → flash message present
- AC-8: `GET /products` contains nav links (Login / Sign Up or user name)

---

## Definition of Done

- [ ] `GET /products` lists all products in a responsive grid (image/placeholder, name, price).
- [ ] Products viewable without logging in.
- [ ] Each product card links to its correct detail page.
- [ ] Detail page shows name, full description, price, image/placeholder, stock status.
- [ ] Out-of-stock products show "Out of stock" badge; Add to Cart button disabled/hidden.
- [ ] `GET /products/9999` shows friendly not-found page (HTTP 404), no crash.
- [ ] In-stock detail page has "Add to Cart" button (placeholder POST, flashes info).
- [ ] Nav bar shows correct login/logout state on catalog pages.
- [ ] Missing images show a styled placeholder, not a broken image.
- [ ] All DB reads use parameterised SQL.
- [ ] `test_catalog.py` — all ACs pass.
