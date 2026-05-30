from flask import Blueprint, flash, redirect, request, url_for
from flask_login import current_user, login_required

from db import can_user_review, get_db, get_review_by_id, get_user_review

reviews = Blueprint('reviews', __name__)


@reviews.route('/products/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    try:
        rating = int(request.form.get('rating', 0))
    except ValueError:
        rating = 0
    if not (1 <= rating <= 5):
        flash('Please select a rating between 1 and 5.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=product_id))

    existing = get_user_review(current_user.id, product_id)
    if existing:
        flash('You have already reviewed this product.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=product_id))

    if not can_user_review(current_user.id, product_id):
        flash('Only verified buyers can review this product.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=product_id))

    comment = request.form.get('comment', '').strip() or None
    conn = get_db()
    try:
        conn.execute(
            "INSERT INTO reviews (product_id, user_id, rating, comment) VALUES (?, ?, ?, ?)",
            (product_id, current_user.id, rating, comment)
        )
        conn.commit()
    finally:
        conn.close()
    flash('Review submitted. Thank you!', 'success')
    return redirect(url_for('catalog.product_detail', product_id=product_id))


@reviews.route('/reviews/<int:review_id>/edit', methods=['POST'])
@login_required
def edit_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != int(current_user.id):
        flash('Review not found or access denied.', 'error')
        return redirect(url_for('catalog.product_list'))
    try:
        rating = int(request.form.get('rating', 0))
    except ValueError:
        rating = 0
    if not (1 <= rating <= 5):
        flash('Please select a rating between 1 and 5.', 'error')
        return redirect(url_for('catalog.product_detail', product_id=review['product_id']))
    comment = request.form.get('comment', '').strip() or None
    conn = get_db()
    try:
        conn.execute(
            "UPDATE reviews SET rating = ?, comment = ? WHERE id = ?",
            (rating, comment, review_id)
        )
        conn.commit()
    finally:
        conn.close()
    flash('Review updated.', 'success')
    return redirect(url_for('catalog.product_detail', product_id=review['product_id']))


@reviews.route('/reviews/<int:review_id>/delete', methods=['POST'])
@login_required
def delete_review(review_id):
    review = get_review_by_id(review_id)
    if review is None or review['user_id'] != int(current_user.id):
        flash('Review not found or access denied.', 'error')
        return redirect(url_for('catalog.product_list'))
    product_id = review['product_id']
    conn = get_db()
    try:
        conn.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
        conn.commit()
    finally:
        conn.close()
    flash('Review deleted.', 'success')
    return redirect(url_for('catalog.product_detail', product_id=product_id))
