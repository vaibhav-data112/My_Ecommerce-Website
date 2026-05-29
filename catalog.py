from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from db import get_all_products, get_product_by_id, search_products

catalog = Blueprint('catalog', __name__)

CATEGORIES = ['Electronics', 'Clothing', 'Home', 'Books', 'Beauty', 'Sports', 'Other']
VALID_SORTS = {'price_asc', 'price_desc', 'newest'}


@catalog.route('/products')
def product_list():
    q        = request.args.get('q', '').strip()
    category = request.args.get('category', '')
    sort     = request.args.get('sort', 'newest')
    try:
        page = int(request.args.get('page', 1))
    except (ValueError, TypeError):
        page = 1

    if sort not in VALID_SORTS:
        sort = 'newest'
    if category not in CATEGORIES:
        category = ''

    result = search_products(q=q, category=category, sort=sort, page=page)
    return render_template('products/list.html',
        products=result['products'],
        total=result['total'],
        page=result['page'],
        total_pages=result['total_pages'],
        q=q, category=category, sort=sort,
        categories=CATEGORIES,
    )


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
