from flask import Blueprint, render_template
from flask_login import current_user, login_required

from db import get_db, get_order_by_id, get_order_items

orders = Blueprint('orders', __name__)


def get_user_orders(user_id):
    conn = get_db()
    try:
        return conn.execute(
            "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
    finally:
        conn.close()


def get_order_detail(order_id, user_id):
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != user_id:
        return None, None
    items = get_order_items(order_id)
    return order, items


@orders.route('/orders')
@login_required
def order_history():
    user_orders = get_user_orders(int(current_user.id))
    return render_template('orders/list.html', orders=user_orders)


@orders.route('/orders/<int:order_id>')
@login_required
def order_detail(order_id):
    order, items = get_order_detail(order_id, int(current_user.id))
    if order is None:
        return render_template('orders/not_found.html'), 404
    return render_template('orders/detail.html', order=order, items=items)
