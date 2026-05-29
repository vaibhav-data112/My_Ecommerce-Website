import hashlib
import hmac
import os

import razorpay
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from db import get_db, get_order_by_id, get_order_items

payment = Blueprint('payment', __name__)


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
        flash('Order not found.', 'error')
        return redirect(url_for('catalog.product_list'))

    if int(order['user_id']) != int(current_user.id):
        abort(403)

    if order['status'] == 'paid':
        return redirect(url_for('payment.order_success', order_id=order_id))

    if order['status'] != 'pending':
        flash('This order cannot be paid.', 'error')
        return redirect(url_for('catalog.product_list'))

    try:
        rz_order = _rz_client().order.create({
            'amount': int(order['total'] * 100),
            'currency': 'INR',
            'receipt': str(order_id),
            'payment_capture': 1
        })
    except Exception:
        flash('Could not connect to the payment gateway. Please try again.', 'error')
        return redirect(url_for('catalog.product_list'))

    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET payment_order_id = ? WHERE id = ?",
            (rz_order['id'], order_id)
        )
        conn.commit()
    finally:
        conn.close()

    return render_template(
        'payment/pay.html',
        order=order,
        rz_order_id=rz_order['id'],
        key_id=os.environ.get('RAZORPAY_KEY_ID', ''),
        amount_paisa=int(order['total'] * 100)
    )


@payment.route('/payment/verify', methods=['POST'])
@login_required
def verify_payment():
    rz_order_id   = request.form.get('razorpay_order_id', '')
    rz_payment_id = request.form.get('razorpay_payment_id', '')
    rz_signature  = request.form.get('razorpay_signature', '')

    conn = get_db()
    try:
        order = conn.execute(
            "SELECT * FROM orders WHERE payment_order_id = ? AND user_id = ?",
            (rz_order_id, int(current_user.id))
        ).fetchone()
    finally:
        conn.close()

    if not order:
        flash('Payment could not be verified.', 'error')
        return redirect(url_for('catalog.product_list'))

    secret = os.environ.get('RAZORPAY_KEY_SECRET', '')
    msg = f"{rz_order_id}|{rz_payment_id}".encode()
    expected = hmac.new(secret.encode(), msg, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, rz_signature):
        flash('Payment verification failed. Your order has not been charged.', 'error')
        return redirect(url_for('payment.pay_page', order_id=order['id']))

    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET status = 'paid', payment_id = ? WHERE id = ?",
            (rz_payment_id, order['id'])
        )
        conn.commit()
    finally:
        conn.close()

    return redirect(url_for('payment.order_success', order_id=order['id']))


@payment.route('/order/<int:order_id>/success')
@login_required
def order_success(order_id):
    order = get_order_by_id(order_id)
    if not order:
        flash('Order not found.', 'error')
        return redirect(url_for('catalog.product_list'))

    if int(order['user_id']) != int(current_user.id):
        abort(403)

    if order['status'] != 'paid':
        return redirect(url_for('payment.pay_page', order_id=order_id))

    items = get_order_items(order_id)
    return render_template('payment/success.html', order=order, items=items)
