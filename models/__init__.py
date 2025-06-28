from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .company import Company
from .user import User
from .product import Product
from .sale import Sale
from .login_log import LoginLog
from .payroll import PayrollRecord
from .bank_account import BankAccount
from .transaction import Transaction  # <-- Add