from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import calculate_totals, get_cart_items, place_order

checkout = Blueprint('checkout', __name__, url_prefix='/api')


@checkout.route('/checkout', methods=['GET'])
@login_required
def checkout_info():
    user_id = int(current_user.id)
    items = get_cart_items(user_id)
    if not items:
        return jsonify({'error': 'Your cart is empty.'}), 400
    totals = calculate_totals(items)
    return jsonify({
        'items':  [dict(i) for i in items],
        **totals,
    })


@checkout.route('/checkout', methods=['POST'])
@login_required
def checkout_page():
    user_id = int(current_user.id)
    data    = request.get_json(silent=True) or {}

    shipping_name    = data.get('shipping_name', '').strip()
    shipping_phone   = data.get('shipping_phone', '').strip()
    shipping_address = data.get('shipping_address', '').strip()

    errors = {}
    if not shipping_name:
        errors['shipping_name'] = 'Full name is required.'
    if not shipping_phone or not shipping_phone.replace('+', '').replace(' ', '').isdigit() \
            or len(shipping_phone.replace('+', '').replace(' ', '')) < 10:
        errors['shipping_phone'] = 'A valid phone number (at least 10 digits) is required.'
    if not shipping_address:
        errors['shipping_address'] = 'Shipping address is required.'

    if errors:
        return jsonify({'errors': errors}), 422

    ok, message, order_id = place_order(user_id, shipping_name, shipping_phone, shipping_address)
    if not ok:
        return jsonify({'error': message}), 400

    return jsonify({'success': True, 'order_id': order_id})
