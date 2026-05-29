import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for
from flask_login import current_user

from auth import auth, init_google_oauth, init_login_manager
from cart import cart
from catalog import catalog
from checkout import checkout
from db import get_cart_count, init_db, migrate_db, seed_db
from payment import payment

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-change-in-production')

init_db()
migrate_db()
seed_db()

init_login_manager(app)

oauth = OAuth(app)
app.oauth = oauth
init_google_oauth(oauth)

app.register_blueprint(auth)
app.register_blueprint(cart)
app.register_blueprint(catalog)
app.register_blueprint(checkout)
app.register_blueprint(payment)


@app.context_processor
def inject_cart_count():
    count = get_cart_count(int(current_user.id)) if current_user.is_authenticated else 0
    return dict(cart_count=count)


@app.route('/')
def index():
    return redirect(url_for('catalog.product_list'))


if __name__ == '__main__':
    app.run(debug=True)
