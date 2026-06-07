from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from db import can_user_review, get_db, get_review_by_id, get_user_review

reviews = Blueprint('reviews', __name__, url_prefix='/api')


@reviews.route('/products/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get('rating', 0))
    except ValueError:
        rating = 0

    if not (1 <= rating <= 5):
        return jsonify({'error': 'Please select a rating between 1 and 5.'}), 400

    if get_user_review(current_user.id, product_id):
        return jsonify({'error': 'You have already reviewed this product.'}), 409

    if not can_user_review(current_user.id, product_id):
        return jsonify({'error': 'Only verified buyers can review this product.'}), 403

    comment = data.get('comment', '').strip() or None
    conn    = get_db()
    try:
        conn.execute(
            "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
            (product_id, current_user.id, rating, comment)
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Review submitted. Thank you!'})


@reviews.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != int(current_user.id):
        return jsonify({'error': 'Review not found or access denied.'}), 403

    data = request.get_json(silent=True) or {}
    try:
        rating = int(data.get('rating', 0))
    except ValueError:
        rating = 0

    if not (1 <= rating <= 5):
        return jsonify({'error': 'Please select a rating between 1 and 5.'}), 400

    comment = data.get('comment', '').strip() or None
    conn    = get_db()
    try:
        conn.execute(
            "UPDATE reviews SET rating = ?, comment = ? WHERE id = ?",
            (rating, comment, review_id)
        )
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Review updated.'})


@reviews.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != int(current_user.id):
        return jsonify({'error': 'Review not found or access denied.'}), 403

    product_id = review['product_id']
    conn       = get_db()
    try:
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True, 'message': 'Review deleted.', 'product_id': product_id})
