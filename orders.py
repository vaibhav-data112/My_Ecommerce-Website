from flask import Blueprint, jsonify
from flask_login import current_user, login_required

from db import get_db, get_order_by_id, get_order_items

orders = Blueprint('orders', __name__, url_prefix='/api')


def get_user_orders(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()


@orders.route('/orders')
@login_required
def order_history():
    user_orders = get_user_orders(int(current_user.id))
    return jsonify({'orders': [dict(o) for o in user_orders]})


@orders.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != int(current_user.id):
        return jsonify({'error': 'Order not found.'}), 404
    items = get_order_items(order_id)
    return jsonify({'order': dict(order), 'items': [dict(i) for i in items]})
