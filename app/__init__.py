from flask import Flask
from flask_login import LoginManager
from app.models import User

login_manager = LoginManager()
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    import sqlite3
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, password FROM users WHERE id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return User(id=row[0], username=row[1], email=row[2], password=row[3])
    return None

def create_app():
    app = Flask(__name__)
    app.secret_key = 'your_super_secret_key'

    login_manager.init_app(app)

    from app.routes import main
    app.register_blueprint(main)

    from app.auth import auth
    app.register_blueprint(auth)

    return app

