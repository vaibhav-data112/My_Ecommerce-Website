import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, render_template, url_for
from flask_login import current_user

from account import account as account_blueprint
from admin import admin as admin_blueprint
from auth import auth, init_google_oauth, init_login_manager
from cart import cart
from catalog import catalog
from checkout import checkout
from db import (get_all_avg_ratings, get_all_products, get_cart_count,
                get_user_wishlist, get_wishlist_count, init_db, migrate_db, seed_db)
from orders import orders
from payment import payment
from reviews import reviews
from wishlist import wishlist

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

init_db()
migrate_db()
seed_db()
os.makedirs(os.path.join('static', 'uploads', 'products'), exist_ok=True)
os.makedirs(os.path.join('static', 'uploads', 'avatars'), exist_ok=True)

init_login_manager(app)

oauth = OAuth(app)
app.oauth = oauth
init_google_oauth(oauth)

app.register_blueprint(account_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(auth)
app.register_blueprint(cart)
app.register_blueprint(catalog)
app.register_blueprint(checkout)
app.register_blueprint(orders)
app.register_blueprint(payment)
app.register_blueprint(reviews)
app.register_blueprint(wishlist)


@app.context_processor
def inject_cart_count():
    count = get_cart_count(int(current_user.id)) if current_user.is_authenticated else 0
    return dict(cart_count=count)


@app.context_processor
def inject_wishlist_data():
    if current_user.is_authenticated:
        uid = int(current_user.id)
        wishlist_count = get_wishlist_count(uid)
        wishlist_ids = {item['id'] for item in get_user_wishlist(uid)}
    else:
        wishlist_count = 0
        wishlist_ids = set()
    return dict(wishlist_count=wishlist_count, wishlist_ids=wishlist_ids)


@app.route('/')
def index():
    products = get_all_products()[:8]
    ratings = get_all_avg_ratings()
    return render_template('index.html', products=products, ratings=ratings)


if __name__ == '__main__':
    app.run(debug=True)
