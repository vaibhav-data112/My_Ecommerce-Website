import os

from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import Flask, render_template

from auth import auth, init_google_oauth, init_login_manager
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


@app.route('/')
def index():
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
