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
