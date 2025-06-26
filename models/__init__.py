from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after initializing `db` to avoid circular imports
from .user import User
from .product import Product
from .sale import Sale
from .login_log import LoginLog
from .payroll import PayrollRecord  # ✅ Safe now since db is defined above
