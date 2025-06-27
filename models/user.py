from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from itsdangerous import URLSafeTimedSerializer as Serializer
from flask import current_app
from models import db  # ✅ Use the existing SQLAlchemy instance

class User(db.Model, UserMixin):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)

    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(30), default='attendant')  # Increased length for safety
    created_by = db.Column(db.String(80), nullable=True)

    reset_token = db.Column(db.String(128), nullable=True)
    email_confirmed = db.Column(db.Boolean, default=False)
    email_confirmed_on = db.Column(db.DateTime, nullable=True)

    # ✅ Fixed: company relationship with correct table name
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('models.company.Company', backref=db.backref('users', lazy=True))

    # Password management
    @property
    def password(self):
        raise AttributeError("❌ Direct password access is not allowed.")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def confirm_email(self):
        self.email_confirmed = True
        self.email_confirmed_on = datetime.utcnow()

    # Role helpers
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

    def get_id(self):
        return str(self.id)

    def __repr__(self):
        return f"<User {self.username} ({self.role}) - Confirmed: {self.email_confirmed}>"

    # 🔐 Token generation (for reset/verify links)
    def generate_token(self, purpose='reset', expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], salt=f'{purpose}-salt')
        return s.dumps({'user_id': self.id})

    # 🔐 Token verification
    @staticmethod
    def verify_token(token, purpose='reset', expires_sec=3600):
        s = Serializer(current_app.config['SECRET_KEY'], salt=f'{purpose}-salt')
        try:
            data = s.loads(token, max_age=expires_sec)
        except Exception:
            return None
        return User.query.get(data.get('user_id'))
