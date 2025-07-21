from flask_wtf import FlaskForm
from wtforms import (StringField, TextAreaField, SelectField, DecimalField, 
                     DateField, BooleanField, IntegerField, SubmitField, 
                     FieldList, FormField, HiddenField)
from wtforms.validators import DataRequired, Length, Email, Optional, NumberRange
from wtforms.widgets import TextArea
from datetime import date, datetime

class ChartOfAccountsForm(FlaskForm):
    """Form for creating and editing chart of accounts"""
    account_code = StringField('Account Code', validators=[DataRequired(), Length(1, 20)])
    account_name = StringField('Account Name', validators=[DataRequired(), Length(1, 200)])
    account_type = SelectField('Account Type', 
                              choices=[('asset', 'Asset'), ('liability', 'Liability'), 
                                     ('equity', 'Equity'), ('revenue', 'Revenue'), 
                                     ('expense', 'Expense')],
                              validators=[DataRequired()])
    account_category = StringField('Account Category', validators=[Optional(), Length(0, 100)])
    parent_account_id = SelectField('Parent Account', coerce=int, validators=[Optional()])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Account')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(ChartOfAccountsForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import ChartOfAccounts
            accounts = ChartOfAccounts.query.filter_by(company_id=company_id, is_active=True).all()
            self.parent_account_id.choices = [(0, 'None')] + [(a.id, f"{a.account_code} - {a.account_name}") for a in accounts]


class InvoiceItemForm(FlaskForm):
    """Form for invoice line items"""
    product_id = SelectField('Product', coerce=int, validators=[Optional()])
    description = StringField('Description', validators=[DataRequired(), Length(1, 500)])
    quantity = DecimalField('Quantity', validators=[DataRequired(), NumberRange(min=0.01)], default=1.00)
    unit_price = DecimalField('Unit Price', validators=[DataRequired(), NumberRange(min=0)], default=0.00)
    item_code = StringField('Item Code', validators=[Optional(), Length(0, 100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 200)])


class InvoiceForm(FlaskForm):
    """Form for creating and editing invoices"""
    # Customer Information
    customer_id = SelectField('Customer', coerce=int, validators=[Optional()])
    opportunity_id = SelectField('Related Opportunity', coerce=int, validators=[Optional()])
    
    # Invoice Details
    invoice_number = StringField('Invoice Number', validators=[Optional(), Length(0, 50)])
    invoice_date = DateField('Invoice Date', validators=[DataRequired()], default=date.today)
    due_date = DateField('Due Date', validators=[DataRequired()])
    payment_terms = SelectField('Payment Terms',
                               choices=[('net_15', 'Net 15'), ('net_30', 'Net 30'), 
                                      ('net_45', 'Net 45'), ('net_60', 'Net 60'),
                                      ('due_on_receipt', 'Due on Receipt')],
                               default='net_30')
    
    # Amounts
    tax_amount = DecimalField('Tax Amount', validators=[NumberRange(min=0)], default=0.00)
    discount_amount = DecimalField('Discount Amount', validators=[NumberRange(min=0)], default=0.00)
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('KES', 'KES')], default='USD')
    
    # Billing Information
    billing_name = StringField('Billing Name', validators=[DataRequired(), Length(1, 200)])
    billing_email = StringField('Billing Email', validators=[Optional(), Email(), Length(0, 255)])
    billing_address = TextAreaField('Billing Address', validators=[Optional(), Length(0, 500)])
    billing_city = StringField('City', validators=[Optional(), Length(0, 100)])
    billing_state = StringField('State/Province', validators=[Optional(), Length(0, 100)])
    billing_country = StringField('Country', validators=[Optional(), Length(0, 100)])
    billing_postal_code = StringField('Postal Code', validators=[Optional(), Length(0, 20)])
    
    # Additional Information
    reference_number = StringField('Reference Number', validators=[Optional(), Length(0, 100)])
    notes = TextAreaField('Customer Notes', validators=[Optional(), Length(0, 1000)])
    internal_notes = TextAreaField('Internal Notes', validators=[Optional(), Length(0, 1000)])
    
    submit = SubmitField('Save Invoice')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(InvoiceForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.crm import Customer, Opportunity
            customers = Customer.query.filter_by(company_id=company_id).all()
            opportunities = Opportunity.query.filter_by(company_id=company_id).all()
            
            self.customer_id.choices = [(0, 'Select Customer')] + [(c.id, c.name) for c in customers]
            self.opportunity_id.choices = [(0, 'None')] + [(o.id, f"{o.name} - {o.customer.name if o.customer else 'No Customer'}") for o in opportunities]


class PaymentForm(FlaskForm):
    """Form for recording payments"""
    # Payment Details
    payment_date = DateField('Payment Date', validators=[DataRequired()], default=date.today)
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('KES', 'KES')], default='USD')
    
    # Payment Method
    payment_method = SelectField('Payment Method',
                                choices=[('cash', 'Cash'), ('check', 'Check'), 
                                       ('bank_transfer', 'Bank Transfer'), 
                                       ('credit_card', 'Credit Card'),
                                       ('mobile_money', 'Mobile Money'),
                                       ('other', 'Other')],
                                validators=[DataRequired()])
    payment_reference = StringField('Payment Reference', validators=[Optional(), Length(0, 200)])
    
    # Bank Account
    bank_account_id = SelectField('Bank Account', coerce=int, validators=[Optional()])
    bank_name = StringField('Bank Name', validators=[Optional(), Length(0, 200)])
    account_number = StringField('Account Number', validators=[Optional(), Length(0, 100)])
    
    # Additional Information
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 1000)])
    
    submit = SubmitField('Record Payment')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance_extended import BankAccount
            bank_accounts = BankAccount.query.filter_by(company_id=company_id, is_active=True).all()
            self.bank_account_id.choices = [(0, 'Select Bank Account')] + [(ba.id, f"{ba.account_name} - {ba.bank_name}") for ba in bank_accounts]


class ExpenseForm(FlaskForm):
    """Form for creating and editing expenses"""
    # Expense Details
    expense_date = DateField('Expense Date', validators=[DataRequired()], default=date.today)
    description = StringField('Description', validators=[DataRequired(), Length(1, 500)])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('KES', 'KES')], default='USD')
    category_id = SelectField('Category', coerce=int, validators=[Optional()])
    
    # Vendor Information
    vendor_name = StringField('Vendor Name', validators=[Optional(), Length(0, 200)])
    vendor_contact = StringField('Vendor Contact', validators=[Optional(), Length(0, 255)])
    invoice_reference = StringField('Invoice/Receipt Reference', validators=[Optional(), Length(0, 100)])
    
    # Payment Information
    payment_method = SelectField('Payment Method',
                                choices=[('', 'Not Paid Yet'), ('cash', 'Cash'), ('check', 'Check'), 
                                       ('bank_transfer', 'Bank Transfer'), 
                                       ('credit_card', 'Credit Card'),
                                       ('mobile_money', 'Mobile Money'),
                                       ('other', 'Other')])
    payment_reference = StringField('Payment Reference', validators=[Optional(), Length(0, 200)])
    
    # Additional Information
    tags = StringField('Tags (comma-separated)', validators=[Optional(), Length(0, 500)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 1000)])
    
    submit = SubmitField('Save Expense')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(ExpenseForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import ExpenseCategory
            categories = ExpenseCategory.query.filter_by(company_id=company_id, is_active=True).all()
            self.category_id.choices = [(0, 'Select Category')] + [(c.id, c.name) for c in categories]


class ExpenseCategoryForm(FlaskForm):
    """Form for expense categories"""
    name = StringField('Category Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    account_id = SelectField('Associated Account', coerce=int, validators=[Optional()])
    is_active = BooleanField('Active', default=True)
    submit = SubmitField('Save Category')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(ExpenseCategoryForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import ChartOfAccounts
            accounts = ChartOfAccounts.query.filter_by(
                company_id=company_id, 
                account_type='expense',
                is_active=True
            ).all()
            self.account_id.choices = [(0, 'Select Account')] + [(a.id, f"{a.account_code} - {a.account_name}") for a in accounts]


class JournalEntryForm(FlaskForm):
    """Form for manual journal entries"""
    entry_number = StringField('Entry Number', validators=[Optional(), Length(0, 50)])
    transaction_date = DateField('Transaction Date', validators=[DataRequired()], default=date.today)
    description = StringField('Description', validators=[DataRequired(), Length(1, 500)])
    
    # Reference Information
    reference_type = SelectField('Reference Type',
                                choices=[('', 'None'), ('invoice', 'Invoice'), 
                                       ('payment', 'Payment'), ('expense', 'Expense'),
                                       ('adjustment', 'Adjustment'), ('other', 'Other')])
    reference_number = StringField('Reference Number', validators=[Optional(), Length(0, 100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 1000)])
    
    submit = SubmitField('Save Entry')


class JournalEntryLineForm(FlaskForm):
    """Form for journal entry lines"""
    account_id = SelectField('Account', coerce=int, validators=[DataRequired()])
    description = StringField('Line Description', validators=[Optional(), Length(0, 200)])
    debit_amount = DecimalField('Debit Amount', validators=[Optional(), NumberRange(min=0)], default=0.00)
    credit_amount = DecimalField('Credit Amount', validators=[Optional(), NumberRange(min=0)], default=0.00)
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(JournalEntryLineForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import ChartOfAccounts
            accounts = ChartOfAccounts.query.filter_by(company_id=company_id, is_active=True).order_by(ChartOfAccounts.account_code).all()
            self.account_id.choices = [(a.id, f"{a.account_code} - {a.account_name}") for a in accounts]


class BankAccountForm(FlaskForm):
    """Form for bank account management"""
    # Account Details
    account_name = StringField('Account Name', validators=[DataRequired(), Length(1, 200)])
    account_number = StringField('Account Number', validators=[DataRequired(), Length(1, 100)])
    bank_name = StringField('Bank Name', validators=[DataRequired(), Length(1, 200)])
    bank_branch = StringField('Bank Branch', validators=[Optional(), Length(0, 200)])
    swift_code = StringField('SWIFT Code', validators=[Optional(), Length(0, 20)])
    routing_number = StringField('Routing Number', validators=[Optional(), Length(0, 50)])
    
    # Account Type and Currency
    account_type = SelectField('Account Type',
                              choices=[('checking', 'Checking'), ('savings', 'Savings'),
                                     ('credit', 'Credit'), ('investment', 'Investment')],
                              default='checking')
    currency = SelectField('Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('KES', 'KES')], default='USD')
    current_balance = DecimalField('Current Balance', validators=[NumberRange(min=-999999999)], default=0.00)
    overdraft_limit = DecimalField('Overdraft Limit', validators=[Optional(), NumberRange(min=0)])
    
    # Status and Settings
    is_active = BooleanField('Active', default=True)
    is_default = BooleanField('Default Account', default=False)
    
    # Additional Information
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(0, 200)])
    contact_phone = StringField('Contact Phone', validators=[Optional(), Length(0, 50)])
    contact_email = StringField('Contact Email', validators=[Optional(), Email(), Length(0, 255)])
    opened_date = DateField('Account Opened Date', validators=[Optional()])
    
    submit = SubmitField('Save Bank Account')


class BankTransactionForm(FlaskForm):
    """Form for bank transactions"""
    transaction_date = DateField('Transaction Date', validators=[DataRequired()], default=date.today)
    description = StringField('Description', validators=[DataRequired(), Length(1, 500)])
    reference_number = StringField('Reference Number', validators=[Optional(), Length(0, 100)])
    
    # Amounts
    debit_amount = DecimalField('Debit Amount', validators=[Optional(), NumberRange(min=0)], default=0.00)
    credit_amount = DecimalField('Credit Amount', validators=[Optional(), NumberRange(min=0)], default=0.00)
    
    # Transaction Type
    transaction_type = SelectField('Transaction Type',
                                  choices=[('deposit', 'Deposit'), ('withdrawal', 'Withdrawal'),
                                         ('transfer', 'Transfer'), ('fee', 'Bank Fee'),
                                         ('interest', 'Interest'), ('other', 'Other')],
                                  validators=[DataRequired()])
    category = StringField('Category', validators=[Optional(), Length(0, 100)])
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 500)])
    
    submit = SubmitField('Save Transaction')


class TaxRateForm(FlaskForm):
    """Form for tax rates"""
    name = StringField('Tax Name', validators=[DataRequired(), Length(1, 100)])
    rate = DecimalField('Tax Rate (%)', validators=[DataRequired(), NumberRange(min=0, max=100)])
    tax_type = SelectField('Tax Type',
                          choices=[('sales_tax', 'Sales Tax'), ('vat', 'VAT'),
                                 ('gst', 'GST'), ('income_tax', 'Income Tax'),
                                 ('other', 'Other')],
                          validators=[DataRequired()])
    
    # Geographic and Category Scope
    region = StringField('Region/Location', validators=[Optional(), Length(0, 100)])
    category = StringField('Product Category', validators=[Optional(), Length(0, 100)])
    
    # Dates
    effective_date = DateField('Effective Date', validators=[DataRequired()], default=date.today)
    expiry_date = DateField('Expiry Date', validators=[Optional()])
    
    # Additional Information
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    tax_authority = StringField('Tax Authority', validators=[Optional(), Length(0, 200)])
    is_active = BooleanField('Active', default=True)
    
    submit = SubmitField('Save Tax Rate')


class BudgetPeriodForm(FlaskForm):
    """Form for budget periods"""
    name = StringField('Budget Name', validators=[DataRequired(), Length(1, 100)])
    description = TextAreaField('Description', validators=[Optional(), Length(0, 500)])
    start_date = DateField('Start Date', validators=[DataRequired()])
    end_date = DateField('End Date', validators=[DataRequired()])
    status = SelectField('Status',
                        choices=[('draft', 'Draft'), ('active', 'Active'), ('closed', 'Closed')],
                        default='draft')
    submit = SubmitField('Save Budget Period')


class BudgetItemForm(FlaskForm):
    """Form for budget line items"""
    account_id = SelectField('Account', coerce=int, validators=[DataRequired()])
    budgeted_amount = DecimalField('Budgeted Amount', validators=[DataRequired(), NumberRange(min=0)], default=0.00)
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 500)])
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(BudgetItemForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import ChartOfAccounts
            accounts = ChartOfAccounts.query.filter_by(company_id=company_id, is_active=True).order_by(ChartOfAccounts.account_code).all()
            self.account_id.choices = [(a.id, f"{a.account_code} - {a.account_name}") for a in accounts]


class RecurringTransactionForm(FlaskForm):
    """Form for recurring transactions"""
    # Basic Information
    name = StringField('Transaction Name', validators=[DataRequired(), Length(1, 200)])
    description = StringField('Description', validators=[DataRequired(), Length(1, 500)])
    amount = DecimalField('Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    transaction_type = SelectField('Transaction Type',
                                  choices=[('invoice', 'Invoice'), ('expense', 'Expense'), ('payment', 'Payment')],
                                  validators=[DataRequired()])
    
    # Recurrence Pattern
    frequency = SelectField('Frequency',
                           choices=[('daily', 'Daily'), ('weekly', 'Weekly'), 
                                  ('monthly', 'Monthly'), ('quarterly', 'Quarterly'), 
                                  ('yearly', 'Yearly')],
                           validators=[DataRequired()])
    interval_count = IntegerField('Every', validators=[DataRequired(), NumberRange(min=1)], default=1)
    day_of_month = IntegerField('Day of Month (1-31)', validators=[Optional(), NumberRange(min=1, max=31)])
    day_of_week = SelectField('Day of Week',
                             choices=[('', 'Not Applicable'), ('0', 'Monday'), ('1', 'Tuesday'),
                                    ('2', 'Wednesday'), ('3', 'Thursday'), ('4', 'Friday'),
                                    ('5', 'Saturday'), ('6', 'Sunday')],
                             coerce=lambda x: int(x) if x else None)
    
    # Schedule Dates
    start_date = DateField('Start Date', validators=[DataRequired()], default=date.today)
    end_date = DateField('End Date (Optional)', validators=[Optional()])
    
    # Settings
    is_active = BooleanField('Active', default=True)
    auto_approve = BooleanField('Auto Approve', default=False)
    
    submit = SubmitField('Save Recurring Transaction')


class FinancialReportForm(FlaskForm):
    """Form for generating financial reports"""
    report_name = StringField('Report Name', validators=[DataRequired(), Length(1, 200)])
    report_type = SelectField('Report Type',
                             choices=[('profit_loss', 'Profit & Loss'), 
                                    ('balance_sheet', 'Balance Sheet'),
                                    ('cash_flow', 'Cash Flow Statement'),
                                    ('trial_balance', 'Trial Balance'),
                                    ('accounts_receivable', 'Accounts Receivable'),
                                    ('accounts_payable', 'Accounts Payable')],
                             validators=[DataRequired()])
    
    # Date Range
    period_start = DateField('Period Start', validators=[DataRequired()])
    period_end = DateField('Period End', validators=[DataRequired()])
    
    # Additional Options
    include_zero_balances = BooleanField('Include Zero Balances', default=False)
    group_by_category = BooleanField('Group by Category', default=True)
    notes = TextAreaField('Notes', validators=[Optional(), Length(0, 1000)])
    
    submit = SubmitField('Generate Report')


class SearchForm(FlaskForm):
    """General search form for finance module"""
    search_term = StringField('Search', validators=[Optional(), Length(0, 200)])
    search_type = SelectField('Search In',
                             choices=[('all', 'All'), ('invoices', 'Invoices'),
                                    ('expenses', 'Expenses'), ('payments', 'Payments'),
                                    ('accounts', 'Chart of Accounts')],
                             default='all')
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    amount_min = DecimalField('Min Amount', validators=[Optional(), NumberRange(min=0)])
    amount_max = DecimalField('Max Amount', validators=[Optional(), NumberRange(min=0)])
    
    submit = SubmitField('Search')


class QuickPaymentForm(FlaskForm):
    """Quick payment form for dashboard"""
    invoice_id = SelectField('Invoice', coerce=int, validators=[DataRequired()])
    amount = DecimalField('Payment Amount', validators=[DataRequired(), NumberRange(min=0.01)])
    payment_method = SelectField('Payment Method',
                                choices=[('cash', 'Cash'), ('check', 'Check'), 
                                       ('bank_transfer', 'Bank Transfer'), 
                                       ('credit_card', 'Credit Card')],
                                validators=[DataRequired()])
    payment_date = DateField('Payment Date', validators=[DataRequired()], default=date.today)
    
    submit = SubmitField('Record Payment')
    
    def __init__(self, company_id=None, *args, **kwargs):
        super(QuickPaymentForm, self).__init__(*args, **kwargs)
        if company_id:
            from models.finance import Invoice
            unpaid_invoices = Invoice.query.filter(
                Invoice.company_id == company_id,
                Invoice.status.in_(['sent', 'overdue']),
                Invoice.total_amount > Invoice.paid_amount
            ).all()
            self.invoice_id.choices = [(i.id, f"{i.invoice_number} - ${i.balance_due:.2f}") for i in unpaid_invoices]
