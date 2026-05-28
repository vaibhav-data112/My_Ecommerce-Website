from flask import Flask
from db import init_db, seed_db

app = Flask(__name__)

init_db()
seed_db()

if __name__ == '__main__':
    app.run(debug=True)
