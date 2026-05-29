from functools import wraps

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from catalog import CATEGORIES
from db import (
    create_product, delete_product, get_all_orders_admin, get_all_products,
    get_order_by_id, get_product_by_id, update_order_status, update_product,
)

admin = Blueprint('admin', __name__, url_prefix='/admin')

ALLOWED_STATUSES = ['paid', 'shipped', 'delivered', 'cancelled']


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Not authorised.', 'error')
            return redirect(url_for('catalog.product_list'))
        return f(*args, **kwargs)
    return decorated


def _validate_product_form(form):
    name = form.get('name', '').strip()
    description = form.get('description', '').strip()
    image_url = form.get('image_url', '').strip()
    category = form.get('category', '').strip()
    error = None
    price = None
    stock = None

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
        order_count = conn.execute("SELECT COUNT(*) FROM orders").fetchone()[0]
    finally:
        conn.close()
    return render_template('admin/dashboard.html',
                           product_count=product_count, order_count=order_count)


# ---------------------------------------------------------------------------
# Products
# ---------------------------------------------------------------------------

@admin.route('/products')
@admin_required
def products():
    all_products = get_all_products()
    return render_template('admin/products.html', products=all_products)


@admin.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        error, name, description, price, stock, category, image_url = \
            _validate_product_form(request.form)
        if error:
            flash(error, 'error')
            return render_template('admin/product_form.html',
                                   action='Add', categories=CATEGORIES,
                                   form=request.form)
        create_product(name, description, price, stock, category, image_url)
        flash('Product added successfully.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html',
                           action='Add', categories=CATEGORIES, form={})


@admin.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin.products'))

    if request.method == 'POST':
        error, name, description, price, stock, category, image_url = \
            _validate_product_form(request.form)
        if error:
            flash(error, 'error')
            return render_template('admin/product_form.html',
                                   action='Edit', categories=CATEGORIES,
                                   form=request.form, product=product)
        update_product(product_id, name, description, price, stock, category, image_url)
        flash('Product updated successfully.', 'success')
        return redirect(url_for('admin.products'))
    return render_template('admin/product_form.html',
                           action='Edit', categories=CATEGORIES,
                           form=product, product=product)


@admin.route('/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def delete_product_route(product_id):
    product = get_product_by_id(product_id)
    if not product:
        flash('Product not found.', 'error')
        return redirect(url_for('admin.products'))
    delete_product(product_id)
    flash(f'"{product["name"]}" has been deleted.', 'success')
    return redirect(url_for('admin.products'))


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------

@admin.route('/orders')
@admin_required
def orders():
    all_orders = get_all_orders_admin()
    return render_template('admin/orders.html',
                           orders=all_orders, allowed_statuses=ALLOWED_STATUSES)


@admin.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_status(order_id):
    order = get_order_by_id(order_id)
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('admin.orders'))
    new_status = request.form.get('status', '').strip()
    if new_status not in ALLOWED_STATUSES:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin.orders'))
    update_order_status(order_id, new_status)
    flash(f'Order #{order_id} status updated to {new_status}.', 'success')
    return redirect(url_for('admin.orders'))
