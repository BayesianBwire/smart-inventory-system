from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from extensions import db
from models.finance import (ChartOfAccounts, Invoice, InvoiceItem, Payment, Expense, 
                           ExpenseCategory, JournalEntry, BudgetPeriod, BudgetItem)
from models.finance_extended import (BankAccount, BankTransaction, TaxRate, 
                                   FinancialReport, RecurringTransaction)
from forms.finance_forms import (ChartOfAccountsForm, InvoiceForm, PaymentForm, 
                                ExpenseForm, ExpenseCategoryForm, JournalEntryForm,
                                BankAccountForm, BankTransactionForm, TaxRateForm,
                                BudgetPeriodForm, BudgetItemForm, RecurringTransactionForm,
                                FinancialReportForm, SearchForm, QuickPaymentForm)
from sqlalchemy import func, and_, or_, desc, asc
from datetime import datetime, date, timedelta
from decimal import Decimal
import json

finance_bp = Blueprint('finance', __name__, url_prefix='/finance')

# Dashboard and Overview Routes
@finance_bp.route('/')
@login_required
def dashboard():
    """Finance dashboard with key metrics and charts"""
    company_id = current_user.company_id
    
    # Key Financial Metrics
    total_revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.status == 'paid'
    ).scalar() or 0
    
    total_expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.company_id == company_id,
        Expense.status == 'approved'
    ).scalar() or 0
    
    outstanding_invoices = db.session.query(func.sum(Invoice.total_amount - Invoice.paid_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.status.in_(['sent', 'overdue']),
        Invoice.total_amount > Invoice.paid_amount
    ).scalar() or 0
    
    overdue_invoices = Invoice.query.filter(
        Invoice.company_id == company_id,
        Invoice.status.in_(['sent', 'overdue']),
        Invoice.due_date < date.today(),
        Invoice.total_amount > Invoice.paid_amount
    ).count()
    
    # Recent Transactions
    recent_invoices = Invoice.query.filter_by(company_id=company_id).order_by(desc(Invoice.created_at)).limit(5).all()
    recent_expenses = Expense.query.filter_by(company_id=company_id).order_by(desc(Expense.created_at)).limit(5).all()
    recent_payments = Payment.query.filter_by(company_id=company_id).order_by(desc(Payment.created_at)).limit(5).all()
    
    # Quick Payment Form
    quick_payment_form = QuickPaymentForm(company_id=company_id)
    
    return render_template('finance/dashboard.html',
                         total_revenue=total_revenue,
                         total_expenses=total_expenses,
                         outstanding_invoices=outstanding_invoices,
                         overdue_invoices=overdue_invoices,
                         recent_invoices=recent_invoices,
                         recent_expenses=recent_expenses,
                         recent_payments=recent_payments,
                         quick_payment_form=quick_payment_form)

# Chart of Accounts Routes
@finance_bp.route('/accounts')
@login_required
def accounts():
    """List all chart of accounts"""
    company_id = current_user.company_id
    search_term = request.args.get('search', '')
    account_type = request.args.get('type', '')
    
    query = ChartOfAccounts.query.filter_by(company_id=company_id)
    
    if search_term:
        query = query.filter(or_(
            ChartOfAccounts.account_code.contains(search_term),
            ChartOfAccounts.account_name.contains(search_term)
        ))
    
    if account_type:
        query = query.filter_by(account_type=account_type)
    
    accounts = query.order_by(ChartOfAccounts.account_code).all()
    
    # Group accounts by type
    accounts_by_type = {}
    for account in accounts:
        if account.account_type not in accounts_by_type:
            accounts_by_type[account.account_type] = []
        accounts_by_type[account.account_type].append(account)
    
    return render_template('finance/accounts/list.html', 
                         accounts_by_type=accounts_by_type,
                         search_term=search_term,
                         account_type=account_type)

@finance_bp.route('/accounts/new', methods=['GET', 'POST'])
@login_required
def new_account():
    """Create new chart of account"""
    form = ChartOfAccountsForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        account = ChartOfAccounts(
            company_id=current_user.company_id,
            account_code=form.account_code.data,
            account_name=form.account_name.data,
            account_type=form.account_type.data,
            account_category=form.account_category.data or None,
            parent_account_id=form.parent_account_id.data if form.parent_account_id.data else None,
            description=form.description.data,
            is_active=form.is_active.data
        )
        
        db.session.add(account)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('finance.accounts'))
    
    return render_template('finance/accounts/form.html', form=form, title='New Account')

@finance_bp.route('/accounts/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_account(id):
    """Edit chart of account"""
    account = ChartOfAccounts.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    form = ChartOfAccountsForm(company_id=current_user.company_id, obj=account)
    
    if form.validate_on_submit():
        account.account_code = form.account_code.data
        account.account_name = form.account_name.data
        account.account_type = form.account_type.data
        account.account_category = form.account_category.data or None
        account.parent_account_id = form.parent_account_id.data if form.parent_account_id.data else None
        account.description = form.description.data
        account.is_active = form.is_active.data
        account.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Account updated successfully!', 'success')
        return redirect(url_for('finance.accounts'))
    
    return render_template('finance/accounts/form.html', form=form, title='Edit Account', account=account)

# Invoice Routes
@finance_bp.route('/invoices')
@login_required
def invoices():
    """List all invoices"""
    company_id = current_user.company_id
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    # Filters
    status = request.args.get('status', '')
    search_term = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = Invoice.query.filter_by(company_id=company_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if search_term:
        query = query.filter(or_(
            Invoice.invoice_number.contains(search_term),
            Invoice.billing_name.contains(search_term)
        ))
    
    if date_from:
        try:
            date_from_obj = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date >= date_from_obj)
        except ValueError:
            pass
    
    if date_to:
        try:
            date_to_obj = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(Invoice.invoice_date <= date_to_obj)
        except ValueError:
            pass
    
    invoices = query.order_by(desc(Invoice.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Summary statistics
    total_invoices = query.count()
    total_amount = query.with_entities(func.sum(Invoice.total_amount)).scalar() or 0
    total_paid = query.with_entities(func.sum(Invoice.paid_amount)).scalar() or 0
    
    return render_template('finance/invoices/list.html',
                         invoices=invoices,
                         total_invoices=total_invoices,
                         total_amount=total_amount,
                         total_paid=total_paid,
                         status=status,
                         search_term=search_term,
                         date_from=date_from,
                         date_to=date_to)

@finance_bp.route('/invoices/new', methods=['GET', 'POST'])
@login_required
def new_invoice():
    """Create new invoice"""
    form = InvoiceForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        invoice = Invoice(
            company_id=current_user.company_id,
            customer_id=form.customer_id.data if form.customer_id.data else None,
            opportunity_id=form.opportunity_id.data if form.opportunity_id.data else None,
            created_by=current_user.id,
            invoice_date=form.invoice_date.data,
            due_date=form.due_date.data,
            payment_terms=form.payment_terms.data,
            tax_amount=form.tax_amount.data or 0,
            discount_amount=form.discount_amount.data or 0,
            currency=form.currency.data,
            billing_name=form.billing_name.data,
            billing_email=form.billing_email.data,
            billing_address=form.billing_address.data,
            billing_city=form.billing_city.data,
            billing_state=form.billing_state.data,
            billing_country=form.billing_country.data,
            billing_postal_code=form.billing_postal_code.data,
            reference_number=form.reference_number.data,
            notes=form.notes.data,
            internal_notes=form.internal_notes.data
        )
        
        # Generate invoice number
        invoice.generate_invoice_number()
        
        db.session.add(invoice)
        db.session.commit()
        
        flash('Invoice created successfully!', 'success')
        return redirect(url_for('finance.invoice_detail', id=invoice.id))
    
    return render_template('finance/invoices/form.html', form=form, title='New Invoice')

@finance_bp.route('/invoices/<int:id>')
@login_required
def invoice_detail(id):
    """View invoice details"""
    invoice = Invoice.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    invoice_items = invoice.invoice_items.all()
    payments = invoice.payments.order_by(desc(Payment.created_at)).all()
    
    return render_template('finance/invoices/detail.html',
                         invoice=invoice,
                         invoice_items=invoice_items,
                         payments=payments)

@finance_bp.route('/invoices/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_invoice(id):
    """Edit invoice"""
    invoice = Invoice.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    
    # Only allow editing draft invoices
    if invoice.status != 'draft':
        flash('Only draft invoices can be edited.', 'warning')
        return redirect(url_for('finance.invoice_detail', id=invoice.id))
    
    form = InvoiceForm(company_id=current_user.company_id, obj=invoice)
    
    if form.validate_on_submit():
        form.populate_obj(invoice)
        invoice.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        flash('Invoice updated successfully!', 'success')
        return redirect(url_for('finance.invoice_detail', id=invoice.id))
    
    return render_template('finance/invoices/form.html', form=form, title='Edit Invoice', invoice=invoice)

@finance_bp.route('/invoices/<int:id>/send', methods=['POST'])
@login_required
def send_invoice(id):
    """Mark invoice as sent"""
    invoice = Invoice.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    
    if invoice.status == 'draft':
        invoice.mark_as_sent()
        flash('Invoice marked as sent!', 'success')
    else:
        flash('Invoice cannot be sent in current status.', 'warning')
    
    return redirect(url_for('finance.invoice_detail', id=invoice.id))

# Payment Routes
@finance_bp.route('/payments')
@login_required
def payments():
    """List all payments"""
    company_id = current_user.company_id
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    payments = Payment.query.filter_by(company_id=company_id).order_by(desc(Payment.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('finance/payments/list.html', payments=payments)

@finance_bp.route('/payments/new', methods=['GET', 'POST'])
@finance_bp.route('/invoices/<int:invoice_id>/payment', methods=['GET', 'POST'])
@login_required
def new_payment(invoice_id=None):
    """Record new payment"""
    invoice = None
    if invoice_id:
        invoice = Invoice.query.filter_by(id=invoice_id, company_id=current_user.company_id).first_or_404()
    
    form = PaymentForm(company_id=current_user.company_id)
    
    # Pre-fill amount if recording payment for specific invoice
    if invoice and request.method == 'GET':
        form.amount.data = invoice.balance_due
    
    if form.validate_on_submit():
        payment = Payment(
            company_id=current_user.company_id,
            invoice_id=invoice.id if invoice else None,
            recorded_by=current_user.id,
            payment_date=form.payment_date.data,
            amount=form.amount.data,
            currency=form.currency.data,
            payment_method=form.payment_method.data,
            payment_reference=form.payment_reference.data,
            bank_account_id=form.bank_account_id.data if form.bank_account_id.data else None,
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            notes=form.notes.data
        )
        
        # Generate payment number
        payment.generate_payment_number()
        
        db.session.add(payment)
        
        # Update invoice if payment is for specific invoice
        if invoice:
            invoice.mark_as_paid(form.amount.data)
        
        db.session.commit()
        
        flash('Payment recorded successfully!', 'success')
        
        if invoice:
            return redirect(url_for('finance.invoice_detail', id=invoice.id))
        else:
            return redirect(url_for('finance.payments'))
    
    return render_template('finance/payments/form.html', form=form, title='Record Payment', invoice=invoice)

# Quick Payment (AJAX)
@finance_bp.route('/quick-payment', methods=['POST'])
@login_required
def quick_payment():
    """Quick payment recording for dashboard"""
    form = QuickPaymentForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        invoice = Invoice.query.filter_by(
            id=form.invoice_id.data, 
            company_id=current_user.company_id
        ).first_or_404()
        
        payment = Payment(
            company_id=current_user.company_id,
            invoice_id=invoice.id,
            recorded_by=current_user.id,
            payment_date=form.payment_date.data,
            amount=form.amount.data,
            payment_method=form.payment_method.data
        )
        
        payment.generate_payment_number()
        db.session.add(payment)
        
        invoice.mark_as_paid(form.amount.data)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Payment recorded successfully!'})
    
    return jsonify({'success': False, 'errors': form.errors})

# Expense Routes
@finance_bp.route('/expenses')
@login_required
def expenses():
    """List all expenses"""
    company_id = current_user.company_id
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config.get('ITEMS_PER_PAGE', 20)
    
    # Filters
    status = request.args.get('status', '')
    category_id = request.args.get('category', '', type=int)
    search_term = request.args.get('search', '')
    
    query = Expense.query.filter_by(company_id=company_id)
    
    if status:
        query = query.filter_by(status=status)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search_term:
        query = query.filter(or_(
            Expense.description.contains(search_term),
            Expense.vendor_name.contains(search_term)
        ))
    
    expenses = query.order_by(desc(Expense.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get categories for filter
    categories = ExpenseCategory.query.filter_by(company_id=company_id, is_active=True).all()
    
    return render_template('finance/expenses/list.html',
                         expenses=expenses,
                         categories=categories,
                         status=status,
                         category_id=category_id,
                         search_term=search_term)

@finance_bp.route('/expenses/new', methods=['GET', 'POST'])
@login_required
def new_expense():
    """Create new expense"""
    form = ExpenseForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        expense = Expense(
            company_id=current_user.company_id,
            recorded_by=current_user.id,
            expense_date=form.expense_date.data,
            description=form.description.data,
            amount=form.amount.data,
            currency=form.currency.data,
            category_id=form.category_id.data if form.category_id.data else None,
            vendor_name=form.vendor_name.data,
            vendor_contact=form.vendor_contact.data,
            invoice_reference=form.invoice_reference.data,
            payment_method=form.payment_method.data,
            payment_reference=form.payment_reference.data,
            tags=form.tags.data,
            notes=form.notes.data
        )
        
        # Generate expense number
        expense.generate_expense_number()
        
        # If payment method is provided, mark as paid
        if form.payment_method.data:
            expense.status = 'paid'
            expense.paid_amount = expense.amount
            expense.paid_date = expense.expense_date
        
        db.session.add(expense)
        db.session.commit()
        
        flash('Expense recorded successfully!', 'success')
        return redirect(url_for('finance.expenses'))
    
    return render_template('finance/expenses/form.html', form=form, title='New Expense')

@finance_bp.route('/expenses/<int:id>')
@login_required
def expense_detail(id):
    """View expense details"""
    expense = Expense.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    return render_template('finance/expenses/detail.html', expense=expense)

@finance_bp.route('/expenses/<int:id>/approve', methods=['POST'])
@login_required
def approve_expense(id):
    """Approve expense"""
    expense = Expense.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    
    if expense.status == 'pending':
        notes = request.form.get('approval_notes', '')
        expense.approve(current_user.id, notes)
        flash('Expense approved successfully!', 'success')
    else:
        flash('Expense cannot be approved in current status.', 'warning')
    
    return redirect(url_for('finance.expense_detail', id=expense.id))

@finance_bp.route('/expenses/<int:id>/reject', methods=['POST'])
@login_required
def reject_expense(id):
    """Reject expense"""
    expense = Expense.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    
    if expense.status == 'pending':
        notes = request.form.get('approval_notes', '')
        expense.reject(current_user.id, notes)
        flash('Expense rejected.', 'info')
    else:
        flash('Expense cannot be rejected in current status.', 'warning')
    
    return redirect(url_for('finance.expense_detail', id=expense.id))

# Expense Categories
@finance_bp.route('/expense-categories')
@login_required
def expense_categories():
    """List expense categories"""
    company_id = current_user.company_id
    categories = ExpenseCategory.query.filter_by(company_id=company_id).order_by(ExpenseCategory.name).all()
    return render_template('finance/expense_categories/list.html', categories=categories)

@finance_bp.route('/expense-categories/new', methods=['GET', 'POST'])
@login_required
def new_expense_category():
    """Create new expense category"""
    form = ExpenseCategoryForm(company_id=current_user.company_id)
    
    if form.validate_on_submit():
        category = ExpenseCategory(
            company_id=current_user.company_id,
            name=form.name.data,
            description=form.description.data,
            account_id=form.account_id.data if form.account_id.data else None,
            is_active=form.is_active.data
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Expense category created successfully!', 'success')
        return redirect(url_for('finance.expense_categories'))
    
    return render_template('finance/expense_categories/form.html', form=form, title='New Category')

# Financial Reports
@finance_bp.route('/reports')
@login_required
def reports():
    """Financial reports dashboard"""
    company_id = current_user.company_id
    
    # Get recent reports
    recent_reports = FinancialReport.query.filter_by(company_id=company_id).order_by(desc(FinancialReport.generated_at)).limit(10).all()
    
    return render_template('finance/reports/dashboard.html', recent_reports=recent_reports)

@finance_bp.route('/reports/generate', methods=['GET', 'POST'])
@login_required
def generate_report():
    """Generate financial report"""
    form = FinancialReportForm()
    
    if form.validate_on_submit():
        # Create report record
        report = FinancialReport(
            company_id=current_user.company_id,
            generated_by=current_user.id,
            report_name=form.report_name.data,
            report_type=form.report_type.data,
            period_start=form.period_start.data,
            period_end=form.period_end.data,
            notes=form.notes.data
        )
        
        # Generate report data based on type
        if form.report_type.data == 'profit_loss':
            report_data = generate_profit_loss_data(current_user.company_id, form.period_start.data, form.period_end.data)
        elif form.report_type.data == 'balance_sheet':
            report_data = generate_balance_sheet_data(current_user.company_id, form.period_end.data)
        elif form.report_type.data == 'cash_flow':
            report_data = generate_cash_flow_data(current_user.company_id, form.period_start.data, form.period_end.data)
        else:
            report_data = {}
        
        report.report_data = report_data
        
        db.session.add(report)
        db.session.commit()
        
        flash('Report generated successfully!', 'success')
        return redirect(url_for('finance.view_report', id=report.id))
    
    return render_template('finance/reports/generate.html', form=form)

@finance_bp.route('/reports/<int:id>')
@login_required
def view_report(id):
    """View generated report"""
    report = FinancialReport.query.filter_by(id=id, company_id=current_user.company_id).first_or_404()
    return render_template('finance/reports/view.html', report=report)

# API Routes for AJAX calls
@finance_bp.route('/api/dashboard-metrics')
@login_required
def api_dashboard_metrics():
    """API endpoint for dashboard metrics"""
    company_id = current_user.company_id
    
    # Monthly revenue trend (last 12 months)
    monthly_revenue = []
    for i in range(12):
        month_start = date.today().replace(day=1) - timedelta(days=31*i)
        month_end = (month_start + timedelta(days=31)).replace(day=1) - timedelta(days=1)
        
        revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
            Invoice.company_id == company_id,
            Invoice.status == 'paid',
            Invoice.invoice_date.between(month_start, month_end)
        ).scalar() or 0
        
        monthly_revenue.append({
            'month': month_start.strftime('%Y-%m'),
            'revenue': float(revenue)
        })
    
    monthly_revenue.reverse()
    
    # Expense breakdown by category
    expense_categories = db.session.query(
        ExpenseCategory.name,
        func.sum(Expense.amount).label('total')
    ).join(Expense).filter(
        Expense.company_id == company_id,
        Expense.status == 'approved'
    ).group_by(ExpenseCategory.name).all()
    
    category_data = [{'category': cat.name, 'amount': float(cat.total)} for cat in expense_categories]
    
    return jsonify({
        'monthly_revenue': monthly_revenue,
        'expense_categories': category_data
    })

# Helper functions for report generation
def generate_profit_loss_data(company_id, start_date, end_date):
    """Generate profit and loss report data"""
    # Revenue
    revenue = db.session.query(func.sum(Invoice.total_amount)).filter(
        Invoice.company_id == company_id,
        Invoice.status == 'paid',
        Invoice.invoice_date.between(start_date, end_date)
    ).scalar() or 0
    
    # Expenses
    expenses = db.session.query(func.sum(Expense.amount)).filter(
        Expense.company_id == company_id,
        Expense.status == 'approved',
        Expense.expense_date.between(start_date, end_date)
    ).scalar() or 0
    
    net_income = revenue - expenses
    
    return {
        'revenue': float(revenue),
        'expenses': float(expenses),
        'net_income': float(net_income),
        'period': f"{start_date} to {end_date}"
    }

def generate_balance_sheet_data(company_id, as_of_date):
    """Generate balance sheet report data"""
    # Get account balances by type
    accounts = ChartOfAccounts.query.filter_by(company_id=company_id, is_active=True).all()
    
    assets = sum(acc.get_balance(as_of_date) for acc in accounts if acc.account_type == 'asset')
    liabilities = sum(acc.get_balance(as_of_date) for acc in accounts if acc.account_type == 'liability')
    equity = sum(acc.get_balance(as_of_date) for acc in accounts if acc.account_type == 'equity')
    
    return {
        'assets': float(assets),
        'liabilities': float(liabilities),
        'equity': float(equity),
        'as_of_date': str(as_of_date)
    }

def generate_cash_flow_data(company_id, start_date, end_date):
    """Generate cash flow statement data"""
    # Operating activities
    cash_from_customers = db.session.query(func.sum(Payment.amount)).filter(
        Payment.company_id == company_id,
        Payment.payment_date.between(start_date, end_date),
        Payment.invoice_id.isnot(None)
    ).scalar() or 0
    
    cash_to_suppliers = db.session.query(func.sum(Expense.amount)).filter(
        Expense.company_id == company_id,
        Expense.status == 'paid',
        Expense.expense_date.between(start_date, end_date)
    ).scalar() or 0
    
    net_operating_cash = cash_from_customers - cash_to_suppliers
    
    return {
        'cash_from_customers': float(cash_from_customers),
        'cash_to_suppliers': float(cash_to_suppliers),
        'net_operating_cash': float(net_operating_cash),
        'period': f"{start_date} to {end_date}"
    }

# Search functionality
@finance_bp.route('/search')
@login_required
def search():
    """Search across all finance records"""
    form = SearchForm()
    results = {'invoices': [], 'expenses': [], 'payments': [], 'accounts': []}
    
    if request.args.get('search_term'):
        form.search_term.data = request.args.get('search_term')
        form.search_type.data = request.args.get('search_type', 'all')
        
        company_id = current_user.company_id
        search_term = form.search_term.data
        search_type = form.search_type.data
        
        if search_type in ['all', 'invoices']:
            results['invoices'] = Invoice.query.filter(
                Invoice.company_id == company_id,
                or_(
                    Invoice.invoice_number.contains(search_term),
                    Invoice.billing_name.contains(search_term)
                )
            ).limit(10).all()
        
        if search_type in ['all', 'expenses']:
            results['expenses'] = Expense.query.filter(
                Expense.company_id == company_id,
                or_(
                    Expense.description.contains(search_term),
                    Expense.vendor_name.contains(search_term)
                )
            ).limit(10).all()
        
        if search_type in ['all', 'payments']:
            results['payments'] = Payment.query.filter(
                Payment.company_id == company_id,
                or_(
                    Payment.payment_number.contains(search_term),
                    Payment.payment_reference.contains(search_term)
                )
            ).limit(10).all()
        
        if search_type in ['all', 'accounts']:
            results['accounts'] = ChartOfAccounts.query.filter(
                ChartOfAccounts.company_id == company_id,
                or_(
                    ChartOfAccounts.account_code.contains(search_term),
                    ChartOfAccounts.account_name.contains(search_term)
                )
            ).limit(10).all()
    
    return render_template('finance/search.html', form=form, results=results)
