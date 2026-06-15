import os
import sqlite3
from werkzeug.security import generate_password_hash

DATABASE = 'ecommerce.db'


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                email         TEXT    UNIQUE NOT NULL,
                password_hash TEXT    NOT NULL,
                created_at    TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS products (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                description TEXT,
                price       REAL    NOT NULL,
                stock       INTEGER NOT NULL DEFAULT 0,
                category    TEXT    NOT NULL,
                image_url   TEXT,
                created_at  TEXT    DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS cart_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                quantity   INTEGER NOT NULL CHECK (quantity > 0),
                created_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id)    REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

            CREATE TABLE IF NOT EXISTS orders (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id          INTEGER NOT NULL,
                status           TEXT    NOT NULL DEFAULT 'pending',
                total            REAL    NOT NULL,
                shipping_address TEXT    NOT NULL,
                created_at       TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );

            CREATE TABLE IF NOT EXISTS order_items (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id     INTEGER NOT NULL,
                product_id   INTEGER NOT NULL,
                product_name TEXT    NOT NULL,
                unit_price   REAL    NOT NULL,
                quantity     INTEGER NOT NULL CHECK (quantity > 0),
                FOREIGN KEY (order_id)   REFERENCES orders(id),
                FOREIGN KEY (product_id) REFERENCES products(id)
            );

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
        """)
        conn.commit()
    finally:
        conn.close()


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
        page = max(1, min(page, total_pages))

        products = conn.execute(
            f"SELECT * FROM products {where_sql} {order_sql} LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page]
        ).fetchall()
    finally:
        conn.close()

    return dict(products=products, total=total, page=page,
                total_pages=total_pages, per_page=per_page)


def get_cart_items(user_id):
    conn = get_db()
    try:
        return conn.execute("""
            SELECT ci.id, ci.product_id, ci.quantity,
                   p.name, p.price, p.image_url, p.stock,
                   (p.price * ci.quantity) AS line_total
            FROM cart_items ci
            JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.created_at
        """, (user_id,)).fetchall()
    finally:
        conn.close()


def calculate_cart_total(items):
    return sum(item['line_total'] for item in items)


def get_cart_count(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COALESCE(SUM(quantity), 0) FROM cart_items WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


def add_to_cart(user_id, product_id, qty=1):
    conn = get_db()
    try:
        product = conn.execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not product:
            return (False, 'Product not found')

        stock = product['stock']
        if stock == 0:
            return (False, 'This product is out of stock')

        existing = conn.execute(
            "SELECT id, quantity FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        ).fetchone()

        if existing:
            new_qty = min(existing['quantity'] + qty, stock)
            capped = new_qty < existing['quantity'] + qty
            conn.execute(
                "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
                (new_qty, user_id, product_id)
            )
        else:
            new_qty = min(qty, stock)
            capped = new_qty < qty
            conn.execute(
                "INSERT INTO cart_items (user_id, product_id, quantity) VALUES (?, ?, ?)",
                (user_id, product_id, new_qty)
            )

        conn.commit()
        if capped:
            return (True, f'Added to cart (quantity capped at {new_qty} due to available stock)')
        return (True, 'Added to cart!')
    finally:
        conn.close()


def update_cart_item(user_id, product_id, qty):
    if qty == 0:
        remove_cart_item(user_id, product_id)
        return (True, 'Item removed from cart')

    conn = get_db()
    try:
        product = conn.execute(
            "SELECT stock FROM products WHERE id = ?", (product_id,)
        ).fetchone()
        if not product:
            return (False, 'Product not found')

        new_qty = min(qty, product['stock'])
        capped = new_qty < qty
        conn.execute(
            "UPDATE cart_items SET quantity = ? WHERE user_id = ? AND product_id = ?",
            (new_qty, user_id, product_id)
        )
        conn.commit()
        if capped:
            return (True, f'Quantity updated (capped at {new_qty} due to available stock)')
        return (True, 'Quantity updated')
    finally:
        conn.close()


def remove_cart_item(user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM cart_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()


SHIPPING_FEE = 40.0  # flat ₹40; free when subtotal >= ₹500


def calculate_totals(items):
    subtotal = round(sum(item['price'] * item['quantity'] for item in items), 2)
    shipping_fee = 0.0 if subtotal >= 500 else SHIPPING_FEE
    total = round(subtotal + shipping_fee, 2)
    return {'subtotal': subtotal, 'shipping_fee': shipping_fee, 'total': total}


def place_order(user_id, shipping_name, shipping_phone, shipping_address):
    conn = get_db()
    try:
        items = conn.execute("""
            SELECT ci.product_id, ci.quantity, p.name, p.price, p.stock
            FROM cart_items ci JOIN products p ON p.id = ci.product_id
            WHERE ci.user_id = ?
            ORDER BY ci.created_at
        """, (user_id,)).fetchall()

        if not items:
            return False, 'Your cart is empty', None

        for item in items:
            if item['stock'] < item['quantity']:
                return False, f"'{item['name']}' is out of stock or has insufficient quantity", None

        totals = calculate_totals(items)

        conn.execute("BEGIN")
        cursor = conn.execute("""
            INSERT INTO orders
              (user_id, status, subtotal, shipping_fee, total,
               shipping_name, shipping_phone, shipping_address)
            VALUES (?, 'pending', ?, ?, ?, ?, ?, ?)
        """, (user_id, totals['subtotal'], totals['shipping_fee'], totals['total'],
              shipping_name, shipping_phone, shipping_address))
        order_id = cursor.lastrowid

        for item in items:
            line_total = round(item['price'] * item['quantity'], 2)
            conn.execute("""
                INSERT INTO order_items
                  (order_id, product_id, product_name, unit_price, quantity, line_total)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (order_id, item['product_id'], item['name'],
                  item['price'], item['quantity'], line_total))

        conn.execute("DELETE FROM cart_items WHERE user_id = ?", (user_id,))
        conn.commit()
        return True, 'Order placed successfully', order_id
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass
        return False, 'Could not place order, please try again', None
    finally:
        conn.close()


def get_order_by_id(order_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
    finally:
        conn.close()


def get_order_items(order_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM order_items WHERE order_id = ? ORDER BY id",
            (order_id,)
        ).fetchall()
    finally:
        conn.close()


def migrate_db():
    conn = get_db()
    try:
        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'google_id' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN google_id TEXT")
            conn.execute(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_google_id ON users (google_id)"
                " WHERE google_id IS NOT NULL"
            )

        orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
        for col, ddl in [
            ('shipping_name',  "ALTER TABLE orders ADD COLUMN shipping_name TEXT NOT NULL DEFAULT ''"),
            ('shipping_phone', "ALTER TABLE orders ADD COLUMN shipping_phone TEXT NOT NULL DEFAULT ''"),
            ('subtotal',       'ALTER TABLE orders ADD COLUMN subtotal REAL NOT NULL DEFAULT 0'),
            ('shipping_fee',   'ALTER TABLE orders ADD COLUMN shipping_fee REAL NOT NULL DEFAULT 0'),
        ]:
            if col not in orders_cols:
                conn.execute(ddl)

        oi_cols = [r[1] for r in conn.execute("PRAGMA table_info(order_items)").fetchall()]
        if 'line_total' not in oi_cols:
            conn.execute('ALTER TABLE order_items ADD COLUMN line_total REAL NOT NULL DEFAULT 0')

        orders_cols = [r[1] for r in conn.execute("PRAGMA table_info(orders)").fetchall()]
        for col, ddl in [
            ('payment_id',       'ALTER TABLE orders ADD COLUMN payment_id TEXT'),
            ('payment_order_id', 'ALTER TABLE orders ADD COLUMN payment_order_id TEXT'),
        ]:
            if col not in orders_cols:
                conn.execute(ddl)

        cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        if 'is_admin' not in cols:
            conn.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")

        admin_email = os.environ.get('ADMIN_EMAIL')
        if admin_email:
            conn.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (admin_email.lower(),))

        conn.execute("""
            CREATE TABLE IF NOT EXISTS wishlist_items (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    INTEGER NOT NULL,
                product_id INTEGER NOT NULL,
                added_at   TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id)    REFERENCES users(id),
                FOREIGN KEY (product_id) REFERENCES products(id),
                UNIQUE (user_id, product_id)
            )
        """)

        # users — phone, avatar, notify_email
        users_cols = [r[1] for r in conn.execute("PRAGMA table_info(users)").fetchall()]
        for col, ddl in [
            ('phone',        "ALTER TABLE users ADD COLUMN phone TEXT"),
            ('avatar',       "ALTER TABLE users ADD COLUMN avatar TEXT"),
            ('notify_email', "ALTER TABLE users ADD COLUMN notify_email INTEGER NOT NULL DEFAULT 1"),
        ]:
            if col not in users_cols:
                conn.execute(ddl)

        # addresses table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS addresses (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id      INTEGER NOT NULL,
                full_name    TEXT    NOT NULL,
                phone        TEXT    NOT NULL,
                address_line TEXT    NOT NULL,
                city         TEXT    NOT NULL,
                state        TEXT    NOT NULL,
                pincode      TEXT    NOT NULL,
                is_default   INTEGER NOT NULL DEFAULT 0,
                created_at   TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        conn.execute(
            "INSERT INTO users (name, email, password_hash, is_admin) VALUES (?, ?, ?, 1)",
            ("Demo User", "demo@example.com", generate_password_hash("demo1234")),
        )

        products = [
            ("Cumin Seeds (Jeera) 100g",        "Aromatic whole cumin seeds, perfect for tempering curries and rice",          75.0,  150, "Whole Spices",  "https://images.unsplash.com/photo-1596040033229-a9821ebd058d?w=400&q=80"),
            ("Turmeric Powder 100g",            "Pure turmeric powder with high curcumin, great for cooking and health",       89.0,  100, "Ground Spices", "https://images.unsplash.com/photo-1615485500704-8e990f9900f7?w=400&q=80"),
            ("Kashmiri Red Chilli Powder 100g", "Deep red colour with mild heat, ideal for tandoori and gravies",              99.0,   90, "Ground Spices", "https://images.unsplash.com/photo-1583119022894-919a68a3d0e3?w=400&q=80"),
            ("Garam Masala 100g",               "Classic blend of 12 slow-roasted whole spices, heart of Indian cooking",    120.0,   80, "Spice Blends",  "https://images.unsplash.com/photo-1505253304499-671c55fb57fe?w=400&q=80"),
            ("Black Pepper Whole 50g",          "Premium whole peppercorns, freshly packed for maximum aroma",               110.0,  120, "Whole Spices",  "https://images.unsplash.com/photo-1599909631372-91db5f6b6e54?w=400&q=80"),
            ("Coriander Powder 100g",           "Freshly ground dhaniya powder with warm citrusy flavour",                    65.0,  130, "Ground Spices", "https://images.unsplash.com/photo-1568158879083-c42860933ed7?w=400&q=80"),
            ("Cardamom Whole 50g",              "Premium green elaichi, hand-picked for intense aroma and flavour",          180.0,   70, "Whole Spices",  "https://images.unsplash.com/photo-1612198273689-dbb8e2fe9d72?w=400&q=80"),
            ("Himalayan Pink Salt 250g",        "Pure Himalayan rock salt, rich in minerals, perfect for everyday cooking",   95.0,  200, "Whole Spices",  "https://images.unsplash.com/photo-1518110925495-5fe2fda0442c?w=400&q=80"),
        ]
        conn.executemany(
            "INSERT INTO products (name, description, price, stock, category, image_url)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Account helpers
# ---------------------------------------------------------------------------

def get_user_by_id(user_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    finally:
        conn.close()


def update_profile(user_id, name, phone, avatar_path=None):
    conn = get_db()
    try:
        if avatar_path is not None:
            conn.execute(
                "UPDATE users SET name=?, phone=?, avatar=? WHERE id=?",
                (name, phone or None, avatar_path, user_id)
            )
        else:
            conn.execute(
                "UPDATE users SET name=?, phone=? WHERE id=?",
                (name, phone or None, user_id)
            )
        conn.commit()
    finally:
        conn.close()


def clear_avatar(user_id):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET avatar=NULL WHERE id=?", (user_id,))
        conn.commit()
    finally:
        conn.close()


def change_password(user_id, new_hash):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET password_hash=? WHERE id=?", (new_hash, user_id))
        conn.commit()
    finally:
        conn.close()


def update_notify_pref(user_id, notify_email):
    conn = get_db()
    try:
        conn.execute("UPDATE users SET notify_email=? WHERE id=?", (int(notify_email), user_id))
        conn.commit()
    finally:
        conn.close()


def get_addresses(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM addresses WHERE user_id=? ORDER BY is_default DESC, created_at ASC",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()


def get_address_by_id(address_id):
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM addresses WHERE id=?", (address_id,)).fetchone()
    finally:
        conn.close()


def add_address(user_id, full_name, phone, address_line, city, state, pincode):
    conn = get_db()
    try:
        count = conn.execute(
            "SELECT COUNT(*) FROM addresses WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        is_default = 1 if count == 0 else 0
        conn.execute("""
            INSERT INTO addresses (user_id, full_name, phone, address_line, city, state, pincode, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, full_name, phone, address_line, city, state, pincode, is_default))
        conn.commit()
    finally:
        conn.close()


def update_address(address_id, full_name, phone, address_line, city, state, pincode):
    conn = get_db()
    try:
        conn.execute("""
            UPDATE addresses SET full_name=?, phone=?, address_line=?, city=?, state=?, pincode=?
            WHERE id=?
        """, (full_name, phone, address_line, city, state, pincode, address_id))
        conn.commit()
    finally:
        conn.close()


def delete_address(user_id, address_id):
    conn = get_db()
    try:
        addr = conn.execute(
            "SELECT is_default FROM addresses WHERE id=? AND user_id=?",
            (address_id, user_id)
        ).fetchone()
        conn.execute("DELETE FROM addresses WHERE id=? AND user_id=?", (address_id, user_id))
        if addr and addr['is_default']:
            next_addr = conn.execute(
                "SELECT id FROM addresses WHERE user_id=? ORDER BY created_at ASC LIMIT 1",
                (user_id,)
            ).fetchone()
            if next_addr:
                conn.execute("UPDATE addresses SET is_default=1 WHERE id=?", (next_addr['id'],))
        conn.commit()
    finally:
        conn.close()


def set_default_address(user_id, address_id):
    conn = get_db()
    try:
        conn.execute("UPDATE addresses SET is_default=0 WHERE user_id=?", (user_id,))
        conn.execute("UPDATE addresses SET is_default=1 WHERE id=? AND user_id=?",
                     (address_id, user_id))
        conn.commit()
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Reviews helpers
# ---------------------------------------------------------------------------

def get_product_reviews(product_id):
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
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT product_id, AVG(rating) AS avg, COUNT(*) AS count FROM reviews GROUP BY product_id"
        ).fetchall()
        return {r['product_id']: {'avg': round(r['avg'], 1), 'count': r['count']} for r in rows}
    finally:
        conn.close()


def can_user_review(user_id, product_id):
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


# ---------------------------------------------------------------------------
# Wishlist helpers
# ---------------------------------------------------------------------------

def add_to_wishlist(user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO wishlist_items (user_id, product_id) VALUES (?, ?)",
            (user_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def remove_from_wishlist(user_id, product_id):
    conn = get_db()
    try:
        conn.execute(
            "DELETE FROM wishlist_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        )
        conn.commit()
    finally:
        conn.close()


def get_user_wishlist(user_id):
    conn = get_db()
    try:
        return conn.execute("""
            SELECT p.*
            FROM wishlist_items wi
            JOIN products p ON p.id = wi.product_id
            WHERE wi.user_id = ?
            ORDER BY wi.added_at DESC
        """, (user_id,)).fetchall()
    finally:
        conn.close()


def is_in_wishlist(user_id, product_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT 1 FROM wishlist_items WHERE user_id = ? AND product_id = ?",
            (user_id, product_id)
        ).fetchone()
        return row is not None
    finally:
        conn.close()


def get_wishlist_count(user_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT COUNT(*) FROM wishlist_items WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        return int(row[0])
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Admin helpers
# ---------------------------------------------------------------------------

def create_product(name, description, price, stock, category, image_url):
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO products (name, description, price, stock, category, image_url)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            (name, description, price, stock, category, image_url or None),
        )
        conn.commit()
    finally:
        conn.close()


def update_product(product_id, name, description, price, stock, category, image_url):
    conn = get_db()
    try:
        conn.execute(
            "UPDATE products SET name=?, description=?, price=?, stock=?, category=?, image_url=?"
            " WHERE id=?",
            (name, description, price, stock, category, image_url or None, product_id),
        )
        conn.commit()
    finally:
        conn.close()


def delete_product(product_id):
    conn = get_db()
    try:
        conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        conn.commit()
    finally:
        conn.close()


def get_all_orders_admin():
    conn = get_db()
    try:
        return conn.execute("""
            SELECT o.*, u.name AS customer_name, u.email AS customer_email
            FROM orders o
            JOIN users u ON u.id = o.user_id
            ORDER BY o.created_at DESC
        """).fetchall()
    finally:
        conn.close()


def update_order_status(order_id, status):
    conn = get_db()
    try:
        conn.execute("UPDATE orders SET status = ? WHERE id = ?", (status, order_id))
        conn.commit()
    finally:
        conn.close()
