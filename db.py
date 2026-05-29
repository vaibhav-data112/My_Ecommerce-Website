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

        conn.commit()
    finally:
        conn.close()


def seed_db():
    conn = get_db()
    try:
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] > 0:
            return

        conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@example.com", generate_password_hash("demo1234")),
        )

        products = [
            ("Wireless Earbuds",       "Bluetooth earbuds with noise cancellation", 29.99, 50,  "Electronics", None),
            ("Cotton T-Shirt",         "Comfortable everyday wear",                  9.99, 100, "Clothing",    None),
            ("Yoga Mat",               "Non-slip exercise mat",                     24.99,  40, "Sports",      None),
            ("Python Programming Book","Learn Python from scratch",                 39.99,  20, "Books",       None),
            ("Face Moisturizer",       "Daily hydrating cream",                     14.99,  60, "Beauty",      None),
            ("Ceramic Mug Set",        "Set of 4 ceramic mugs",                     12.99,  75, "Home",        None),
        ]
        conn.executemany(
            "INSERT INTO products (name, description, price, stock, category, image_url)"
            " VALUES (?, ?, ?, ?, ?, ?)",
            products,
        )
        conn.commit()
    finally:
        conn.close()
