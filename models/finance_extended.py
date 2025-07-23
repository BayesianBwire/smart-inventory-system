from extensions import db
from datetime import datetime, date
from sqlalchemy import func
from decimal import Decimal

# Import existing BankAccount model to avoid conflicts
from models.bank_account import BankAccount

class BankTransaction(db.Model):
    """Bank transaction records"""
    __tablename__ = 'bank_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_account.id'), nullable=False)
    
    # Transaction Details
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    description = db.Column(db.String(500), nullable=False)
    reference_number = db.Column(db.String(100), nullable=True)
    
    # Amounts
    debit_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    credit_amount = db.Column(db.Numeric(15, 2), nullable=False, default=0.00)
    running_balance = db.Column(db.Numeric(15, 2), nullable=True)
    
    # Transaction Type and Status
    transaction_type = db.Column(db.String(50), nullable=False)  # deposit, withdrawal, transfer, fee, interest
    status = db.Column(db.String(20), nullable=False, default='cleared')  # pending, cleared, cancelled
    
    # Reconciliation
    is_reconciled = db.Column(db.Boolean, default=False)
    reconciled_date = db.Column(db.Date, nullable=True)
    
    # Categories and References
    category = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<BankTransaction {self.description}: Dr.${self.debit_amount} Cr.${self.credit_amount}>'
    
    @property
    def net_amount(self):
        """Net transaction amount (positive for credits, negative for debits)"""
        return self.credit_amount - self.debit_amount


class TaxRate(db.Model):
    """Tax rates for different regions and types"""
    __tablename__ = 'tax_rates'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Tax Details
    name = db.Column(db.String(100), nullable=False)  # VAT, GST, Sales Tax, etc.
    rate = db.Column(db.Numeric(5, 2), nullable=False)  # Percentage rate
    tax_type = db.Column(db.String(50), nullable=False)  # sales_tax, vat, gst, etc.
    
    # Geographic and Category Scope
    region = db.Column(db.String(100), nullable=True)  # Country, State, City
    category = db.Column(db.String(100), nullable=True)  # Product category
    
    # Status and Dates
    is_active = db.Column(db.Boolean, default=True)
    effective_date = db.Column(db.Date, nullable=False, default=date.today)
    expiry_date = db.Column(db.Date, nullable=True)
    
    # Additional Information
    description = db.Column(db.Text, nullable=True)
    tax_authority = db.Column(db.String(200), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='tax_rates')
    
    def __repr__(self):
        return f'<TaxRate {self.name}: {self.rate}%>'
    
    def is_applicable(self, date_check=None):
        """Check if tax rate is applicable for a given date"""
        if not date_check:
            date_check = date.today()
        
        if not self.is_active:
            return False
        
        if date_check < self.effective_date:
            return False
        
        if self.expiry_date and date_check > self.expiry_date:
            return False
        
        return True


class FinancialReport(db.Model):
    """Generated financial reports"""
    __tablename__ = 'financial_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    generated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Report Details
    report_name = db.Column(db.String(200), nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # profit_loss, balance_sheet, cash_flow, trial_balance
    period_start = db.Column(db.Date, nullable=False)
    period_end = db.Column(db.Date, nullable=False)
    
    # Report Data and Status
    report_data = db.Column(db.JSON, nullable=True)  # Stored JSON data of the report
    status = db.Column(db.String(20), nullable=False, default='generated')  # generating, generated, error
    file_path = db.Column(db.String(500), nullable=True)  # Path to exported file
    
    # Additional Information
    parameters = db.Column(db.JSON, nullable=True)  # Report generation parameters
    notes = db.Column(db.Text, nullable=True)
    
    # Timestamps
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='financial_reports')
    generator = db.relationship('User', backref='generated_reports')
    
    def __repr__(self):
        return f'<FinancialReport {self.report_name}: {self.period_start} to {self.period_end}>'


class RecurringTransaction(db.Model):
    """Recurring transactions for automation"""
    __tablename__ = 'recurring_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Transaction Template
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    amount = db.Column(db.Numeric(15, 2), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)  # invoice, expense, payment
    
    # Recurrence Pattern
    frequency = db.Column(db.String(20), nullable=False)  # daily, weekly, monthly, quarterly, yearly
    interval_count = db.Column(db.Integer, nullable=False, default=1)  # Every X intervals
    day_of_month = db.Column(db.Integer, nullable=True)  # For monthly recurrence
    day_of_week = db.Column(db.Integer, nullable=True)  # For weekly recurrence (0=Monday)
    
    # Schedule Dates
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    next_run_date = db.Column(db.Date, nullable=False)
    last_run_date = db.Column(db.Date, nullable=True)
    
    # Status and Settings
    is_active = db.Column(db.Boolean, default=True)
    auto_approve = db.Column(db.Boolean, default=False)
    
    # Template Data
    template_data = db.Column(db.JSON, nullable=True)  # Stored template for transaction creation
    
    # Statistics
    total_generated = db.Column(db.Integer, nullable=False, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='recurring_transactions')
    creator = db.relationship('User', backref='recurring_transactions')
    
    def __repr__(self):
        return f'<RecurringTransaction {self.name}: {self.frequency}>'
    
    def calculate_next_run_date(self):
        """Calculate the next run date based on frequency"""
        from dateutil.relativedelta import relativedelta
        
        if not self.last_run_date:
            self.next_run_date = self.start_date
            return
        
        current_date = self.last_run_date
        
        if self.frequency == 'daily':
            self.next_run_date = current_date + relativedelta(days=self.interval_count)
        elif self.frequency == 'weekly':
            self.next_run_date = current_date + relativedelta(weeks=self.interval_count)
        elif self.frequency == 'monthly':
            if self.day_of_month:
                self.next_run_date = current_date + relativedelta(months=self.interval_count, day=self.day_of_month)
            else:
                self.next_run_date = current_date + relativedelta(months=self.interval_count)
        elif self.frequency == 'quarterly':
            self.next_run_date = current_date + relativedelta(months=3*self.interval_count)
        elif self.frequency == 'yearly':
            self.next_run_date = current_date + relativedelta(years=self.interval_count)
        
        # If end date is set and next run date exceeds it, deactivate
        if self.end_date and self.next_run_date > self.end_date:
            self.is_active = False
            self.next_run_date = None
    
    def should_run_today(self):
        """Check if transaction should run today"""
        if not self.is_active or not self.next_run_date:
            return False
        
        return self.next_run_date <= date.today()


class CashFlowCategory(db.Model):
    """Categories for cash flow classification"""
    __tablename__ = 'cash_flow_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    
    # Category Details
    name = db.Column(db.String(100), nullable=False)
    category_type = db.Column(db.String(20), nullable=False)  # operating, investing, financing
    description = db.Column(db.Text, nullable=True)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    company = db.relationship('Company', backref='cash_flow_categories')
    
    __table_args__ = (
        db.UniqueConstraint('company_id', 'name', name='unique_cash_flow_category_per_company'),
    )
    
    def __repr__(self):
        return f'<CashFlowCategory {self.name}: {self.category_type}>'
