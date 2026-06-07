from flask import Blueprint, jsonify, request
from flask_login import current_user

from db import (can_user_review, get_all_avg_ratings, get_average_rating,
                get_product_by_id, get_product_reviews, get_user_review,
                is_in_wishlist, search_products)

catalog = Blueprint('catalog', __name__, url_prefix='/api')

CATEGORIES = ['Whole Spices', 'Ground Spices', 'Spice Blends', 'Organic']
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

    result  = search_products(q=q, category=category, sort=sort, page=page)
    ratings = get_all_avg_ratings()

    products_data = []
    for p in result['products']:
        pd  = dict(p)
        pid = pd['id']
        pd['avg_rating']   = ratings.get(pid, {}).get('avg')
        pd['review_count'] = ratings.get(pid, {}).get('count', 0)
        if current_user.is_authenticated:
            pd['in_wishlist'] = is_in_wishlist(current_user.id, pid)
        else:
            pd['in_wishlist'] = False
        products_data.append(pd)

    return jsonify({
        'products':    products_data,
        'total':       result['total'],
        'page':        result['page'],
        'total_pages': result['total_pages'],
        'q':           q,
        'category':    category,
        'sort':        sort,
        'categories':  CATEGORIES,
    })


@catalog.route('/products/<int:product_id>')
def product_detail(product_id):
    product = get_product_by_id(product_id)
    if product is None:
        return jsonify({'error': 'Product not found'}), 404

    product_reviews = get_product_reviews(product_id)
    avg_data        = get_average_rating(product_id)
    user_review     = None
    can_review      = False
    in_wishlist     = False

    if current_user.is_authenticated:
        user_review = get_user_review(current_user.id, product_id)
        can_review  = can_user_review(current_user.id, product_id)
        in_wishlist = is_in_wishlist(current_user.id, product_id)

    reviews_data = [dict(r) for r in product_reviews]

    return jsonify({
        'product':      dict(product),
        'reviews':      reviews_data,
        'avg_rating':   avg_data['avg'],
        'review_count': avg_data['count'],
        'user_review':  dict(user_review) if user_review else None,
        'can_review':   can_review,
        'in_wishlist':  in_wishlist,
        'categories':   CATEGORIES,
    })


@catalog.app_errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Not found'}), 404
