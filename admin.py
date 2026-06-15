import os
import uuid
from functools import wraps

from flask import Blueprint, jsonify, redirect, request, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename

from catalog import CATEGORIES
from db import (
    append_status_history, create_product, delete_product, get_all_orders_admin,
    get_all_products, get_order_by_id, get_product_by_id, update_courier_details,
    update_product,
)

admin = Blueprint('admin', __name__, url_prefix='/api/admin')

ALLOWED_STATUSES = [
    'paid', 'packed', 'shipped', 'out_for_delivery', 'delivered',
    'cancelled', 'returned', 'refunded',
]
UPLOAD_FOLDER    = os.path.join('static', 'uploads', 'products')
ALLOWED_EXT      = {'jpg', 'jpeg', 'png', 'webp'}
MAX_FILE_BYTES   = 5 * 1024 * 1024


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({'error': 'Authentication required', 'login_required': True}), 401
        if not current_user.is_admin:
            return jsonify({'error': 'Admin access required.'}), 403
        return f(*args, **kwargs)
    return decorated


def _save_uploaded_image():
    file = request.files.get('image_file')
    if not file or not file.filename:
        return None, None
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
    if ext not in ALLOWED_EXT:
        return None, 'Invalid file type. Allowed: jpg, jpeg, png, webp.'
    data = file.read()
    if len(data) > MAX_FILE_BYTES:
        return None, 'File too large. Maximum size is 5 MB.'
    safe_name   = secure_filename(file.filename)
    unique_name = f'{uuid.uuid4().hex}_{safe_name}'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with open(os.path.join(UPLOAD_FOLDER, unique_name), 'wb') as f:
        f.write(data)
    return f'uploads/products/{unique_name}', None


def _validate_product_form(form):
    name        = form.get('name', '').strip()
    description = form.get('description', '').strip()
    image_url   = form.get('image_url', '').strip()
    category    = form.get('category', '').strip()
    error = price = stock = None

    if not name:
        error = 'Product name is required.'
    elif not category or category not in CATEGORIES:
        error = 'Please select a valid category.'
    else:
        try:
            price = float(form.get('price', ''))
            if price < 0:
                error = 'Price must be 0 or greater.'
        except (ValueError, TypeError):
            error = 'Price must be a valid number.'
        if error is None:
            try:
                stock = int(form.get('stock', ''))
                if stock < 0:
                    error = 'Stock must be 0 or greater.'
            except (ValueError, TypeError):
                error = 'Stock must be a whole number.'

    if error is None:
        uploaded_path, upload_error = _save_uploaded_image()
        if upload_error:
            error = upload_error
        elif uploaded_path:
            image_url = uploaded_path

    return error, name, description, price, stock, category, image_url


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@admin.route('', strict_slashes=False)
@admin_required
def dashboard():
    from db import get_db
    conn = get_db()
    try:
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        order_count   = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
        revenue       = conn.execute(
            "SELECT COALESCE(SUM(total),0) FROM orders WHERE status != 'cancelled'"
        ).fetchone()[0]
    finally:
        conn.close()
    return jsonify({
        'product_count': product_count,
        'order_count':   order_count,
        'revenue':       revenue,
        'categories':    CATEGORIES,
    })


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@admin.route('/products')
@admin_required
def products():
    all_products = get_all_products()
    return jsonify({'products': [dict(p) for p in all_products], 'categories': CATEGORIES})


@admin.route('/products/add', methods=['POST'])
@admin_required
def add_product():
    error, name, description, price, stock, category, image_url = \
        _validate_product_form(request.form)
    if error:
        return jsonify({'error': error}), 422
    create_product(name, description, price, stock, category, image_url)
    return jsonify({'success': True, 'message': 'Product added successfully.'}), 201


@admin.route('/products/<int:product_id>', methods=['GET'])
@admin_required
def get_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404
    return jsonify({'product': dict(product), 'categories': CATEGORIES})


@admin.route('/products/<int:product_id>/edit', methods=['POST'])
@admin_required
def edit_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404
    error, name, description, price, stock, category, image_url = \
        _validate_product_form(request.form)
    if error:
        return jsonify({'error': error}), 422
    update_product(product_id, name, description, price, stock, category, image_url)
    return jsonify({'success': True, 'message': 'Product updated successfully.'})


@admin.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product_route(product_id):
    product = get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found.'}), 404
    delete_product(product_id)
    return jsonify({'success': True, 'message': f'"{product["name"]}" has been deleted.'})


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@admin.route('/orders')
@admin_required
def orders():
    all_orders = get_all_orders_admin()
    return jsonify({
        'orders':           [dict(o) for o in all_orders],
        'allowed_statuses': ALLOWED_STATUSES,
    })


@admin.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_status(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404
    data       = request.get_json(silent=True) or {}
    new_status = data.get('status', '').strip()
    if new_status not in ALLOWED_STATUSES:
        return jsonify({'error': 'Invalid status.'}), 400

    note            = (data.get('note')            or '').strip() or None
    courier_name    = (data.get('courier_name')    or '').strip() or None
    tracking_number = (data.get('tracking_number') or '').strip() or None

    append_status_history(order_id, new_status, note=note)
    if new_status == 'shipped':
        update_courier_details(order_id, courier_name, tracking_number)

    return jsonify({'success': True, 'message': f'Order #{order_id} updated to {new_status}.'})
