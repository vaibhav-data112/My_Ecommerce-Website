from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from db import (add_to_cart as db_add_to_cart, calculate_cart_total,
                get_cart_items, remove_cart_item, update_cart_item)

cart = Blueprint('cart', __name__)


@cart.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    try:
        product_id = int(request.form.get('product_id', 0))
        qty = max(1, int(request.form.get('quantity', 1)))
    except (ValueError, TypeError):
        flash('Invalid request', 'error')
        return redirect(url_for('catalog.product_list'))

    user_id = int(current_user.id)
    success, message = db_add_to_cart(user_id, product_id, qty)
    flash(message, 'success' if success else 'error')

    referrer = request.referrer
    if referrer:
        return redirect(referrer)
    return redirect(url_for('catalog.product_detail', product_id=product_id))


@cart.route('/cart')
@login_required
def view_cart():
    user_id = int(current_user.id)
    items = get_cart_items(user_id)
    subtotal = calculate_cart_total(items)
    return render_template('cart/cart.html', items=items, subtotal=subtotal)


@cart.route('/cart/update', methods=['POST'])
@login_required
def update_quantity():
    try:
        product_id = int(request.form.get('product_id', 0))
        qty = int(request.form.get('quantity', 1))
    except (ValueError, TypeError):
        flash('Invalid request', 'error')
        return redirect(url_for('cart.view_cart'))

    user_id = int(current_user.id)
    _, message = update_cart_item(user_id, product_id, qty)
    flash(message, 'info')
    return redirect(url_for('cart.view_cart'))


@cart.route('/cart/remove', methods=['POST'])
@login_required
def remove_item():
    try:
        product_id = int(request.form.get('product_id', 0))
    except (ValueError, TypeError):
        return redirect(url_for('cart.view_cart'))

    user_id = int(current_user.id)
    remove_cart_item(user_id, product_id)
    flash('Item removed from cart', 'info')
    return redirect(url_for('cart.view_cart'))
