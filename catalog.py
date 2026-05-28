from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from db import get_all_products, get_product_by_id

catalog = Blueprint('catalog', __name__)


@catalog.route('/products')
def product_list():
    products = get_all_products()
    return render_template('products/list.html', products=products)


@catalog.route('/products/<int:product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if product is None:
        abort(404)
    return render_template('products/detail.html', product=product)


@catalog.route('/cart/add', methods=['POST'])
def cart_add_placeholder():
    product_id = request.form.get('product_id', '')
    flash('Shopping cart coming soon!', 'info')
    return redirect(url_for('catalog.product_detail', product_id=product_id))


@catalog.app_errorhandler(404)
def not_found(e):
    return render_template('products/not_found.html'), 404
