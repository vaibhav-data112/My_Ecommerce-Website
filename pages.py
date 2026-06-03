from flask import Blueprint, render_template

pages = Blueprint('pages', __name__)


@pages.route('/about')
def about():
    return render_template('pages/about.html')


@pages.route('/contact')
def contact():
    return render_template('pages/contact.html')


@pages.route('/privacy')
def privacy():
    return render_template('pages/privacy.html')


@pages.route('/terms')
def terms():
    return render_template('pages/terms.html')
