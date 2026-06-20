import hashlib
import hmac
import os

import razorpay
from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import get_db, get_order_by_id, get_order_items

payment = Blueprint('payment', __name__, url_prefix='/api')


def _rz_client():
    return razorpay.Client(auth=(
        os.environ.get('RAZORPAY_KEY_ID', ''),
        os.environ.get('RAZORPAY_KEY_SECRET', '')
    ))


@payment.route('/payment/<int:order_id>')
@login_required
def pay_page(order_id):
    order = get_order_by_id(order_id)
    if not order:
        return jsonify({'error': 'Order not found.'}), 404

    if int(order['user_id']) != int(current_user.id):
        return jsonify({'error': 'Forbidden'}), 403

    if order['status'] == 'paid':
        return jsonify({'already_paid': True, 'order_id': order_id})

    if order.get('payment_method') == 'cod' and order['status'] not in ('cod_pending',):
        return jsonify({'is_cod': True, 'order_id': order_id})

    if order['status'] not in ('pending', 'cod_pending'):
        return jsonify({'error': 'This order cannot be paid.'}), 400

    try:
        rz_order = _rz_client().order.create({
            'amount':          int(order['total'] * 100),
            'currency':        'INR',
            'receipt':         str(order_id),
            'payment_capture': 1
        })
    except Exception:
        return jsonify({'error': 'Could not connect to payment gateway. Please try again.'}), 502

    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET payment_order_id = ? WHERE id = ?",
            (rz_order['id'], order_id)
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({
        'order':        dict(order),
        'rz_order_id':  rz_order['id'],
        'key_id':       os.environ.get('RAZORPAY_KEY_ID', ''),
        'amount_paisa': int(order['total'] * 100),
    })


@payment.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    data          = request.get_json(silent=True) or {}
    rz_order_id   = data.get('razorpay_order_id', '')
    rz_payment_id = data.get('razorpay_payment_id', '')
    rz_signature  = data.get('razorpay_signature', '')

    conn = get_db()
    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE payment_order_id = ? AND user_id = ?",
            (rz_order_id, int(current_user.id))
        ).fetchone()
    finally:
        conn.close()

    if not order:
        return jsonify({'error': 'Payment could not be verified.'}), 400

    secret   = os.environ.get('RAZORPAY_KEY_SECRET', '')
    msg      = f"{rz_order_id}|{rz_payment_id}".encode()
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, rz_signature):
        return jsonify({'error': 'Payment signature verification failed.'}), 400

    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET status = 'paid', payment_id = ?, payment_method = 'razorpay' WHERE id = ?",
            (rz_payment_id, order['id'])
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'order_id': order['id']})


@payment.route('/order/<int:order_id>/success')
@login_required
def order_success(order_id):
    order = get_order_by_id(order_id)
    if not order or int(order['user_id']) != int(current_user.id):
        return jsonify({'error': 'Order not found.'}), 404
    items = get_order_items(order_id)
    return jsonify({'order': dict(order), 'items': [dict(i) for i in items]})
