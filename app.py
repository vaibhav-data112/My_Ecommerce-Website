import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, url_for

from auth import auth, init_google_oauth, init_login_manager
from catalog import catalog
from db import init_db, migrate_db, seed_db

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
app.register_blueprint(catalog)


@app.route('/')
def index():
    return redirect(url_for('catalog.product_list'))


if __name__ == '__main__':
    app.run(debug=True)
