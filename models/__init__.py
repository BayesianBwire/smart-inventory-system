from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models after initializing `db` to avoid circular imports
from .company import Company            # ✅ Must come before User
from .user import User
from .product import Product
from .sale import Sale
from .login_log import LoginLog
from .payroll import PayrollRecord
