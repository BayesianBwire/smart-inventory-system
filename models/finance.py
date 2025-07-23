from extensions import db
from datetime import datetime, date
from sqlalchemy import func, and_
from decimal import Decimal
import uuid

class ChartOfAccounts(db.Model):
    """Chart of Accounts for financial tracking"""
    __tablename__ = 'chart_of_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    account_code = db.Column(db.String(20), nullable=False)
    account_name = db.Column(db.String(200), nullable=False)
    account_type = db.Column(db.String(50), nullable=False)  # asset, liability, equity, revenue, expense
    account_category = db.Column(db.String(100), nullable=True)  # current_assets, fixed_assets, etc.
    parent_account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    description = db.Column(db.Text, nullable=True)
    balance = db.Column(db.Numeric(15, 2), default=0.00)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='chart_accounts')
    parent_account = db.relationship('ChartOfAccounts', remote_side=[id], backref='sub_accounts')
    journal_entries = db.relationship('JournalEntry', backref='account', lazy='dynamic')
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'account_code', name='unique_account_code_per_company'),
    )
    
    def __repr__(self):
        return f'<ChartOfAccounts {self.account_code}: {self.account_name}>'
    
    @property
    def full_account_name(self):
        if self.parent_account:
            return f"{self.parent_account.account_name} - {self.account_name}"
        return self.account_name
    
    def get_balance(self, as_of_date=None):
        """Get account balance as of a specific date"""
        query = self.journal_entries
        if as_of_date:
            query = query.filter(JournalEntry.transaction_date <= as_of_date)
        
        total_debits = query.with_entities(func.sum(JournalEntry.debit_amount)).scalar() or 0
        total_credits = query.with_entities(func.sum(JournalEntry.credit_amount)).scalar() or 0
        
        # For asset and expense accounts, balance = debits - credits
        # For liability, equity, and revenue accounts, balance = credits - debits
        if self.account_type in ['asset', 'expense']:
            return total_debits - total_credits
        else:
            return total_credits - total_debits


class Invoice(db.Model):
    """Invoice management for customer billing"""
    __tablename__ = 'invoices'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    opportunity_id = db.Column(db.Integer, db.ForeignKey('opportunities.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Invoice Details
    invoice_number = db.Column(db.String(50), nullable=False, unique=True)
    invoice_date = db.Column(db.Date, nullable=False, default=date.today)
    due_date = db.Column(db.Date, nullable=False)
    
    # Amounts
    subtotal = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    tax_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    discount_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    total_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    paid_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    
    # Status and Terms
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, sent, paid, overdue, cancelled
    payment_terms = db.Column(db.String(50), nullable=False, default='net_30')
    currency = db.Column(db.String(3), nullable=False, default='USD')
    
    # Additional Information
    notes = db.Column(db.Text, nullable=True)
    internal_notes = db.Column(db.Text, nullable=True)
    reference_number = db.Column(db.String(100), nullable=True)
    
    # Billing Information
    billing_name = db.Column(db.String(200), nullable=False)
    billing_email = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.Text, nullable=True)
    billing_city = db.Column(db.String(100), nullable=True)
    billing_state = db.Column(db.String(100), nullable=True)
    billing_country = db.Column(db.String(100), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    
    # Timestamps
    sent_at = db.Column(db.DateTime, nullable=True)
    paid_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='invoices')
    creator = db.relationship('User', backref='created_invoices')
    invoice_items = db.relationship('InvoiceItem', backref='invoice', lazy='dynamic', cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='invoice', lazy='dynamic')
    
    def __repr__(self):
        return f'<Invoice {self.invoice_number}: ${self.total_amount}>'
    
    @property
    def balance_due(self):
        return self.total_amount - self.paid_amount
    
    @property
    def is_overdue(self):
        return self.status != 'paid' and self.due_date < date.today()
    
    @property
    def days_overdue(self):
        if self.is_overdue:
            return (date.today() - self.due_date).days
        return 0
    
    def calculate_totals(self):
        """Calculate invoice totals from line items"""
        items = self.invoice_items.all()
        self.subtotal = sum(item.line_total for item in items)
        self.total_amount = self.subtotal + self.tax_amount - self.discount_amount
        return self.total_amount
    
    def mark_as_sent(self):
        """Mark invoice as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        db.session.commit()
    
    def mark_as_paid(self, payment_amount=None):
        """Mark invoice as paid"""
        if payment_amount:
            self.paid_amount += payment_amount
        
        if self.paid_amount >= self.total_amount:
            self.status = 'paid'
            self.paid_at = datetime.utcnow()
        
        db.session.commit()
    
    def generate_invoice_number(self):
        """Generate unique invoice number"""
        if not self.invoice_number:
            year = datetime.now().year
            month = datetime.now().month
            
            # Get last invoice number for this month
            last_invoice = Invoice.query.filter(
                Invoice.company_id == self.company_id,
                func.extract('year', Invoice.created_at) == year,
                func.extract('month', Invoice.created_at) == month
            ).order_by(Invoice.id.desc()).first()
            
            if last_invoice and last_invoice.invoice_number:
                try:
                    last_num = int(last_invoice.invoice_number.split('-')[-1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            self.invoice_number = f"INV-{year}{month:02d}-{next_num:04d}"


class InvoiceItem(db.Model):
    """Line items for invoices"""
    __tablename__ = 'invoice_items'
    
    id = db.Column(db.Integer, primary_key=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    
    # Item Details
    description = db.Column(db.String(500), nullable=False)
    quantity = db.Column(db.Numeric(10, 2), nullable=False, default=1.00)
    unit_price = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    line_total = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    
    # Additional Information
    item_code = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    product = db.relationship('Product', backref='invoice_items')
    
    def __repr__(self):
        return f'<InvoiceItem {self.description}: {self.quantity} x ${self.unit_price}>'
    
    def calculate_line_total(self):
        """Calculate line total"""
        self.line_total = self.quantity * self.unit_price
        return self.line_total


class Payment(db.Model):
    """Payment tracking for invoices and expenses"""
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expenses.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Payment Details
    payment_number = db.Column(db.String(50), nullable=False, unique=True)
    payment_date = db.Column(db.Date, nullable=False, default=date.today)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    
    # Payment Method and Information
    payment_method = db.Column(db.String(50), nullable=False)  # cash, check, bank_transfer, credit_card, mobile_money
    payment_reference = db.Column(db.String(200), nullable=True)  # check number, transaction ID, etc.
    
    # Bank/Account Information
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=True)
    bank_name = db.Column(db.String(200), nullable=True)
    account_number = db.Column(db.String(100), nullable=True)
    
    # Status and Notes
    status = db.Column(db.String(20), nullable=False, default='completed')  # pending, completed, failed, cancelled
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='payments')
    recorder = db.relationship('User', backref='recorded_payments')
    bank_account = db.relationship('BankAccount', backref='payments')
    
    def __repr__(self):
        return f'<Payment {self.payment_number}: ${self.amount}>'
    
    def generate_payment_number(self):
        """Generate unique payment number"""
        if not self.payment_number:
            year = datetime.now().year
            month = datetime.now().month
            
            # Get last payment number for this month
            last_payment = Payment.query.filter(
                Payment.company_id == self.company_id,
                func.extract('year', Payment.created_at) == year,
                func.extract('month', Payment.created_at) == month
            ).order_by(Payment.id.desc()).first()
            
            if last_payment and last_payment.payment_number:
                try:
                    last_num = int(last_payment.payment_number.split('-')[-1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            self.payment_number = f"PAY-{year}{month:02d}-{next_num:04d}"


class Expense(db.Model):
    """Expense tracking and management"""
    __tablename__ = 'expenses'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('expense_categories.id'), nullable=True)
    recorded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Expense Details
    expense_number = db.Column(db.String(50), nullable=False, unique=True)
    expense_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(500), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='USD')
    
    # Vendor/Supplier Information
    vendor_name = db.Column(db.String(200), nullable=True)
    vendor_contact = db.Column(db.String(255), nullable=True)
    invoice_reference = db.Column(db.String(100), nullable=True)
    
    # Status and Approval
    status = db.Column(db.String(20), nullable=False, default='pending')  # pending, approved, rejected, paid
    approval_notes = db.Column(db.Text, nullable=True)
    
    # Payment Information
    payment_method = db.Column(db.String(50), nullable=True)
    payment_reference = db.Column(db.String(200), nullable=True)
    paid_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    paid_date = db.Column(db.Date, nullable=True)
    
    # Additional Information
    receipt_file = db.Column(db.String(500), nullable=True)  # File path for receipt/invoice
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    
    # Timestamps
    approved_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='expenses')
    category = db.relationship('ExpenseCategory', backref='expenses')
    recorder = db.relationship('User', foreign_keys=[recorded_by], backref='recorded_expenses')
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_expenses')
    payments = db.relationship('Payment', backref='expense', lazy='dynamic')
    
    def __repr__(self):
        return f'<Expense {self.expense_number}: ${self.amount}>'
    
    @property
    def balance_due(self):
        return self.amount - self.paid_amount
    
    @property
    def is_fully_paid(self):
        return self.paid_amount >= self.amount
    
    def approve(self, approver_id, notes=None):
        """Approve the expense"""
        self.status = 'approved'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        if notes:
            self.approval_notes = notes
        db.session.commit()
    
    def reject(self, approver_id, notes=None):
        """Reject the expense"""
        self.status = 'rejected'
        self.approved_by = approver_id
        self.approved_at = datetime.utcnow()
        if notes:
            self.approval_notes = notes
        db.session.commit()
    
    def generate_expense_number(self):
        """Generate unique expense number"""
        if not self.expense_number:
            year = datetime.now().year
            month = datetime.now().month
            
            # Get last expense number for this month
            last_expense = Expense.query.filter(
                Expense.company_id == self.company_id,
                func.extract('year', Expense.created_at) == year,
                func.extract('month', Expense.created_at) == month
            ).order_by(Expense.id.desc()).first()
            
            if last_expense and last_expense.expense_number:
                try:
                    last_num = int(last_expense.expense_number.split('-')[-1])
                    next_num = last_num + 1
                except:
                    next_num = 1
            else:
                next_num = 1
            
            self.expense_number = f"EXP-{year}{month:02d}-{next_num:04d}"


class ExpenseCategory(db.Model):
    """Categories for organizing expenses"""
    __tablename__ = 'expense_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='expense_categories')
    account = db.relationship('ChartOfAccounts', backref='expense_categories')
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='unique_category_per_company'),
    )
    
    def __repr__(self):
        return f'<ExpenseCategory {self.name}>'


class JournalEntry(db.Model):
    """Double-entry bookkeeping journal entries"""
    __tablename__ = 'journal_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Entry Details
    entry_number = db.Column(db.String(50), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(500), nullable=False)
    
    # Amounts
    debit_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    credit_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    
    # Reference Information
    reference_type = db.Column(db.String(50), nullable=True)  # invoice, payment, expense, adjustment
    reference_id = db.Column(db.Integer, nullable=True)  # ID of the referenced record
    reference_number = db.Column(db.String(100), nullable=True)
    
    # Additional Information
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='journal_entries')
    creator = db.relationship('User', backref='journal_entries')
    
    def __repr__(self):
        return f'<JournalEntry {self.entry_number}: Dr.${self.debit_amount} Cr.${self.credit_amount}>'


class BudgetPeriod(db.Model):
    """Budget periods for financial planning"""
    __tablename__ = 'budget_periods'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='draft')  # draft, active, closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='budget_periods')
    budget_items = db.relationship('BudgetItem', backref='period', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<BudgetPeriod {self.name}: {self.start_date} to {self.end_date}>'


class BudgetItem(db.Model):
    """Budget line items for accounts"""
    __tablename__ = 'budget_items'
    
    id = db.Column(db.Integer, primary_key=True)
    period_id = db.Column(db.Integer, db.ForeignKey('budget_periods.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('chart_of_accounts.id'), nullable=False)
    budgeted_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    notes = db.Column(db.Text, nullable=True)
    
    # Relationships
    account = db.relationship('ChartOfAccounts', backref='budget_items')
    
    def __repr__(self):
        return f'<BudgetItem {self.account.account_name}: ${self.budgeted_amount}>'
