from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from db import calculate_totals, get_cart_items, place_order

checkout = Blueprint('checkout', __name__)


@checkout.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout_page():
    user_id = int(current_user.id)

    if request.method == 'POST':
        shipping_name    = request.form.get('shipping_name', '').strip()
        shipping_phone   = request.form.get('shipping_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()

        errors = {}
        if not shipping_name:
            errors['shipping_name'] = 'Full name is required.'
        if not shipping_phone or not shipping_phone.replace('+', '').replace(' ', '').isdigit() \
                or len(shipping_phone.replace('+', '').replace(' ', '')) < 10:
            errors['shipping_phone'] = 'A valid phone number (at least 10 digits) is required.'
        if not shipping_address:
            errors['shipping_address'] = 'Shipping address is required.'

        if errors:
            items = get_cart_items(user_id)
            totals = calculate_totals(items) if items else {'subtotal': 0, 'shipping_fee': 0, 'total': 0}
            return render_template(
                'checkout/checkout.html',
                items=items, errors=errors,
                form=request.form,
                **totals
            )

        ok, message, order_id = place_order(user_id, shipping_name, shipping_phone, shipping_address)
        if not ok:
            flash(message, 'error')
            return redirect(url_for('checkout.checkout_page'))

        return redirect(url_for('checkout.checkout_page') if order_id is None
                        else f'/payment/{order_id}')

    items = get_cart_items(user_id)
    if not items:
        flash('Your cart is empty.', 'error')
        return redirect(url_for('cart.view_cart'))

    totals = calculate_totals(items)
    return render_template('checkout/checkout.html', items=items, errors={}, form={}, **totals)
