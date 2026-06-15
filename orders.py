from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import can_self_return, get_db, get_order_by_id, get_order_items

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
    import json as _json
    uid   = int(current_user.id)
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != uid:
        return jsonify({'error': 'Order not found.'}), 404
    items      = get_order_items(order_id)
    order_dict = dict(order)
    raw_hist   = order_dict.get('status_history')
    order_dict['status_history']  = _json.loads(raw_hist) if raw_hist else []
    order_dict['can_self_return'] = can_self_return(uid, order_id)[0]
    return jsonify({'order': order_dict, 'items': [dict(i) for i in items]})


@orders.route('/orders/<int:order_id>/return-request', methods=['POST'])
@login_required
def return_request(order_id):
    from datetime import datetime, timezone
    uid   = int(current_user.id)
    order = get_order_by_id(order_id)
    if not order or order['user_id'] != uid:
        return jsonify({'error': 'Order not found.'}), 404

    eligible, err = can_self_return(uid, order_id)
    if not eligible:
        return jsonify({'error': err}), 403

    data   = request.get_json(silent=True) or {}
    reason = (data.get('reason') or '').strip()[:500]
    if not reason:
        return jsonify({'error': 'Please provide a reason for the return.'}), 400

    now  = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%S')
    conn = get_db()
    try:
        conn.execute(
            "UPDATE orders SET return_reason=?, return_requested_at=? WHERE id=?",
            (reason, now, order_id)
        )
        conn.commit()
    finally:
        conn.close()

    from db import append_status_history
    append_status_history(order_id, 'return_requested',
                          note=f"Customer return request: {reason}")
    return jsonify({'success': True,
                    'message': 'Return request submitted. Admin will review shortly.'})
