from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from models import db

class User(db.Model, UserMixin):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)

    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(30), default='attendant')  # Default user role
    created_by = db.Column(db.String(80), nullable=True)

    reset_token = db.Column(db.String(128), nullable=True)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)

    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)
    company = db.relationship('Company', back_populates='users')

    # ---------- Password Handling ----------
    @property
    def password(self):
        raise AttributeError("❌ Direct access to password is not allowed.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    # ---------- Email Confirmation ----------
    def confirm_email(self):
        self.email_confirmed = True
        self.email_confirmed_on = datetime.utcnow()

    # ---------- Flask-Login Requirement ----------
    def get_id(self):
        return str(self.id)

    # ---------- Role Checks ----------
    def is_super_admin(self): return self.role == 'super_admin'
    def is_admin(self): return self.role == 'admin'
    def is_manager(self): return self.role == 'manager'
    def is_hr(self): return self.role == 'hr'
    def is_supervisor(self): return self.role == 'supervisor'
    def is_attendant(self): return self.role == 'attendant'
    def is_sales(self): return self.role == 'sales'
    def is_finance(self): return self.role == 'finance'
    def is_support(self): return self.role == 'support'
    def is_it(self): return self.role == 'it'

    def has_any_role(self, *roles):
        return self.role in roles

    # ---------- Debugging & Display ----------
    def __repr__(self):
        return f"<User {self.username} ({self.role}) - Confirmed: {self.email_confirmed}>"

    def __str__(self):
        return self.username

    # ---------- Token Generators ----------
    def generate_token(self, purpose='reset', expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], salt=f'{purpose}-salt')
        return s.dumps({'user_id': self.id})

    @staticmethod
    def verify_token(token, purpose='reset', expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], salt=f'{purpose}-salt')
        try:
            data = s.loads(token, max_age=expires_sec)
        except Exception:
            return None
        return User.query.get(data.get('user_id'))

    def generate_confirmation_token(self, expires_sec=86400):
        s = Serializer(current_app.config['SECRET_KEY'], salt='confirm-email-salt')
        return s.dumps({'user_id': self.id})

    @staticmethod
    def confirm_token(token, expires_sec=86400):
        s = Serializer(current_app.config['SECRET_KEY'], salt='confirm-email-salt')
        try:
            data = s.loads(token, max_age=expires_sec)
        except Exception:
            return None
        return User.query.get(data.get('user_id'))
