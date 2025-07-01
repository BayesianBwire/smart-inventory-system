from extensions import db

from .user import User
from .product import Product
from .sale import Sale
from .login_log import LoginLog
from .company import Company
from .audit_log import AuditLog
from .bank_account import BankAccount  # ✅ Corrected
from .transaction import Transaction
from .employee import Employee
from .attendance import AttendanceRecord
# Also import other models like Employee, User, etc.
from .leave import LeaveRequest
from .payroll import Payroll
from .support_ticket import SupportTicket
