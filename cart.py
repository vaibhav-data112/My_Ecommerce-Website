from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import (add_to_cart as db_add_to_cart, calculate_cart_total,
                get_cart_count, get_cart_items, remove_cart_item, update_cart_item)

cart = Blueprint('cart', __name__, url_prefix='/api')


@cart.route('/cart/add', methods=['POST'])
@login_required
def add_to_cart():
    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data.get('product_id', 0))
        qty        = max(1, int(data.get('quantity', 1)))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid request'}), 400

    user_id = int(current_user.id)
    success, message = db_add_to_cart(user_id, product_id, qty)
    cart_count = get_cart_count(user_id)
    return jsonify({'success': success, 'message': message, 'cart_count': cart_count}), (200 if success else 400)


@cart.route('/cart')
@login_required
def view_cart():
    user_id  = int(current_user.id)
    items    = get_cart_items(user_id)
    subtotal = calculate_cart_total(items)
    return jsonify({
        'items':      [dict(i) for i in items],
        'subtotal':   subtotal,
        'cart_count': len(items),
    })


@cart.route('/cart/update', methods=['POST'])
@login_required
def update_quantity():
    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data.get('product_id', 0))
        qty        = int(data.get('quantity', 1))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid request'}), 400

    user_id = int(current_user.id)
    _, message = update_cart_item(user_id, product_id, qty)
    cart_count = get_cart_count(user_id)
    return jsonify({'success': True, 'message': message, 'cart_count': cart_count})


@cart.route('/cart/remove', methods=['POST'])
@login_required
def remove_item():
    data = request.get_json(silent=True) or {}
    try:
        product_id = int(data.get('product_id', 0))
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid request'}), 400

    user_id = int(current_user.id)
    remove_cart_item(user_id, product_id)
    cart_count = get_cart_count(user_id)
    return jsonify({'success': True, 'message': 'Item removed from cart', 'cart_count': cart_count})
