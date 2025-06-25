from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from models import db
from flask_login import UserMixin  # ✅ Needed for Flask-Login

class User(db.Model, UserMixin):  # ✅ Inherit from UserMixin
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='attendant')  # 'admin', 'manager', etc.
    created_by = db.Column(db.String(80), nullable=True)
    reset_token = db.Column(db.String(128), nullable=True)

    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)

    @property
    def password(self):
        raise AttributeError("❌ Direct password access not allowed.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def confirm_email(self):
        self.email_confirmed = True
        self.email_confirmed_on = datetime.utcnow()

    def is_admin(self):
        return self.role == 'admin'

    def is_attendant(self):
        return self.role == 'attendant'

    def is_manager(self):
        return self.role == 'manager'

    def get_id(self):  # ✅ Required by Flask-Login
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} ({self.role}) - Confirmed: {self.email_confirmed}>"
