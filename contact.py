from flask import Blueprint, jsonify, request
from flask_login import current_user

from db import get_db
from utils import admin_required

contact = Blueprint('contact', __name__, url_prefix='/api')

ALLOWED_CATEGORIES = ['Return issue', 'Product issue', 'Order issue', 'Other']


# ---------------------------------------------------------------------------
# Public — submit contact message
# ---------------------------------------------------------------------------

@contact.route('/contact', methods=['POST'])
def submit_contact():
    data = request.get_json(silent=True) or {}

    # Honeypot: bot filled hidden field → silently discard
    if (data.get('website') or '').strip():
        return jsonify({'success': True,
                        'message': 'Your message has been sent!'}), 200

    name         = (data.get('name')         or '').strip()[:100]
    email        = (data.get('email')        or '').strip()[:200]
    order_number = (data.get('order_number') or '').strip()[:50] or None
    category     = (data.get('category')     or '').strip()
    message      = (data.get('message')      or '').strip()[:2000]

    errors = []
    if not name:
        errors.append('Name is required.')
    if not email or '@' not in email or '.' not in email.split('@')[-1]:
        errors.append('Please enter a valid email address.')
    if category not in ALLOWED_CATEGORIES:
        errors.append('Please select a valid category.')
    if not message:
        errors.append('Message is required.')
    if errors:
        return jsonify({'error': ' '.join(errors)}), 400

    user_id = int(current_user.id) if current_user.is_authenticated else None

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO contact_messages
              (user_id, name, email, order_number, category, message)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, name, email, order_number, category, message))
        conn.commit()
    finally:
        conn.close()

    return jsonify({'success': True,
                    'message': 'Message sent! We will get back to you within 24 hours.'})


# ---------------------------------------------------------------------------
# Admin — list messages
# ---------------------------------------------------------------------------

@contact.route('/admin/contacts')
@admin_required
def get_contacts():
    status_filter = (request.args.get('status') or '').strip()
    conn = get_db()
    try:
        if status_filter in ('new', 'resolved'):
            rows = conn.execute(
                "SELECT * FROM contact_messages WHERE status=? ORDER BY created_at DESC",
                (status_filter,)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM contact_messages ORDER BY created_at DESC"
            ).fetchall()
    finally:
        conn.close()
    return jsonify({'messages': [dict(r) for r in rows]})


# ---------------------------------------------------------------------------
# Admin — mark resolved
# ---------------------------------------------------------------------------

@contact.route('/admin/contacts/<int:msg_id>/resolve', methods=['PATCH'])
@admin_required
def resolve_contact(msg_id):
    conn = get_db()
    try:
        row = conn.execute(
            "SELECT id FROM contact_messages WHERE id=?", (msg_id,)
        ).fetchone()
        if not row:
            return jsonify({'error': 'Message not found.'}), 404
        conn.execute(
            "UPDATE contact_messages SET status='resolved' WHERE id=?", (msg_id,)
        )
        conn.commit()
    finally:
        conn.close()
    return jsonify({'success': True,
                    'message': f'Message #{msg_id} marked resolved.'})
