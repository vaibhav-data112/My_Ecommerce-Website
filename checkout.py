import re as _re
import threading
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import calculate_totals, get_cart_items, get_db, get_user_by_id, place_order
from email_utils import send_order_confirmation

checkout = Blueprint('checkout', __name__, url_prefix='/api')

_CODE_RE_CO = _re.compile(r'^[A-Z0-9\-]{3,20}$')


def _validate_coupon_at_checkout(conn, code, subtotal):
    coupon = conn.execute(
        "SELECT * FROM coupons WHERE code = ?", (code,)
    ).fetchone()

    if not coupon:
        return None, 0.0, "Invalid coupon code."
    if not coupon['is_active']:
        return None, 0.0, "This coupon is no longer active."
    if coupon['expiry_date']:
        try:
            expiry = datetime.strptime(coupon['expiry_date'], '%Y-%m-%d').date()
            if expiry < datetime.now(timezone.utc).date():
                return None, 0.0, "This coupon has expired."
        except ValueError:
            return None, 0.0, "This coupon has expired."
    if coupon['max_uses'] > 0 and coupon['used_count'] >= coupon['max_uses']:
        return None, 0.0, "This coupon has reached its usage limit."
    if subtotal < coupon['min_order_amount']:
        return None, 0.0, (
            f"Minimum order of ₹{coupon['min_order_amount']:.0f} required for this coupon."
        )

    if coupon['discount_type'] == 'percentage':
        discount = round(subtotal * coupon['discount_value'] / 100, 2)
    else:
        discount = coupon['discount_value']
    discount = min(round(discount, 2), subtotal)

    return coupon, discount, None


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
    coupon_code_raw  = data.get('coupon_code', '').strip().upper() or None
    payment_method   = data.get('payment_method', 'razorpay').strip().lower()
    if payment_method not in ('razorpay', 'cod'):
        payment_method = 'razorpay'

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

    coupon_code     = None
    discount_amount = 0.0

    if coupon_code_raw:
        if not _CODE_RE_CO.match(coupon_code_raw):
            return jsonify({'error': 'Invalid coupon code format.'}), 400

        items = get_cart_items(user_id)
        if not items:
            return jsonify({'error': 'Your cart is empty.'}), 400
        raw_subtotal = round(sum(item['price'] * item['quantity'] for item in items), 2)

        conn = get_db()
        try:
            _, discount_amount, err = _validate_coupon_at_checkout(conn, coupon_code_raw, raw_subtotal)
        finally:
            conn.close()

        if err:
            return jsonify({'error': err}), 400
        coupon_code = coupon_code_raw

    ok, message, order_id = place_order(
        user_id, shipping_name, shipping_phone, shipping_address,
        coupon_code=coupon_code, discount_amount=discount_amount,
        payment_method=payment_method,
    )
    if not ok:
        return jsonify({'error': message}), 400

    # Send confirmation email in background (never blocks the response)
    try:
        user_row = get_user_by_id(user_id)
        user = dict(user_row) if user_row else None
    except Exception:
        user = None

    if user and user.get('notify_email', 1) and user.get('email'):
        try:
            conn = get_db()
            try:
                items_for_mail = conn.execute(
                    "SELECT oi.product_name AS name, oi.quantity, oi.unit_price AS price "
                    "FROM order_items oi WHERE oi.order_id = ?", (order_id,)
                ).fetchall()
                order_row = conn.execute(
                    "SELECT total FROM orders WHERE id = ?", (order_id,)
                ).fetchone()
                items_list = [dict(i) for i in items_for_mail]
                order_total = order_row['total'] if order_row else 0
            finally:
                conn.close()

            threading.Thread(
                target=send_order_confirmation,
                args=(order_id, user['name'], user['email'],
                      items_list, order_total, shipping_address, payment_method),
                daemon=True,
            ).start()
        except Exception:
            pass  # email failure must never affect order response

    return jsonify({'success': True, 'order_id': order_id, 'payment_method': payment_method})
