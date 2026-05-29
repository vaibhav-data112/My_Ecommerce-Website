# Plan: 04 — Search & Filter

## Context

The product listing page (`/products`) currently fetches and displays all products with no filtering, sorting, or pagination. This plan enhances that page so shoppers can search by keyword, filter by category, sort by price, and navigate pages — all through URL query parameters so state is shareable and bookmarkable.

No schema changes are needed (reads from the existing `products` table). No new libraries are needed.

---

## Files to Change

| File | What changes |
|------|-------------|
| `db.py` | Add `search_products()` helper |
| `catalog.py` | Enhance `product_list()` route; add `CATEGORIES` and `VALID_SORTS` constants |
| `templates/products/list.html` | Add search bar, category buttons, sort dropdown, pagination, no-results message |

**New file:** `test_search_filter.py` — acceptance-criteria test suite.

---

## Step 1 — `db.py`: Add `search_products()`

Add below `get_product_by_id()`. Keep `get_all_products()` untouched (still used by existing tests).

```python
def search_products(q='', category='', sort='newest', page=1, per_page=12):
    where_clauses, params = [], []
    if q:
        where_clauses.append("LOWER(name) LIKE ?")
        params.append(f'%{q.lower()}%')
    if category:
        where_clauses.append("category = ?")
        params.append(category)

    where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
    order_sql = {
        'price_asc':  'ORDER BY price ASC',
        'price_desc': 'ORDER BY price DESC',
    }.get(sort, 'ORDER BY created_at DESC')

    conn = get_db()
    try:
        total = conn.execute(
            f"SELECT COUNT(*) FROM products {where_sql}", params
        ).fetchone()[0]

        total_pages = max(1, (total + per_page - 1) // per_page)
        page = max(1, min(page, total_pages))        # clamp to valid range

        products = conn.execute(
            f"SELECT * FROM products {where_sql} {order_sql} LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]
        ).fetchall()
    finally:
        conn.close()

    return dict(products=products, total=total, page=page,
                total_pages=total_pages, per_page=per_page)
```

**Security note:** `where_sql` and `order_sql` are built from whitelisted constants only — no user input is interpolated into SQL. All user-supplied values go through `?` placeholders.

---

## Step 2 — `catalog.py`: Enhance `product_list()`

Add at module level:
```python
CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Books', 'Beauty', 'Sports', 'Other']
VALID_SORTS = {'price_asc', 'price_desc', 'newest'}
```

Replace the `product_list()` function:
```python
@catalog.route('/products')
def product_list():
    q        = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    sort     = request.args.get('sort', 'newest')
    try:
        page = int(request.args.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    if sort not in VALID_SORTS:
        sort = 'newest'
    if category not in CATEGORIES:
        category = ''

    result = search_products(q=q, category=category, sort=sort, page=page)
    return render_template('products/list.html',
        products=result['products'],
        total=result['total'],
        page=result['page'],
        total_pages=result['total_pages'],
        q=q, category=category, sort=sort,
        categories=CATEGORIES,
    )
```

Update the import from `db`:
```python
from db import get_all_products, get_product_by_id, search_products
```

---

## Step 3 — `templates/products/list.html`: Add UI Controls

Restructure the template (keep the existing card styles, add new styles for controls):

### Layout structure
```
[Search bar form]
[Category filter row]          [Sort dropdown]
[Product grid / no-results]
[Pagination controls]
```

### Search bar
A GET form targeting `/products`. Preserve `category` and `sort` as hidden inputs so submitting a new search doesn't lose them.

```html
<form method="get" action="{{ url_for('catalog.product_list') }}">
  <input type="hidden" name="category" value="{{ category }}">
  <input type="hidden" name="sort" value="{{ sort }}">
  <input type="text" name="q" value="{{ q }}" placeholder="Search products…">
  <button type="submit">Search</button>
  {% if q or category %}
    <a href="{{ url_for('catalog.product_list') }}">Clear</a>
  {% endif %}
</form>
```

### Category buttons
Render as `<a>` links so each click is a GET request preserving `q` and `sort`, resetting `page` to 1.

```html
<a href="{{ url_for('catalog.product_list', q=q, sort=sort) }}"
   class="{{ 'active' if not category }}">All</a>
{% for cat in categories %}
  <a href="{{ url_for('catalog.product_list', q=q, category=cat, sort=sort) }}"
     class="{{ 'active' if category == cat }}">{{ cat }}</a>
{% endfor %}
```

### Sort dropdown
Wrapped in a form with hidden `q` and `category`; submits on `change`.

```html
<form method="get" action="{{ url_for('catalog.product_list') }}">
  <input type="hidden" name="q" value="{{ q }}">
  <input type="hidden" name="category" value="{{ category }}">
  <select name="sort" onchange="this.form.submit()">
    <option value="newest"     {{ 'selected' if sort=='newest' }}>Newest</option>
    <option value="price_asc"  {{ 'selected' if sort=='price_asc' }}>Price: Low to High</option>
    <option value="price_desc" {{ 'selected' if sort=='price_desc' }}>Price: High to Low</option>
  </select>
</form>
```

### Product count
Change to use the server-supplied `total` (not `products|length`) so it reflects the full match count, not just one page.

### No-results message
```html
{% if total == 0 %}
  <p class="empty-state">No products found for your search.
    <a href="{{ url_for('catalog.product_list') }}">Clear filters</a>
  </p>
{% endif %}
```

### Pagination controls
```html
{% if total_pages > 1 %}
  {% if page > 1 %}
    <a href="{{ url_for('catalog.product_list', q=q, category=category, sort=sort, page=page-1) }}">Previous</a>
  {% endif %}
  {% for p in range(1, total_pages + 1) %}
    <a href="{{ url_for('catalog.product_list', q=q, category=category, sort=sort, page=p) }}"
       class="{{ 'active' if p == page }}">{{ p }}</a>
  {% endfor %}
  {% if page < total_pages %}
    <a href="{{ url_for('catalog.product_list', q=q, category=category, sort=sort, page=page+1) }}">Next</a>
  {% endif %}
{% endif %}
```

---

## Step 4 — `test_search_filter.py`: Acceptance-Criteria Tests

One test per AC (AC-1 through AC-9). Pattern mirrors `test_catalog.py`:
- Use a temp DB, seed it with known products spanning multiple categories and prices.
- Test the Flask test client against `/products?q=...&category=...&sort=...&page=...`.
- Assert response status 200 and that the right product names appear/are absent in the HTML.

Key test cases:
| Test | Query | Assert |
|------|-------|--------|
| AC-1 search by name | `?q=earbuds` | only Wireless Earbuds visible |
| AC-2 case-insensitive | `?q=WIRELESS` | Wireless Earbuds visible |
| AC-3 category filter | `?category=Electronics` | only Electronics products |
| AC-4a sort price asc | `?sort=price_asc` | cheapest product appears before expensive |
| AC-4b sort price desc | `?sort=price_desc` | most expensive first |
| AC-5 combined | `?q=ear&category=Electronics&sort=price_asc` | correct intersection |
| AC-6 pagination | seed 15 products, `?page=2` | page 2 items present, page 1 items absent |
| AC-7 no results | `?q=xyznotexist` | "No products found" in response |
| AC-8 empty search | `/products` | all products shown |
| AC-9 URL state | `?q=mug&category=Home&sort=price_asc` | 200 and correct results |

---

## Verification

```bash
# Run the new acceptance tests
python test_search_filter.py

# Start the dev server and manually verify in browser
python app.py
# Visit: http://localhost:5000/products
# Test: search bar, category buttons, sort dropdown, pagination, clear link
```

Existing tests should still pass:
```bash
python test_catalog.py
python test_auth.py
```
