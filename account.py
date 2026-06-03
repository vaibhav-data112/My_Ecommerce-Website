import os

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, url_for
)
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

account = Blueprint('account', __name__, url_prefix='/account')

AVATAR_UPLOAD_DIR = os.path.join('static', 'uploads', 'avatars')
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'webp'}
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5 MB


def _allowed_avatar(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ---------------------------------------------------------------------------
# Dashboard
# ---------------------------------------------------------------------------

@account.route('/')
@login_required
def dashboard():
    uid = int(current_user.id)
    user = get_user_by_id(uid)
    orders = get_user_orders(uid)
    wcount = get_wishlist_count(uid)
    return render_template(
        'account/dashboard.html',
        active='dashboard',
        user=user,
        order_count=len(orders),
        wishlist_count_acct=wcount,
    )


# ---------------------------------------------------------------------------
# Profile edit
# ---------------------------------------------------------------------------

@account.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    uid = int(current_user.id)
    user = get_user_by_id(uid)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()

        if not name:
            flash('Name cannot be empty.', 'error')
            return render_template('account/profile.html', active='dashboard', user=user)

        avatar_path = None
        file = request.files.get('avatar')
        if file and file.filename:
            if not _allowed_avatar(file.filename):
                flash('Only JPG, PNG, or WEBP files are allowed.', 'error')
                return render_template('account/profile.html', active='dashboard', user=user)
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > MAX_AVATAR_SIZE:
                flash('Photo must be under 5 MB.', 'error')
                return render_template('account/profile.html', active='dashboard', user=user)
            filename = f"{uid}_{secure_filename(file.filename)}"
            file.save(os.path.join(AVATAR_UPLOAD_DIR, filename))
            avatar_path = f"uploads/avatars/{filename}"

        update_profile(uid, name, phone, avatar_path)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('account.profile'))

    return render_template('account/profile.html', active='dashboard', user=user)


@account.route('/profile/delete-avatar', methods=['POST'])
@login_required
def delete_avatar():
    uid = int(current_user.id)
    user = get_user_by_id(uid)
    if user and user['avatar']:
        disk_path = os.path.join('static', user['avatar'])
        if os.path.exists(disk_path):
            os.remove(disk_path)
    clear_avatar(uid)
    flash('Profile photo removed.', 'success')
    return redirect(url_for('account.profile'))


# ---------------------------------------------------------------------------
# Addresses
# ---------------------------------------------------------------------------

@account.route('/addresses')
@login_required
def addresses():
    uid = int(current_user.id)
    addrs = get_addresses(uid)
    return render_template('account/addresses.html', active='addresses', addresses=addrs)


@account.route('/addresses/new', methods=['POST'])
@login_required
def add_address_route():
    uid = int(current_user.id)
    full_name    = request.form.get('full_name', '').strip()
    phone        = request.form.get('phone', '').strip()
    address_line = request.form.get('address_line', '').strip()
    city         = request.form.get('city', '').strip()
    state        = request.form.get('state', '').strip()
    pincode      = request.form.get('pincode', '').strip()

    if not all([full_name, phone, address_line, city, state, pincode]):
        flash('All address fields are required.', 'error')
        return redirect(url_for('account.addresses'))

    add_address(uid, full_name, phone, address_line, city, state, pincode)
    flash('Address added successfully!', 'success')
    return redirect(url_for('account.addresses'))


@account.route('/addresses/<int:addr_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_address(addr_id):
    uid = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        abort(403)

    if request.method == 'POST':
        full_name    = request.form.get('full_name', '').strip()
        phone        = request.form.get('phone', '').strip()
        address_line = request.form.get('address_line', '').strip()
        city         = request.form.get('city', '').strip()
        state        = request.form.get('state', '').strip()
        pincode      = request.form.get('pincode', '').strip()

        if not all([full_name, phone, address_line, city, state, pincode]):
            flash('All address fields are required.', 'error')
            return render_template('account/edit_address.html', active='addresses', addr=addr)

        update_address(addr_id, full_name, phone, address_line, city, state, pincode)
        flash('Address updated successfully!', 'success')
        return redirect(url_for('account.addresses'))

    return render_template('account/edit_address.html', active='addresses', addr=addr)


@account.route('/addresses/<int:addr_id>/delete', methods=['POST'])
@login_required
def delete_address_route(addr_id):
    uid = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        abort(403)
    delete_address(uid, addr_id)
    flash('Address removed.', 'success')
    return redirect(url_for('account.addresses'))


@account.route('/addresses/<int:addr_id>/default', methods=['POST'])
@login_required
def set_default_route(addr_id):
    uid = int(current_user.id)
    addr = get_address_by_id(addr_id)
    if not addr or int(addr['user_id']) != uid:
        abort(403)
    set_default_address(uid, addr_id)
    flash('Default address updated.', 'success')
    return redirect(url_for('account.addresses'))


# ---------------------------------------------------------------------------
# Settings (password + notifications)
# ---------------------------------------------------------------------------

@account.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    uid = int(current_user.id)
    user = get_user_by_id(uid)
    is_google_only = not user['password_hash']

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'password' and not is_google_only:
            current_pw  = request.form.get('current_password', '')
            new_pw      = request.form.get('new_password', '')
            confirm_pw  = request.form.get('confirm_password', '')

            if not check_password_hash(user['password_hash'], current_pw):
                flash('Current password is incorrect.', 'error')
            elif len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'error')
            elif new_pw != confirm_pw:
                flash('New passwords do not match.', 'error')
            else:
                change_password(uid, generate_password_hash(new_pw))
                flash('Password changed successfully!', 'success')

        elif action == 'notifications':
            notify = bool(request.form.get('notify_email'))
            update_notify_pref(uid, notify)
            flash('Notification preferences saved.', 'success')

        return redirect(url_for('account.settings'))

    return render_template(
        'account/settings.html',
        active='settings',
        user=user,
        is_google_only=is_google_only,
    )
