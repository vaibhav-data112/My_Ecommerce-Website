import os

from flask import Blueprint, abort, jsonify, request
from flask_login import current_user, login_required
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from db import (
    add_address, change_password, clear_avatar, delete_address, get_address_by_id,
    get_addresses, get_user_by_id, set_default_address,
    update_address, update_notify_pref, update_profile,
    get_wishlist_count
)
from orders import get_user_orders

account = Blueprint('account', __name__, url_prefix='/api/account')

AVATAR_UPLOAD_DIR = os.path.join('static', 'uploads', 'avatars')
ALLOWED_EXT       = {'jpg', 'jpeg', 'png', 'webp'}
MAX_AVATAR_SIZE   = 5 * 1024 * 1024


def _allowed_avatar(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXT


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@account.route('/', strict_slashes=False)
@login_required
def dashboard():
    uid    = int(current_user.id)
    user   = get_user_by_id(uid)
    ords   = get_user_orders(uid)
    wcount = get_wishlist_count(uid)
    u      = dict(user)
    u.pop('password_hash', None)
    return jsonify({
        'user':           u,
        'order_count':    len(ords),
        'wishlist_count': wcount,
    })


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

@account.route('/profile')
@login_required
def profile():
    uid  = int(current_user.id)
    user = get_user_by_id(uid)
    u    = dict(user)
    u.pop('password_hash', None)
    return jsonify({'user': u})


@account.route('/profile', methods=['POST'])
@login_required
def update_profile_route():
    uid  = int(current_user.id)
    user = get_user_by_id(uid)
    name  = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()

    if not name:
        return jsonify({'error': 'Name cannot be empty.'}), 400

    avatar_path = None
    file = request.files.get('avatar')
    if file and file.filename:
        if not _allowed_avatar(file.filename):
            return jsonify({'error': 'Only JPG, PNG, or WEBP files are allowed.'}), 400
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        if size > MAX_AVATAR_SIZE:
            return jsonify({'error': 'Photo must be under 5 MB.'}), 400
        os.makedirs(AVATAR_UPLOAD_DIR, exist_ok=True)
        filename    = f"{uid}_{secure_filename(file.filename)}"
        file.save(os.path.join(AVATAR_UPLOAD_DIR, filename))
        avatar_path = f"uploads/avatars/{filename}"

    update_profile(uid, name, phone, avatar_path)
    updated = get_user_by_id(uid)
    u       = dict(updated)
    u.pop('password_hash', None)
    return jsonify({'success': True, 'message': 'Profile updated successfully!', 'user': u})


@account.route('/profile/delete-avatar', methods=['POST'])
@login_required
def delete_avatar():
    uid  = int(current_user.id)
    user = get_user_by_id(uid)
    if user and user['avatar']:
        disk_path = os.path.join('static', user['avatar'])
        if os.path.exists(disk_path):
            os.remove(disk_path)
    clear_avatar(uid)
    return jsonify({'success': True, 'message': 'Profile photo removed.'})


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------

@account.route('/addresses')
@login_required
def addresses():
    uid   = int(current_user.id)
    addrs = get_addresses(uid)
    return jsonify({'addresses': [dict(a) for a in addrs]})


@account.route('/addresses/new', methods=['POST'])
@login_required
def add_address_route():
    uid  = int(current_user.id)
    data = request.get_json(silent=True) or {}

    full_name    = data.get('full_name', '').strip()
    phone        = data.get('phone', '').strip()
    address_line = data.get('address_line', '').strip()
    city         = data.get('city', '').strip()
    state        = data.get('state', '').strip()
    pincode      = data.get('pincode', '').strip()

    if not all([full_name, phone, address_line, city, state, pincode]):
        return jsonify({'error': 'All address fields are required.'}), 400

    add_address(uid, full_name, phone, address_line, city, state, pincode)
    addrs = get_addresses(uid)
    return jsonify({'success': True, 'addresses': [dict(a) for a in addrs]}), 201


@account.route('/addresses/<int:addr_id>', methods=['PUT'])
@login_required
def edit_address(addr_id):
    uid  = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        return jsonify({'error': 'Forbidden'}), 403

    data         = request.get_json(silent=True) or {}
    full_name    = data.get('full_name', '').strip()
    phone        = data.get('phone', '').strip()
    address_line = data.get('address_line', '').strip()
    city         = data.get('city', '').strip()
    state        = data.get('state', '').strip()
    pincode      = data.get('pincode', '').strip()

    if not all([full_name, phone, address_line, city, state, pincode]):
        return jsonify({'error': 'All address fields are required.'}), 400

    update_address(addr_id, full_name, phone, address_line, city, state, pincode)
    return jsonify({'success': True, 'message': 'Address updated successfully!'})


@account.route('/addresses/<int:addr_id>/delete', methods=['POST'])
@login_required
def delete_address_route(addr_id):
    uid  = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        return jsonify({'error': 'Forbidden'}), 403
    delete_address(uid, addr_id)
    return jsonify({'success': True, 'message': 'Address removed.'})


@account.route('/addresses/<int:addr_id>/default', methods=['POST'])
@login_required
def set_default_route(addr_id):
    uid  = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        return jsonify({'error': 'Forbidden'}), 403
    set_default_address(uid, addr_id)
    return jsonify({'success': True, 'message': 'Default address updated.'})


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------

@account.route('/settings', methods=['GET'])
@login_required
def settings():
    uid            = int(current_user.id)
    user           = get_user_by_id(uid)
    is_google_only = not user['password_hash']
    u              = dict(user)
    u.pop('password_hash', None)
    return jsonify({'user': u, 'is_google_only': is_google_only})


@account.route('/settings/password', methods=['POST'])
@login_required
def change_password_route():
    uid            = int(current_user.id)
    user           = get_user_by_id(uid)
    is_google_only = not user['password_hash']

    if is_google_only:
        return jsonify({'error': 'Password change not available for Google accounts.'}), 400

    data       = request.get_json(silent=True) or {}
    current_pw = data.get('current_password', '')
    new_pw     = data.get('new_password', '')
    confirm_pw = data.get('confirm_password', '')

    if not check_password_hash(user['password_hash'], current_pw):
        return jsonify({'error': 'Current password is incorrect.'}), 400
    if len(new_pw) < 8:
        return jsonify({'error': 'New password must be at least 8 characters.'}), 400
    if new_pw != confirm_pw:
        return jsonify({'error': 'New passwords do not match.'}), 400

    change_password(uid, generate_password_hash(new_pw))
    return jsonify({'success': True, 'message': 'Password changed successfully!'})


@account.route('/settings/notifications', methods=['POST'])
@login_required
def update_notifications():
    uid    = int(current_user.id)
    data   = request.get_json(silent=True) or {}
    notify = bool(data.get('notify_email', True))
    update_notify_pref(uid, notify)
    return jsonify({'success': True, 'message': 'Notification preferences saved.'})
