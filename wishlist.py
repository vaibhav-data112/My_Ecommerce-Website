from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import (add_to_cart, add_to_wishlist, get_cart_count,
                get_user_wishlist, get_wishlist_count,
                is_in_wishlist, remove_from_wishlist)

wishlist = Blueprint('wishlist', __name__, url_prefix='/api')


@wishlist.route('/wishlist')
@login_required
def view_wishlist():
    uid   = int(current_user.id)
    items = get_user_wishlist(uid)
    return jsonify({
        'items':          [dict(i) for i in items],
        'wishlist_count': get_wishlist_count(uid),
    })


@wishlist.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    data       = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id required'}), 400

    uid = int(current_user.id)
    if is_in_wishlist(uid, product_id):
        remove_from_wishlist(uid, product_id)
        in_wishlist = False
        message     = 'Removed from wishlist.'
    else:
        add_to_wishlist(uid, product_id)
        in_wishlist = True
        message     = 'Added to wishlist!'

    return jsonify({
        'success':        True,
        'in_wishlist':    in_wishlist,
        'message':        message,
        'wishlist_count': get_wishlist_count(uid),
    })


@wishlist.route('/wishlist/add-to-cart', methods=['POST'])
@login_required
def wishlist_add_to_cart():
    data       = request.get_json(silent=True) or {}
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'error': 'product_id required'}), 400

    uid       = int(current_user.id)
    ok, msg   = add_to_cart(uid, product_id, 1)
    cart_count = get_cart_count(uid)
    return jsonify({'success': ok, 'message': msg, 'cart_count': cart_count})
