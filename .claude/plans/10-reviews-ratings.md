# Plan — Feature 10: Reviews & Ratings

## Context

This is the final core feature of the e-commerce project. Product pages currently show no social proof — no ratings, no reviews. This plan implements verified-purchase reviews: only users with a paid order containing the product may leave a star rating and written comment. All visitors can read reviews. The feature adds a `reviews` table, a new `reviews.py` blueprint, enhances the product detail page, and optionally surfaces average ratings on the catalog listing cards.

---

## Files to Create

| File | Purpose |
|------|---------|
| `reviews.py` | Blueprint with add/edit/delete review routes |
| `templates/products/reviews_section.html` | Reviews section partial (included in detail.html) |
| `test_reviews_ratings.py` | AC tests following the `test_order_management.py` pattern |

---

## Files to Modify

| File | What changes |
|------|-------------|
| `db.py` | Add `reviews` table to `init_db()` + 6 new helper functions |
| `catalog.py` | Enhance `product_detail` route to pass review data; update `product_list` to pass ratings map |
| `templates/products/detail.html` | Include reviews_section partial + add styles |
| `templates/products/list.html` | Add star badge to product cards |
| `app.py` | Register reviews blueprint |

---

## Step 1 — Database: `db.py`

### 1a. Add `reviews` table in `init_db()`

Append to the existing `executescript` block (before the closing `"""`):

```sql
CREATE TABLE IF NOT EXISTS reviews (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    user_id    INTEGER NOT NULL,
    rating     INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    comment    TEXT,
    created_at TEXT    DEFAULT (datetime('now')),
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (user_id)    REFERENCES users(id),
    UNIQUE (product_id, user_id)
);
```

The `UNIQUE (product_id, user_id)` constraint enforces one review per user per product at the DB level.

### 1b. Add 6 helper functions

```python
def get_product_reviews(product_id):
    """All reviews for a product, newest first, with reviewer name."""
    conn = get_db()
    try:
        return conn.execute("""
            SELECT r.id, r.rating, r.comment, r.created_at,
                   u.name AS reviewer_name
            FROM reviews r
            JOIN users u ON r.user_id = u.id
            WHERE r.product_id = ?
            ORDER BY r.created_at DESC
        """, (product_id,)).fetchall()
    finally:
        conn.close()


def get_average_rating(product_id):
    """Returns {'avg': float|None, 'count': int}."""
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT AVG(rating) AS avg, COUNT(*) AS count FROM reviews WHERE product_id = ?",
            (product_id,)
        ).fetchone()
        avg = round(row['avg'], 1) if row['avg'] is not None else None
        return {'avg': avg, 'count': row['count']}
    finally:
        conn.close()


def get_all_avg_ratings():
    """Returns {product_id: {'avg': float, 'count': int}} for all products with reviews."""
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT product_id, AVG(rating) AS avg, COUNT(*) AS count FROM reviews GROUP BY product_id"
        ).fetchall()
        return {r['product_id']: {'avg': round(r['avg'], 1), 'count': r['count']} for r in rows}
    finally:
        conn.close()


def can_user_review(user_id, product_id):
    """True only if: user has a paid order containing product AND hasn't reviewed yet."""
    conn = get_db()
    try:
        purchased = conn.execute("""
            SELECT 1 FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            WHERE o.user_id = ? AND oi.product_id = ? AND o.status = 'paid'
            LIMIT 1
        """, (user_id, product_id)).fetchone()
        if not purchased:
            return False
        reviewed = conn.execute(
            "SELECT 1 FROM reviews WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        ).fetchone()
        return reviewed is None
    finally:
        conn.close()


def get_user_review(user_id, product_id):
    """Returns the user's existing review for a product, or None."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM reviews WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        ).fetchone()
    finally:
        conn.close()


def get_review_by_id(review_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM reviews WHERE id = ?", (review_id,)).fetchone()
    finally:
        conn.close()
```

---

## Step 2 — Blueprint: `reviews.py`

```python
from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required

from db import can_user_review, get_db, get_review_by_id

reviews = Blueprint('reviews', __name__)


@reviews.route('/products/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    try:
        rating = int(request.form.get('rating', 0))
    except ValueError:
        rating = 0
    if not (1 <= rating <= 5):
        flash('Please select a rating between 1 and 5.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=product_id))
    if not can_user_review(current_user.id, product_id):
        flash('You can only review products you have purchased.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=product_id))
    comment = request.form.get('comment', '').strip() or None
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
            (product_id, current_user.id, rating, comment)
        )
        conn.commit()
    finally:
        conn.close()
    flash('Review submitted. Thank you!', 'success')
    return redirect(url_for('catalog.product_detail', product_id=product_id))


@reviews.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != current_user.id:
        flash('Review not found or access denied.', 'error')
        return redirect(url_for('catalog.product_list'))
    try:
        rating = int(request.form.get('rating', 0))
    except ValueError:
        rating = 0
    if not (1 <= rating <= 5):
        flash('Please select a rating between 1 and 5.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=review['product_id']))
    comment = request.form.get('comment', '').strip() or None
    conn = get_db()
    try:
        conn.execute(
            "UPDATE reviews SET rating = ?, comment = ? WHERE id = ?",
            (rating, comment, review_id)
        )
        conn.commit()
    finally:
        conn.close()
    flash('Review updated.', 'success')
    return redirect(url_for('catalog.product_detail', product_id=review['product_id']))


@reviews.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != current_user.id:
        flash('Review not found or access denied.', 'error')
        return redirect(url_for('catalog.product_list'))
    product_id = review['product_id']
    conn = get_db()
    try:
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()
    flash('Review deleted.', 'success')
    return redirect(url_for('catalog.product_detail', product_id=product_id))
```

---

## Step 3 — Enhance `catalog.py`

### 3a. `product_detail` route

Update imports and route to pass review data:

```python
# Add to imports from db:
from db import ..., get_average_rating, get_product_reviews, can_user_review, get_user_review

@catalog.route('/products/<int:product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if product is None:
        abort(404)
    product_reviews = get_product_reviews(product_id)
    avg_data = get_average_rating(product_id)
    user_review = None
    can_review = False
    if current_user.is_authenticated:
        user_review = get_user_review(current_user.id, product_id)
        can_review = can_user_review(current_user.id, product_id)
    return render_template(
        'products/detail.html',
        product=product,
        product_reviews=product_reviews,
        avg_rating=avg_data['avg'],
        review_count=avg_data['count'],
        user_review=user_review,
        can_review=can_review
    )
```

### 3b. `product_list` route

Add `ratings` dict to the render call:

```python
from db import ..., get_all_avg_ratings

# Inside product_list():
ratings = get_all_avg_ratings()
return render_template('products/list.html', ..., ratings=ratings)
```

---

## Step 4 — Template: `templates/products/reviews_section.html`

New partial included at the bottom of `detail.html`. Contains:

- **Average rating bar**: `★ 4.2 (12 reviews)` — shown if `review_count > 0`, else "No reviews yet."
- **Add-review form** (only if `can_review`): 5-star radio buttons + comment textarea + submit.
- **User's existing review** (only if `user_review`): shows their review with Edit and Delete forms.
- **Review list**: loops `product_reviews` showing `reviewer_name`, stars, `comment`, `created_at`.

Star display uses Unicode `★` / `☆` filled from `rating`. CSS uses colors consistent with existing palette (`#1a1a2e`, `#888`, `#f39c12` for gold stars).

---

## Step 5 — Template: `templates/products/detail.html`

At the bottom of `{% block content %}`, before `{% endblock %}`:

```jinja
{% include 'products/reviews_section.html' %}
```

Add CSS for `.reviews-section`, `.stars`, `.review-card`, `.review-form` inside the existing `<style>` block.

---

## Step 6 — Template: `templates/products/list.html`

Inside `.card-body`, after the price line, add:

```jinja
{% set r = ratings.get(p['id']) %}
{% if r %}
    <p class="product-rating">★ {{ r.avg }} <span class="rating-count">({{ r.count }})</span></p>
{% endif %}
```

Add CSS: `.product-rating { color: #f39c12; font-size: .82rem; margin: .15rem 0; }`

---

## Step 7 — Register blueprint in `app.py`

```python
from reviews import reviews as reviews_blueprint
app.register_blueprint(reviews_blueprint)
```

---

## Step 8 — Test file: `test_reviews_ratings.py`

Follow `test_order_management.py` exactly:
- Temp DB via `tempfile.mkdtemp()`; `os.environ['DATABASE']` set before imports
- Helpers: `_create_user`, `_create_product`, `_create_order`, `_create_order_item`, `_create_review`, `_login`
- Tests: `test_ac1_buyer_can_review`, `test_ac2_nonbuyer_cannot_review`, `test_ac3_average_rating`, `test_ac4_reviews_listed`, `test_ac5_one_review_per_user`, `test_ac6_edit_review`, `test_ac7_delete_review`, `test_ac8_cannot_edit_others_review`, `test_ac9_invalid_rating`, `test_ac10_login_required`, `test_ac11_no_reviews_state`
- Manual runner at bottom tracking pass/fail count; cleanup with `shutil.rmtree`

---

## Verification

```bash
python test_reviews_ratings.py   # all 11 ACs green
python app.py                    # manual smoke test in browser:
                                 # - product page shows "No reviews yet"
                                 # - demo user with paid order sees review form
                                 # - star ratings appear on catalog cards after review submitted
```
