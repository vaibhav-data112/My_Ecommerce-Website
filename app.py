import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
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

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

CORS(app, supports_credentials=True, origins=[
    'http://localhost:5173',
    'http://127.0.0.1:5173',
    'http://localhost:5174',
    'http://127.0.0.1:5174',
])

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


@app.route('/api/')
@app.route('/api')
def api_index():
    products = get_all_products()[:8]
    ratings = get_all_avg_ratings()
    featured = []
    for p in products:
        pd = dict(p)
        pid = pd['id']
        pd['avg_rating'] = ratings.get(pid, {}).get('avg')
        pd['review_count'] = ratings.get(pid, {}).get('count', 0)
        featured.append(pd)
    return jsonify({'featured_products': featured})


REACT_DIST = os.path.join(os.path.dirname(__file__), 'frontend', 'dist')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve_react(path):
    if os.path.exists(REACT_DIST):
        full = os.path.join(REACT_DIST, path)
        if path and os.path.exists(full) and os.path.isfile(full):
            return send_from_directory(REACT_DIST, path)
        return send_from_directory(REACT_DIST, 'index.html')
    return jsonify({'message': 'Run: cd frontend && npm install && npm run build'}), 503


if __name__ == '__main__':
    app.run(debug=True)
