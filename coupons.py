import re
from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import login_required

from db import SHIPPING_FEE, get_db
from utils import admin_required

coupons_bp = Blueprint('coupons', __name__, url_prefix='/api')

_CODE_RE = re.compile(r'^[A-Z0-9\-]{3,20}$')


def _validate_coupon_code(code, subtotal):
    conn = get_db()
    try:
        coupon = conn.execute(
            "SELECT * FROM coupons WHERE code = ?", (code,)
        ).fetchone()
    finally:
        conn.close()

    if not coupon:
        return None, "Invalid coupon code."
    if not coupon['is_active']:
        return None, "This coupon is no longer active."
    if coupon['expiry_date']:
        try:
            expiry = datetime.strptime(coupon['expiry_date'], '%Y-%m-%d').date()
            if expiry < datetime.now(timezone.utc).date():
                return None, "This coupon has expired."
        except ValueError:
            return None, "This coupon has expired."
    if coupon['max_uses'] > 0 and coupon['used_count'] >= coupon['max_uses']:
        return None, "This coupon has reached its usage limit."
    if subtotal < coupon['min_order_amount']:
        return None, f"Minimum order of ₹{coupon['min_order_amount']:.0f} required for this coupon."

    return coupon, None


def _compute_discount(coupon, subtotal):
    if coupon['discount_type'] == 'percentage':
        discount = round(subtotal * coupon['discount_value'] / 100, 2)
    else:
        discount = coupon['discount_value']
    return min(round(discount, 2), subtotal)


# ---------------------------------------------------------------------------
# Customer endpoint
# ---------------------------------------------------------------------------

@coupons_bp.route('/coupons/validate', methods=['POST'])
@login_required
def validate_coupon():
    data     = request.get_json(silent=True) or {}
    raw_code = data.get('code', '')
    subtotal = data.get('subtotal', 0)

    code = raw_code.strip().upper()
    if not code:
        return jsonify({'valid': False, 'error': 'Coupon code is required.'}), 200

    try:
        subtotal = float(subtotal)
    except (TypeError, ValueError):
        return jsonify({'valid': False, 'error': 'Invalid subtotal.'}), 200

    coupon, err = _validate_coupon_code(code, subtotal)
    if err:
        return jsonify({'valid': False, 'error': err}), 200

    discount_amount   = _compute_discount(coupon, subtotal)
    new_subtotal      = round(subtotal - discount_amount, 2)
    new_shipping_fee  = 0.0 if new_subtotal >= 500 else SHIPPING_FEE
    new_total         = round(new_subtotal + new_shipping_fee, 2)

    return jsonify({
        'valid':            True,
        'discount_type':    coupon['discount_type'],
        'discount_value':   coupon['discount_value'],
        'discount_amount':  discount_amount,
        'new_subtotal':     new_subtotal,
        'new_shipping_fee': new_shipping_fee,
        'new_total':        new_total,
        'message':          f"Coupon applied! You save ₹{discount_amount:.0f}.",
    }), 200


# ---------------------------------------------------------------------------
# Admin endpoints
# ---------------------------------------------------------------------------

@coupons_bp.route('/admin/coupons', methods=['GET'])
@admin_required
def list_coupons():
    conn = get_db()
    try:
        rows = conn.execute(
            "SELECT * FROM coupons ORDER BY created_at DESC"
        ).fetchall()
    finally:
        conn.close()
    return jsonify({'coupons': [dict(r) for r in rows]})


@coupons_bp.route('/admin/coupons', methods=['POST'])
@admin_required
def create_coupon():
    data = request.get_json(silent=True) or {}

    code               = data.get('code', '').strip().upper()
    discount_type      = data.get('discount_type', '').strip()
    discount_value_raw = data.get('discount_value')
    min_order_raw      = data.get('min_order_amount', 0)
    max_uses_raw       = data.get('max_uses', 0)
    expiry_date        = (data.get('expiry_date') or '').strip() or None

    if not code:
        return jsonify({'error': 'Coupon code is required.'}), 400
    if not _CODE_RE.match(code):
        return jsonify({'error': 'Code must be 3-20 characters: letters, numbers, hyphens only.'}), 400
    if discount_type not in ('percentage', 'fixed'):
        return jsonify({'error': 'discount_type must be "percentage" or "fixed".'}), 400

    try:
        discount_value = float(discount_value_raw)
        if discount_value <= 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'discount_value must be a positive number.'}), 400
    if discount_type == 'percentage' and discount_value > 100:
        return jsonify({'error': 'Percentage discount cannot exceed 100.'}), 400

    try:
        min_order_amount = float(min_order_raw)
        if min_order_amount < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'min_order_amount must be 0 or greater.'}), 400

    try:
        max_uses = int(max_uses_raw)
        if max_uses < 0:
            raise ValueError
    except (TypeError, ValueError):
        return jsonify({'error': 'max_uses must be 0 or greater (0 = unlimited).'}), 400

    if expiry_date:
        try:
            expiry_parsed = datetime.strptime(expiry_date, '%Y-%m-%d').date()
            if expiry_parsed <= datetime.now(timezone.utc).date():
                return jsonify({'error': 'expiry_date must be a future date.'}), 400
        except ValueError:
            return jsonify({'error': 'expiry_date must be in YYYY-MM-DD format.'}), 400

    conn = get_db()
    try:
        conn.execute("""
            INSERT INTO coupons
              (code, discount_type, discount_value, min_order_amount, max_uses, expiry_date)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (code, discount_type, discount_value, min_order_amount, max_uses, expiry_date))
        conn.commit()
    except Exception as e:
        if 'UNIQUE' in str(e).upper():
            return jsonify({'error': f'Coupon code "{code}" already exists.'}), 409
        return jsonify({'error': 'Could not create coupon.'}), 500
    finally:
        conn.close()

    return jsonify({'success': True, 'message': f'Coupon "{code}" created.'}), 201


@coupons_bp.route('/admin/coupons/<int:coupon_id>/toggle', methods=['PATCH'])
@admin_required
def toggle_coupon(coupon_id):
    conn = get_db()
    try:
        coupon = conn.execute(
            "SELECT * FROM coupons WHERE id = ?", (coupon_id,)
        ).fetchone()
        if not coupon:
            return jsonify({'error': 'Coupon not found.'}), 404
        new_state = 0 if coupon['is_active'] else 1
        conn.execute(
            "UPDATE coupons SET is_active = ? WHERE id = ?",
            (new_state, coupon_id)
        )
        conn.commit()
        updated = conn.execute(
            "SELECT * FROM coupons WHERE id = ?", (coupon_id,)
        ).fetchone()
    finally:
        conn.close()
    return jsonify({'success': True, 'coupon': dict(updated)})
