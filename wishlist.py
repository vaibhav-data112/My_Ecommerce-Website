from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from db import (add_to_cart, add_to_wishlist, get_user_wishlist,
                is_in_wishlist, remove_from_wishlist)

wishlist = Blueprint('wishlist', __name__)


@wishlist.route('/wishlist')
@login_required
def view_wishlist():
    items = get_user_wishlist(int(current_user.id))
    return render_template('wishlist/wishlist.html', items=items)


@wishlist.route('/wishlist/toggle', methods=['POST'])
@login_required
def toggle_wishlist():
    product_id = request.form.get('product_id', type=int)
    next_url = request.form.get('next') or url_for('catalog.product_list')
    if product_id:
        uid = int(current_user.id)
        if is_in_wishlist(uid, product_id):
            remove_from_wishlist(uid, product_id)
            flash('Removed from wishlist.', 'info')
        else:
            add_to_wishlist(uid, product_id)
            flash('Added to wishlist!', 'success')
    return redirect(next_url)


@wishlist.route('/wishlist/add-to-cart', methods=['POST'])
@login_required
def wishlist_add_to_cart():
    product_id = request.form.get('product_id', type=int)
    if product_id:
        ok, msg = add_to_cart(int(current_user.id), product_id, 1)
        flash(msg, 'success' if ok else 'error')
    return redirect(url_for('wishlist.view_wishlist'))
