# app/models.py

from flask_login import UserMixin
import sqlite3

# User model (used by flask-login)
class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password

