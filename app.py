from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, current_user, login_required as flask_login_required
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import os
import random
import string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Local imports
from models import db, User, Product, Sale, LoginLog, BankAccount, Transaction, PayrollRecord
from models.audit_log import AuditLog
from models.product import Product
from models.company import Company
from models.login_log import LoginLog
from models.user import User
from models.sale import Sale
from forms import ProductForm, LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm, CompanyForm
from utils.permissions import has_permission
from translations.translations import TRANSLATIONS

load_dotenv()

app = Flask(__name__)

# Flask-Mail configuration
app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER')
app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('FROM_EMAIL')

mail = Mail(app)
app.secret_key = os.getenv('SECRET_KEY')
app.jinja_env.globals.update(zip=zip)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login_page'  # or 'login' depending on your route

@login_manager.user_loader
def load_user(user_id):
    with app.app_context():  # Optional but safe in some async edge cases
        return db.session.get(User, int(user_id))

@app.context_processor
def inject_csrf_token():
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf())

@app.context_processor
def inject_translation():
    def translate(text):
        lang = session.get('lang', 'en')
        return TRANSLATIONS.get(lang, {}).get(text, text)
    return dict(_=translate)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SESSION_COOKIE_SECURE'] = True
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=30)
app.permanent_session_lifetime = timedelta(minutes=30)

csrf = CSRFProtect(app)
serializer = URLSafeTimedSerializer(app.secret_key)

db.init_app(app)
migrate = Migrate(app, db)

# ✅ Audit log helper function
def log_action(action, entity, entity_id=None):
    if 'user' in session:
        audit = AuditLog(
            action=action,
            entity=entity,
            entity_id=entity_id,
            performed_by=session['user']
        )
        try:
            db.session.add(audit)
            db.session.commit()
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"[AuditLog Error] {str(e)}")

@app.before_request
def set_session_permanent():
    session.permanent = True

# -------------------- Auth Helpers --------------------

def company_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Login required", "warning")
            return redirect(url_for('login_page'))
        
        # Check if user has a company
        user = User.query.filter_by(username=session['user']).first()
        if not user or not user.company_id:
            # Show company registration modal/page
            return redirect(url_for('register_company'))
        return f(*args, **kwargs)
    return decorated_function

def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)  # Skip email verification for now
    return decorated_function

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash("Login required", "warning")
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session or session['role'] not in roles:
                flash("Access denied", "danger")
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

# -------------------- Email Sending --------------------

import os
import smtplib
from flask import url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Shared SMTP config
def get_smtp_config():
    return {
        'server': os.getenv('SMTP_SERVER'),
        'port': int(os.getenv('SMTP_PORT', 587)),
        'username': os.getenv('SMTP_USERNAME'),
        'password': os.getenv('SMTP_PASSWORD'),
        'from_email': os.getenv('FROM_EMAIL'),
        'app_name': "RahaSoft"
    }

def send_verification_email(user_email, token):
    cfg = get_smtp_config()
    verify_url = url_for('verify_email', token=token, _external=True)

    subject = f"{cfg['app_name']} - Verify Your Email"
    body = f"""Hi,

Thank you for registering with {cfg['app_name']}.

Please verify your email address by clicking the link below:

{verify_url}

If you did not register, please ignore this email.

Regards,
{cfg['app_name']} Team
"""

    send_email(cfg, user_email, subject, body)

def send_reset_email(user_email, token):
    cfg = get_smtp_config()
    reset_url = url_for('reset_password', token=token, _external=True)

    subject = f"{cfg['app_name']} - Password Reset Request"
    body = f"""Hi,

We received a request to reset your password.

Click the link below to reset it (valid for 1 hour):

{reset_url}

If you didn't request a password reset, please ignore this email.

Regards,
{cfg['app_name']} Team
"""

    send_email(cfg, user_email, subject, body)

def send_email(cfg, to_email, subject, body):
    msg = MIMEMultipart()
    msg['From'] = cfg['from_email']
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(cfg['server'], cfg['port']) as server:
            server.starttls()
            server.login(cfg['username'], cfg['password'])
            server.send_message(msg)
    except Exception as e:
        app.logger.error(f"❌ Failed to send email to {to_email}: {e}")

def send_welcome_email(user):
    subject = "🎉 Welcome to RahaSoft!"
    recipient = user.email
    message_body = f"""
    Hi {user.full_name},

    🎉 Congratulations on registering with RahaSoft!

    We're excited to have you on board. Your account details:
    - Username: {user.username}
    - Email: {user.email}
    - Password: {user.password} (keep this safe!)

    You can use either your username or email to log in.

    🚨 Please treat this information as confidential and do not share it with anyone.

    We're confident RahaSoft will help you manage your operations with ease!

    Warm regards,  
    RahaSoft Team
    """

    msg = Message(subject, recipients=[recipient], body=message_body)
    mail.send(msg)

def send_company_id_email(user, company):
    """Send company unique ID to the admin via email"""
    subject = f"🏢 Company Registration Successful - Your Unique ID: {company.unique_id}"
    recipient = user.email
    message_body = f"""
    Hi {user.full_name},

    🎉 Congratulations! Your company "{company.name}" has been successfully registered with RahaSoft!

    📋 COMPANY DETAILS:
    ----------------------------------------
    Company Name: {company.name}
    Unique Company ID: {company.unique_id}
    Industry: {company.industry or 'Not specified'}
    Admin: {user.full_name} ({user.email})
    Registration Date: {company.created_at.strftime('%B %d, %Y') if company.created_at else 'Today'}
    ----------------------------------------

    🔐 IMPORTANT: Your Unique Company ID is {company.unique_id}
    
    This ID is permanent and identifies your company in our system. Please:
    ✅ Save this ID in a secure location
    ✅ Use it for any support requests
    ✅ Share it only with authorized personnel
    
    🚀 You are now the administrator of your company and can:
    • Add and manage employees
    • Access all ERP modules
    • Configure company settings
    • Generate reports and analytics

    🆘 Need help? Contact our support team at support@rahasoft.app
    Include your Company ID ({company.unique_id}) in all communications.

    Welcome to the RahaSoft family!

    Best regards,  
    RahaSoft Team
    """

    try:
        msg = Message(subject, recipients=[recipient], body=message_body)
        mail.send(msg)
        app.logger.info(f"✅ Company ID email sent to {recipient} for company {company.unique_id}")
    except Exception as e:
        app.logger.error(f"❌ Failed to send company ID email to {recipient}: {e}")

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    supported_langs = ['en', 'fr', 'es', 'de', 'sw', 'ar', 'zh', 'hi', 'pt']
    if lang_code in supported_langs:
        session['lang'] = lang_code
        flash(f"Language changed successfully", "success")
    else:
        flash("Language not supported", "warning")
    # Redirect back to where user came from or dashboard page as fallback
    next_url = request.referrer or url_for('dashboard')
    return redirect(next_url)
# -------------------- Routes --------------------
@app.route('/users')
@login_required
def user_list():
    if not has_permission(current_user.role, 'view_users'):
        flash("⛔ You don’t have permission to view user accounts.", "danger")
        return redirect(url_for('hr_dashboard'))  # or whichever dashboard you want

    users = User.query.all()
    return render_template('users.html', users=users)

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    form = LoginForm()

    if form.validate_on_submit():
        login_input = form.username.data.strip().lower()  # Accepts username or email
        password = form.password.data.strip()

        # Try to find user by username or email, case-insensitively
        user = User.query.filter(
            (User.username.ilike(login_input)) | (User.email.ilike(login_input))
        ).first()

        if user:
            if not user.email_confirmed:
                flash("⚠️ Please verify your email address before logging in. Check your inbox or spam.", "warning")
                return redirect(url_for('login_page'))

            if user.verify_password(password):
                login_user(user)

                # Store additional info in session
                session['user'] = user.username
                session['email'] = user.email
                session['role'] = user.role

                flash(f"✅ Welcome back, {user.username}!", "success")
                return redirect(url_for('dashboard'))

        flash("❌ Invalid username/email or password.", "danger")

    return render_template('login.html', form=form)

@app.route('/unverified')
def unverified_notice():
    return render_template('unverified_notice.html')

# Decorator to ensure the user's email is verified
def email_verified_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, 'email_confirmed', False):
            flash("⚠️ Please verify your email address to access this page.", "warning")
            return redirect(url_for('unverified_notice'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login_logs')
@login_required
@role_required('admin', 'hr', 'superadmin')
def login_logs():
    logs = LoginLog.query.order_by(LoginLog.timestamp.desc()).all()
    return render_template('login_logs.html', logs=logs)

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    return render_template('privacy.html')

@app.route('/welcome')
def welcome():
    username = session.get('user')  # No default, so no fake name
    return render_template('welcome.html', username=username)


@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out of RahaSoft.", "info")
    return redirect(url_for('welcome'))

@app.route('/register_company', methods=['GET', 'POST'])
@login_required
def register_company():
    """Company registration route - required before accessing modules"""
    form = CompanyForm()
    
    # Check if user already has a company
    user = User.query.filter_by(username=session['user']).first()
    if user and user.company_id:
        flash("You already have a registered company.", "info")
        return redirect(url_for('dashboard'))
    
    if form.validate_on_submit():
        # Generate unique company ID
        unique_company_id = Company.generate_unique_id()
        
        # Create new company
        company = Company(
            name=form.name.data,
            unique_id=unique_company_id,
            industry=form.industry.data,
            address=form.address.data,
            phone=form.phone.data,
            email=form.email.data
        )
        
        try:
            db.session.add(company)
            db.session.flush()  # Get the company ID
            
            # Create free subscription for the company (3 modules free)
            from models.subscription import Subscription
            from datetime import datetime, timedelta
            
            free_subscription = Subscription(
                company_id=company.id,
                plan_name="Free Plan",
                plan_type="free",
                status="active",
                start_date=datetime.utcnow(),
                end_date=datetime.utcnow() + timedelta(days=365),  # 1 year free
                price=0.00,
                modules_limit=3,
                active_modules="[]",  # Empty list initially
                features={
                    "modules_limit": 3,
                    "max_users": 10,
                    "max_storage_gb": 5,
                    "support": "basic"
                }
            )
            db.session.add(free_subscription)
            
            # Assign user to company as admin
            user.company_id = company.id
            user.role = 'admin'  # Make them admin of their company
            
            db.session.commit()
            
            # Update session
            session['role'] = 'admin'
            session['company_id'] = company.id
            session['company_name'] = company.name
            
            # Send company ID notification email to admin
            send_company_id_email(user, company)
            
            flash(f"Company '{company.name}' registered successfully! Your unique company ID is: {unique_company_id}. Check your email for details.", "success")
            log_action("Company Registration", "Company", company.id)
            
            # Redirect to module selection page
            return redirect(url_for('select_modules'))
            
        except SQLAlchemyError as e:
            db.session.rollback()
            flash("Error registering company. Please try again.", "danger")
            app.logger.error(f"Company registration error: {str(e)}")
    
    return render_template('register_company.html', form=form)

@app.route('/select_modules', methods=['GET', 'POST'])
@login_required
def select_modules():
    """Module selection page for new companies"""
    user = User.query.filter_by(username=session['user']).first()
    if not user or not user.company_id:
        flash("Please register a company first.", "warning")
        return redirect(url_for('register_company'))
    
    from models.subscription import Subscription
    subscription = Subscription.query.filter_by(company_id=user.company_id).first()
    if not subscription:
        flash("No subscription found. Please contact support.", "error")
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        selected_modules = request.form.getlist('modules')
        
        if len(selected_modules) == 0:
            flash("Please select at least one module.", "warning")
            return render_template('select_modules.html')
        
        if len(selected_modules) > subscription.modules_limit:
            flash(f"You can only select up to {subscription.modules_limit} modules with your current plan.", "warning")
            return render_template('select_modules.html')
        
        # Update subscription with selected modules
        subscription.set_active_modules(selected_modules)
        db.session.commit()
        
        flash(f"Successfully activated {len(selected_modules)} modules: {', '.join(selected_modules)}", "success")
        return redirect(url_for('dashboard'))
    
    return render_template('select_modules.html')

@app.route('/founder')
@login_required
@role_required('super_admin')
def founder_dashboard():
    """Founder dashboard to view all companies and their details"""
    from models.subscription import Subscription
    
    # Get all companies with their related data
    companies = Company.query.all()
    
    # Calculate statistics
    total_companies = len(companies)
    total_users = User.query.count()
    
    # Count subscription types
    free_plans = Subscription.query.filter_by(plan_type='free').count()
    paid_plans = Subscription.query.filter(Subscription.plan_type != 'free').count()
    
    return render_template('founder_dashboard.html',
                         companies=companies,
                         total_companies=total_companies,
                         total_users=total_users,
                         free_plans=free_plans,
                         paid_plans=paid_plans)

@app.route('/founder/export')
@login_required
@role_required('super_admin')
def founder_export_data():
    """Export company data as CSV"""
    import csv
    from io import StringIO
    from flask import make_response
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Company ID', 'Company Name', 'Industry', 'Admin Name', 'Admin Email',
        'Phone', 'Employee Count', 'Active Modules', 'Plan Type', 'Created Date'
    ])
    
    # Write data
    companies = Company.query.all()
    for company in companies:
        admin = next((user for user in company.users if user.role == 'admin'), None)
        subscription = company.subscription[0] if company.subscription else None
        active_modules = subscription.get_active_modules_list() if subscription else []
        
        writer.writerow([
            company.unique_id,
            company.name,
            company.industry or '',
            admin.full_name if admin else '',
            admin.email if admin else '',
            company.phone or '',
            len(company.users),
            ', '.join(active_modules),
            subscription.plan_type if subscription else 'No Plan',
            company.created_at.strftime('%Y-%m-%d') if company.created_at else ''
        ])
    
    output.seek(0)
    
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=companies_export.csv'
    
    return response

@app.route('/check_company_status')
@login_required
def check_company_status():
    """API endpoint to check if user has a company"""
    user = User.query.filter_by(username=session['user']).first()
    has_company = bool(user and user.company_id)
    
    return {
        'has_company': has_company,
        'company_name': user.company.name if has_company else None,
        'user_role': user.role if has_company else None
    }
# --- Product Master Data ---
@app.route('/product_list')
@login_required
def product_list():
    # Show all products, with filters/search
    return render_template('product_list.html')

@app.route('/categories_units')
@login_required
def categories_units():
    # Manage categories, subcategories, and units
    return render_template('categories_units.html')

@app.route('/product_images')
@login_required
def product_images():
    # Manage product images
    return render_template('product_images.html')

# --- Stock Entries ---
@app.route('/stock_in', methods=['GET', 'POST'])
@login_required
def stock_in():
    # Handle stock in (purchases/restocks)
    return render_template('stock_in.html')

@app.route('/stock_out', methods=['GET', 'POST'])
@login_required
def stock_out():
    # Handle stock out (sales, consumption, returns)
    return render_template('stock_out.html')

@app.route('/stock_adjustment', methods=['GET', 'POST'])
@login_required
def stock_adjustment():
    # Handle stock adjustments (losses, damage, etc.)
    return render_template('stock_adjustment.html')

@app.route('/opening_stock', methods=['GET', 'POST'])
@login_required
def opening_stock():
    # Set up opening stock balances
    return render_template('opening_stock.html')

# --- Current Stock Levels ---
@app.route('/stock_overview')
@login_required
def stock_overview():
    # View current stock levels
    return render_template('stock_overview.html')

@app.route('/stock_alerts')
@login_required
def stock_alerts():
    # Low stock and overstock alerts
    return render_template('stock_alerts.html')

@app.route('/stock_value')
@login_required
def stock_value():
    # Show total stock value
    return render_template('stock_value.html')

# --- Stock History Logs ---
@app.route('/stock_logs')
@login_required
def stock_logs():
    # Detailed movement log for every item
    return render_template('stock_logs.html')

# --- Stock Alerts & Notifications ---
@app.route('/expiry_alerts')
@login_required
def expiry_alerts():
    # Expiry/overstock notifications
    return render_template('expiry_alerts.html')

# --- Product Variants & Units ---
@app.route('/product_variants')
@login_required
def product_variants():
    # Manage product variants (sizes, packaging, etc.)
    return render_template('product_variants.html')

@app.route('/units_of_measure')
@login_required
def units_of_measure():
    # Manage multiple units per product
    return render_template('units_of_measure.html')

# --- Inventory Valuation ---
@app.route('/inventory_valuation')
@login_required
def inventory_valuation():
    # FIFO, LIFO, Average Cost valuation
    return render_template('inventory_valuation.html')

# --- Reports ---
@app.route('/stock_summary_report')
@login_required
def stock_summary_report():
    # Stock summary report
    return render_template('stock_summary_report.html')

@app.route('/stock_movement_report')
@login_required
def stock_movement_report():
    # Stock movement report
    return render_template('stock_movement_report.html')

@app.route('/fast_slow_movers')
@login_required
def fast_slow_movers():
    # Fast/slow moving items report
    return render_template('fast_slow_movers.html')
@app.route('/pos')
@login_required
def pos_dashboard():
    return render_template('pos_dashboard.html')

@app.route('/pos/new_sale')
@login_required
def pos_new_sale():
    return render_template('pos_new_sale.html')

@app.route('/pos/payment')
@login_required
def pos_payment():
    return render_template('pos_payment.html')

@app.route('/pos/add_customer')
@login_required
def pos_add_customer():
    return render_template('pos_add_customer.html')

@app.route('/pos/customer_history')
@login_required
def pos_customer_history():
    return render_template('pos_customer_history.html')

@app.route('/pos/loyalty')
@login_required
def pos_loyalty():
    return render_template('pos_loyalty.html')

@app.route('/pos/receipt')
@login_required
def pos_receipt():
    return render_template('pos_receipt.html')

@app.route('/pos/settings')
@login_required
def pos_settings():
    return render_template('pos_settings.html')

@app.route('/pos/shift')
@login_required
def pos_shift():
    return render_template('pos_shift.html')

@app.route('/pos/cash')
@login_required
def pos_cash():
    return render_template('pos_cash.html')

@app.route('/pos/register_report')
@login_required
def pos_register_report():
    return render_template('pos_register_report.html')

@app.route('/pos/park_order')
@login_required
def pos_park_order():
    return render_template('pos_park_order.html')

@app.route('/pos/returns')
@login_required
def pos_returns():
    return render_template('pos_returns.html')

@app.route('/pos/reports')
@login_required
def pos_reports():
    return render_template('pos_reports.html')

@app.route('/pos/offline')
@login_required
def pos_offline():
    return render_template('pos_offline.html')

@app.route('/pos/hardware')
@login_required
def pos_hardware():
    return render_template('pos_hardware.html')
@app.route('/purchasing')
@login_required
def purchasing_dashboard():
    return render_template('purchasing_dashboard.html')

@app.route('/create_purchase_order')
@login_required
def create_purchase_order():
    return render_template('create_purchase_order.html')

@app.route('/purchase_orders')
@login_required
def purchase_orders():
    return render_template('purchase_orders.html')

@app.route('/supplier_quotations')
@login_required
def supplier_quotations():
    return render_template('supplier_quotations.html')

@app.route('/create_purchase_request')
@login_required
def create_purchase_request():
    return render_template('create_purchase_request.html')

@app.route('/purchase_requests')
@login_required
def purchase_requests():
    return render_template('purchase_requests.html')

@app.route('/goods_receipt')
@login_required
def goods_receipt():
    return render_template('goods_receipt.html')

@app.route('/pending_grn')
@login_required
def pending_grn():
    return render_template('pending_grn.html')

@app.route('/suppliers')
@login_required
def suppliers():
    return render_template('suppliers.html')

@app.route('/supplier_contracts')
@login_required
def supplier_contracts():
    return render_template('supplier_contracts.html')

@app.route('/create_purchase_invoice')
@login_required
def create_purchase_invoice():
    return render_template('create_purchase_invoice.html')

@app.route('/purchase_invoices')
@login_required
def purchase_invoices():
    return render_template('purchase_invoices.html')

@app.route('/record_supplier_payment')
@login_required
def record_supplier_payment():
    return render_template('record_supplier_payment.html')

@app.route('/supplier_payments')
@login_required
def supplier_payments():
    return render_template('supplier_payments.html')

@app.route('/purchase_returns')
@login_required
def purchase_returns():
    return render_template('purchase_returns.html')

@app.route('/purchase_summary_report')
@login_required
def purchase_summary_report():
    return render_template('purchase_summary_report.html')

@app.route('/purchase_by_supplier_report')
@login_required
def purchase_by_supplier_report():
    return render_template('purchase_by_supplier_report.html')

@app.route('/purchase_item_report')
@login_required
def purchase_item_report():
    return render_template('purchase_item_report.html')

@app.route('/purchase_price_tracking')
@login_required
def purchase_price_tracking():
    return render_template('purchase_price_tracking.html')

@app.route('/purchase_landed_cost')
@login_required
def purchase_landed_cost():
    return render_template('purchase_landed_cost.html')

@app.route('/purchase_settings')
@login_required
def purchase_settings():
    return render_template('purchase_settings.html')

@app.route('/purchase_po_numbering')
@login_required
def purchase_po_numbering():
    return render_template('purchase_po_numbering.html')
@app.route('/warehouse')
@login_required
def warehouse_dashboard():
    return render_template('warehouse_dashboard.html')

@app.route('/manage_warehouses')
@login_required
def manage_warehouses():
    return render_template('manage_warehouses.html')

@app.route('/warehouse_zones')
@login_required
def warehouse_zones():
    return render_template('warehouse_zones.html')

@app.route('/warehouse_managers')
@login_required
def warehouse_managers():
    return render_template('warehouse_managers.html')

@app.route('/putaway_rules')
@login_required
def putaway_rules():
    return render_template('putaway_rules.html')

@app.route('/picking_rules')
@login_required
def picking_rules():
    return render_template('picking_rules.html')

@app.route('/warehouse_transfers')
@login_required
def warehouse_transfers():
    return render_template('warehouse_transfers.html')

@app.route('/bins_shelves')
@login_required
def bins_shelves():
    return render_template('bins_shelves.html')

@app.route('/bin_capacity')
@login_required
def bin_capacity():
    return render_template('bin_capacity.html')

@app.route('/stock_by_warehouse')
@login_required
def stock_by_warehouse():
    return render_template('stock_by_warehouse.html')

@app.route('/batch_serial_tracking')
@login_required
def batch_serial_tracking():
    return render_template('batch_serial_tracking.html')

@app.route('/bin_stock_alerts')
@login_required
def bin_stock_alerts():
    return render_template('bin_stock_alerts.html')

@app.route('/warehouse_receiving')
@login_required
def warehouse_receiving():
    return render_template('warehouse_receiving.html')

@app.route('/warehouse_discrepancy')
@login_required
def warehouse_discrepancy():
    return render_template('warehouse_discrepancy.html')

@app.route('/warehouse_dispatch')
@login_required
def warehouse_dispatch():
    return render_template('warehouse_dispatch.html')

@app.route('/warehouse_delivery')
@login_required
def warehouse_delivery():
    return render_template('warehouse_delivery.html')

@app.route('/warehouse_audits')
@login_required
def warehouse_audits():
    return render_template('warehouse_audits.html')

@app.route('/warehouse_multiuser_count')
@login_required
def warehouse_multiuser_count():
    return render_template('warehouse_multiuser_count.html')

@app.route('/warehouse_alerts')
@login_required
def warehouse_alerts():
    return render_template('warehouse_alerts.html')

@app.route('/warehouse_automation')
@login_required
def warehouse_automation():
    return render_template('warehouse_automation.html')

@app.route('/warehouse_stock_report')
@login_required
def warehouse_stock_report():
    return render_template('warehouse_stock_report.html')

@app.route('/warehouse_transfer_report')
@login_required
def warehouse_transfer_report():
    return render_template('warehouse_transfer_report.html')

@app.route('/warehouse_bin_audit_report')
@login_required
def warehouse_bin_audit_report():
    return render_template('warehouse_bin_audit_report.html')

@app.route('/warehouse_rfid_barcode')
@login_required
def warehouse_rfid_barcode():
    return render_template('warehouse_rfid_barcode.html')

@app.route('/warehouse_mobile_geo')
@login_required
def warehouse_mobile_geo():
    return render_template('warehouse_mobile_geo.html')
@app.route('/order_management')
@login_required
def order_management_dashboard():
    return render_template('order_management_dashboard.html')

@app.route('/create_sales_order')
@login_required
def create_sales_order():
    return render_template('create_sales_order.html')

@app.route('/sales_orders')
@login_required
def sales_orders():
    return render_template('sales_orders.html')

@app.route('/order_fulfillment')
@login_required
def order_fulfillment():
    return render_template('order_fulfillment.html')

@app.route('/backorders')
@login_required
def backorders():
    return render_template('backorders.html')

@app.route('/preorders')
@login_required
def preorders():
    return render_template('preorders.html')

@app.route('/order_returns')
@login_required
def order_returns():
    return render_template('order_returns.html')

@app.route('/order_invoicing')
@login_required
def order_invoicing():
    return render_template('order_invoicing.html')

@app.route('/order_tracking')
@login_required
def order_tracking():
    return render_template('order_tracking.html')

@app.route('/order_integration')
@login_required
def order_integration():
    return render_template('order_integration.html')

@app.route('/order_reports')
@login_required
def order_reports():
    return render_template('order_reports.html')

@app.route('/order_advanced')
@login_required
def order_advanced():
    return render_template('order_advanced.html')

@app.route('/employee_profiles')
@login_required
def employee_profiles():
    return render_template('employee_profiles.html')

@app.route('/departments_locations')
@login_required
def departments_locations():
    return render_template('departments_locations.html')

@app.route('/employee_exit')
@login_required
def employee_exit():
    return render_template('employee_exit.html')

@app.route('/performance_kpi')
@login_required
def performance_kpi():
    return render_template('performance_kpi.html')

@app.route('/performance_goals')
@login_required
def performance_goals():
    return render_template('performance_goals.html')

@app.route('/recruitment_jobs')
@login_required
def recruitment_jobs():
    return render_template('recruitment_jobs.html')

@app.route('/recruitment_applicants')
@login_required
def recruitment_applicants():
    return render_template('recruitment_applicants.html')

@app.route('/training_calendar')
@login_required
def training_calendar():
    return render_template('training_calendar.html')

@app.route('/training_resources')
@login_required
def training_resources():
    return render_template('training_resources.html')

@app.route('/disciplinary_actions')
@login_required
def disciplinary_actions():
    return render_template('disciplinary_actions.html')

@app.route('/benefits_assets')
@login_required
def benefits_assets():
    return render_template('benefits_assets.html')

@app.route('/awards_events')
@login_required
def awards_events():
    return render_template('awards_events.html')

@app.route('/employee_contracts')
@login_required
def employee_contracts():
    return render_template('employee_contracts.html')

@app.route('/employee_policies')
@login_required
def employee_policies():
    return render_template('employee_policies.html')

@app.route('/hr_analytics')
@login_required
def hr_analytics():
    return render_template('hr_analytics.html')

@app.route('/self_service_dashboard')
@login_required
def self_service_dashboard():
    return render_template('self_service_dashboard.html')

@app.route('/self_service_announcements')
@login_required
def self_service_announcements():
    return render_template('self_service_announcements.html')
@app.route('/attendance')
@login_required
def attendance_dashboard():
    return render_template('attendance_dashboard.html')

@app.route('/attendance/checkin')
@login_required
def attendance_checkin():
    return render_template('attendance_checkin.html')

@app.route('/attendance/biometric')
@login_required
def attendance_biometric():
    return render_template('attendance_biometric.html')

@app.route('/attendance/logs')
@login_required
def attendance_logs():
    return render_template('attendance_logs.html')

@app.route('/attendance/export')
@login_required
def attendance_export():
    return render_template('attendance_export.html')

@app.route('/attendance/shifts')
@login_required
def attendance_shifts():
    return render_template('attendance_shifts.html')

@app.route('/attendance/shift_swap')
@login_required
def attendance_shift_swap():
    return render_template('attendance_shift_swap.html')

@app.route('/attendance/overtime')
@login_required
def attendance_overtime():
    return render_template('attendance_overtime.html')

@app.route('/attendance/exceptions')
@login_required
def attendance_exceptions():
    return render_template('attendance_exceptions.html')

@app.route('/attendance/reports')
@login_required
def attendance_reports():
    return render_template('attendance_reports.html')

@app.route('/attendance/analytics_export')
@login_required
def attendance_analytics_export():
    return render_template('attendance_analytics_export.html')
# ...existing code...

@app.route('/finance/bank_cash')
@login_required
def finance_bank_cash_dashboard():
    return render_template('finance_bank_cash_dashboard.html')


@app.route('/finance/cash_accounts')
@login_required
def cash_accounts():
    return render_template('cash_accounts.html')

@app.route('/finance/fund_transfers')
@login_required
def fund_transfers():
    return render_template('fund_transfers.html')

@app.route('/finance/bank_reconciliation')
@login_required
def bank_reconciliation():
    return render_template('bank_reconciliation.html')

@app.route('/finance/daily_cash_position')
@login_required
def daily_cash_position():
    return render_template('daily_cash_position.html')

@app.route('/finance/loan_tracking')
@login_required
def loan_tracking():
    return render_template('loan_tracking.html')

@app.route('/finance/bank_deposits_withdrawals')
@login_required
def bank_deposits_withdrawals():
    return render_template('bank_deposits_withdrawals.html')


from forms import BankAccountForm

@app.route('/bank_accounts', methods=['GET', 'POST'])
@login_required
def bank_accounts():
    form = BankAccountForm()

    if form.validate_on_submit():
        new_account = BankAccount(
            name=form.name.data,
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            account_type=form.account_type.data,
            currency=form.currency.data,
            opening_balance=form.opening_balance.data,
            chart_of_accounts=form.chart_of_accounts.data
        )
        db.session.add(new_account)
        db.session.commit()
        flash('Bank account added!', 'success')
        return redirect(url_for('bank_accounts'))

    accounts = BankAccount.query.all()

    # ✅ Serialize account data for Chart.js
    accounts_json = [
        {
            "name": acc.name,
            "bank_name": acc.bank_name,
            "account_number": acc.account_number,
            "account_type": acc.account_type,
            "currency": acc.currency,
            "opening_balance": float(acc.opening_balance),
            "chart_of_accounts": acc.chart_of_accounts,
            "created_at": acc.created_at.strftime('%Y-%m-%d') if acc.created_at else None
        }
        for acc in accounts
    ]

    return render_template(
        'bank_accounts.html',
        form=form,
        accounts=accounts,            # Used for table display
        accounts_json=accounts_json  # Used for JSON/Chart.js
    )

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    # ✅ Step 1: Check permission
    if not has_permission(current_user.role, 'create_user'):
        flash("⛔ You don't have permission to create users.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        phone_number = request.form['phone_number'].strip()
        role = request.form['role'].strip()
        admin_password = request.form['admin_password']

        # ✅ Step 2: Verify password of current admin
        if not current_user.verify_password(admin_password):
            flash("❌ Incorrect password for authorization.", "danger")
            return redirect(url_for('create_user'))

        # ✅ Step 3: Prevent role escalation to 'super_admin'
        if role == 'super_admin' and not current_user.is_super_admin():
            flash("⛔ You are not allowed to assign the 'super_admin' role.", "danger")
            return redirect(url_for('create_user'))

        # ✅ Step 4: Check for duplicate email
        if User.query.filter_by(email=email).first():
            flash("⚠️ Email already registered.", "warning")
            return redirect(url_for('create_user'))

        # ✅ Step 5: Generate secure random password
        random_password = ''.join(random.choices(string.ascii_letters + string.digits, k=10))

        # ✅ Step 6: Create unique username
        base_username = '.'.join(full_name.lower().split())
        username = base_username
        counter = 1
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1

        # ✅ Step 7: Create new user instance
        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone_number=phone_number,
            password_hash=generate_password_hash(random_password),
            role=role,
            email_confirmed=True,
            created_by=current_user.username
        )

        # ✅ Step 8: Save to DB
        db.session.add(new_user)
        db.session.commit()

        flash(f"✅ User '{username}' created successfully. Temporary password: {random_password}", "success")
        return redirect(url_for('dashboard'))

    # ✅ Render form if GET
    return render_template('create_user.html')

@app.route('/audit_logs')
@login_required
def audit_logs():
    if not has_permission(current_user.role, 'view_audit_logs'):
        flash("⛔ You are not authorized to view audit logs.", "danger")
        return redirect(url_for('dashboard'))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_logs.html', logs=logs)

@app.route('/verify_email/<token>')
def verify_email(token):
    user = User.verify_token(token, purpose='confirm')  # uses your model's staticmethod

    if not user:
        flash("⛔ This verification link is invalid or has expired.", "danger")
        return redirect(url_for('register'))

    if user.email_confirmed:
        flash("✅ Your email is already verified. Please log in.", "info")
        return redirect(url_for('login_page'))

    user.confirm_email()  # sets email_confirmed = True and email_confirmed_on = now
    db.session.commit()

    flash("🎉 Email verified successfully! You can now log in.", "success")
    return redirect(url_for('login_page'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        full_name = form.full_name.data.strip()
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        phone_number = form.phone_number.data.strip()
        password = form.password.data
        role = form.role.data or 'attendant'

        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("⚠️ Username or email already exists.", "danger")
            return redirect(url_for('register'))

        # Assign admin to the first user
        if User.query.count() == 0:
            role = 'admin'

        new_user = User(
            full_name=full_name,
            username=username,
            email=email,
            phone_number=phone_number,
            role=role
        )
        new_user.password = password  # use setter for password hash

        db.session.add(new_user)
        db.session.commit()

        # ✅ Send account confirmation email
        token = new_user.generate_token(purpose='confirm')
        send_verification_email(new_user.email, token)

        # ✅ Send Welcome Email with credentials
        try:
            msg = Message(
                subject="🎉 Welcome to RahaSoft!",
                recipients=[new_user.email]
            )
            msg.body = f"""
Hello {new_user.full_name},

🎉 Congratulations on registering with RahaSoft!

You're now part of a smart system designed to streamline your operations.

Here are your login credentials:
----------------------------------------
Username: {new_user.username}
Email: {new_user.email}
Password: {password}
----------------------------------------

You can log in using either your username or your email address.

🔐 Please keep this email confidential as it contains sensitive information. Do NOT share it with anyone.

We’re thrilled to have you onboard.

Warm regards,  
The RahaSoft Team
"""
            mail.send(msg)
        except Exception as e:
            print(f"[Email Error] Welcome email failed: {e}")
            flash("✅ Account created. Email confirmation sent, but welcome email failed.", "warning")
            return redirect(url_for('login_page'))

        flash("✅ Registration successful! Please check your email to confirm your account.", "success")
        return redirect(url_for('login_page'))

    return render_template('register.html', form=form)



from flask import render_template, request, redirect, url_for, flash
from flask_mail import Message
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from itsdangerous import SignatureExpired, BadSignature

# === RESET PASSWORD ROUTE ===
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    form = ResetPasswordForm()

    try:
        email = serializer.loads(token, salt='reset-password-salt', max_age=900)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid or expired token.", "danger")
            return redirect(url_for('forgot_password'))
    except (SignatureExpired, BadSignature):
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for('forgot_password'))

    if form.validate_on_submit():
        new_password = form.password.data
        # 🔒 HASH the password before saving
        user.password = generate_password_hash(new_password)
        db.session.commit()
        flash("Your password has been reset. You can now log in.", "success")
        return redirect(url_for('login'))  # Use your login route here

    return render_template('reset_password.html', form=form)

# === FORGOT PASSWORD ROUTE ===
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()

        if user:
            token = serializer.dumps(user.email, salt='reset-password-salt')
            send_reset_email(user.email, token)

        flash("A password reset link will be sent to your email if it's associated with a RahaSoft account. Check your inbox or spam folder.", "info")
        return redirect(url_for('forgot_password_confirmation'))

    return render_template('forgot_password.html', form=form)


# === RESET EMAIL FUNCTION ===
def send_reset_email(to_email, token):
    reset_url = url_for('reset_password', token=token, _external=True)
    subject = "Reset Your RahaSoft Password"

    body = f"""Hello,

We received a request to reset the password for your RahaSoft account.

Click the link below to reset your password:
{reset_url}

This link will expire in 1 hour for your security.

If you did not request this, you can safely ignore this email — no changes will be made to your account.

Sincerely,  
The RahaSoft Team  
support@rahasoft.app
"""

    msg = Message(subject=subject, recipients=[to_email], body=body, reply_to='support@rahasoft.app')
    mail.send(msg)
    app.logger.info(f"✅ Sent password reset email to {to_email}")


# === ACCOUNT CREATION EMAIL FUNCTION ===
def send_account_email(user_email, username, password):
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    APP_NAME = "RahaSoft"

    subject = f"{APP_NAME} - Your Account Details"
    body = f"""Hi {username},

Your account has been created successfully on {APP_NAME}.

Here are your login details:

📧 Username: {username}
🔒 Password: {password}

You can log in at: http://localhost:5000/login

Please change your password after logging in for security.

Regards,  
{APP_NAME} Team
"""

    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = user_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            app.logger.info(f"✅ Account email sent to {user_email}")
    except Exception as e:
        app.logger.error(f"❌ Failed to send account email to {user_email}: {e}")

@app.route('/make_admin')
def make_admin():
    user = User.query.filter_by(username='Bilford').first()
    if user:
        user.role = 'super_admin'
        db.session.commit()
        return f"{user.username} is now a super_admin"
    return "User not found"

@app.route('/forgot-password-confirmation')
def forgot_password_confirmation():
    return render_template('forgot_password_confirmation.html')

# -------------------- Dashboard --------------------
@app.route('/dashboard')
@login_required
@email_verified_required
def dashboard():
    # Import at the function level to avoid scope issues
    from models.user import User
    from models.product import Product
    
    # Check if user has a company registered
    user = User.query.filter_by(username=session['user']).first()
    show_company_modal = not (user and user.company_id)
    
    # Get company information for display
    current_company = None
    if user and user.company_id:
        current_company = Company.query.get(user.company_id)
    
    # Always show dashboard, but pass flag for company modal
    company_id = getattr(current_user, 'company_id', None) if user and user.company_id else None
    category_filter = request.args.get('category')
    low_stock = request.args.get('low_stock') == 'on'
    search_query = request.args.get('search', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    user_role = getattr(current_user, 'role', 'guest').strip().lower()
    cart = session.get('cart', {})
    cart_item_count = sum(cart.values())

    # ✅ HR Panel (unchanged)
    if user_role == 'hr':
        from collections import Counter

        staff_query = User.query.filter_by(company_id=company_id)
        if search_query:
            staff_query = staff_query.filter(
                db.or_(
                    User.username.ilike(f"%{search_query}%"),
                    User.email.ilike(f"%{search_query}%")
                )
            )

        staff_users = staff_query.all()
        role_counts = Counter([user.role for user in staff_users])
        recent_joiners = User.query.filter_by(company_id=company_id).order_by(User.id.desc()).limit(5).all()

        return render_template(
            "dashboard_modern.html",
            staff_users=staff_users,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission,
            total_staff=len(staff_users),
            role_counts=role_counts,
            recent_joiners=recent_joiners,
            search_query=search_query,
            current_company=current_company,
            show_company_modal=show_company_modal
        )

    # ✅ Sales Panel
    if user_role == 'sales':
        fast_movers = Product.query.filter_by(company_id=company_id).order_by(Product.sold.desc()).limit(12).all()
        labels = [p.product_name for p in fast_movers] if fast_movers else []
        quantities = [p.sold for p in fast_movers] if fast_movers else []
        return render_template(
            "dashboard_modern.html",
            fast_movers=fast_movers,
            labels=labels,
            quantities=quantities,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission,
            current_company=current_company,
            show_company_modal=show_company_modal
        )

    # ✅ Finance Panel
    if user_role == 'finance':
        all_products = Product.query.filter_by(company_id=company_id).all()
        top_value_products = sorted(all_products, key=lambda p: p.quantity * p.price, reverse=True)[:12]
        total_value = sum(p.quantity * p.price for p in all_products)
        total_profit = sum((p.price - p.cost_price) * p.quantity for p in all_products)
        unsold_products = [p for p in all_products if p.sold == 0]
        return render_template(
            "dashboard_modern.html",
            products=top_value_products,
            total_value=total_value,
            total_profit=total_profit,
            unsold_products=unsold_products,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission,
            current_company=current_company,
            show_company_modal=show_company_modal
        )

    # ✅ Auditor Panel
    if user_role == 'auditor':
        query = Product.query.filter_by(company_id=company_id)
        if category_filter:
            query = query.filter_by(category=category_filter)
        if low_stock:
            query = query.filter(Product.quantity < 5)
        if search_query:
            query = query.filter(Product.product_name.ilike(f"%{search_query}%"))

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        products = pagination.items
        categories = [c[0] for c in db.session.query(Product.category).filter_by(company_id=company_id).distinct()]
        all_products = Product.query.filter_by(company_id=company_id).all()

        total_stock = sum(p.quantity for p in all_products)
        total_value = sum(p.quantity * p.price for p in all_products)
        low_stock_count = sum(1 for p in all_products if p.quantity < 5)
        most_valuable = max(all_products, key=lambda p: p.quantity * p.price, default=None)
        total_profit = sum((p.price - p.cost_price) * p.quantity for p in all_products)

        labels = [p.product_name for p in products] if products else []
        quantities = [p.quantity for p in products] if products else []

        category_totals = {}
        for p in all_products:
            category_totals[p.category] = category_totals.get(p.category, 0) + (p.quantity * p.price)

        pie_labels = list(category_totals.keys())
        pie_values = list(category_totals.values())

        return render_template(
            "dashboard_modern.html",
            products=products,
            categories=categories,
            pagination=pagination,
            selected_category=category_filter,
            low_stock_checked=low_stock,
            search_query=search_query,
            labels=labels,
            quantities=quantities,
            pie_labels=pie_labels,
            pie_values=pie_values,
            most_valuable=most_valuable,
            total_profit=total_profit,
            total_stock=total_stock,
            total_value=total_value,
            low_stock_count=low_stock_count,
            cart_item_count=cart_item_count,
            user_role=user_role,
            page=page,
            total_pages=pagination.pages,
            has_permission=has_permission,
            current_company=current_company,
            show_company_modal=show_company_modal
        )

    # ✅ Default (Admin/Manager/SuperAdmin)
    query = Product.query.filter_by(company_id=company_id)
    if category_filter:
        query = query.filter_by(category=category_filter)
    if low_stock:
        query = query.filter(Product.quantity < 5)
    if search_query:
        query = query.filter(Product.product_name.ilike(f"%{search_query}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    categories = [c[0] for c in db.session.query(Product.category).filter_by(company_id=company_id).distinct()]
    all_products = Product.query.filter_by(company_id=company_id).all()

    total_stock = sum(p.quantity for p in all_products)
    total_value = sum(p.quantity * p.price for p in all_products)
    low_stock_count = sum(1 for p in all_products if p.quantity < 5)
    most_valuable = max(all_products, key=lambda p: p.quantity * p.price, default=None)
    total_profit = sum((p.price - p.cost_price) * p.quantity for p in all_products)

    labels = [p.product_name for p in products] if products else []
    quantities = [p.quantity for p in products] if products else []
    category_totals = {}
    for p in all_products:
        category_totals[p.category] = category_totals.get(p.category, 0) + (p.quantity * p.price)

    pie_labels = list(category_totals.keys())
    pie_values = list(category_totals.values())

    return render_template(
        "dashboard_modern.html",
        products=products,
        categories=categories,
        pagination=pagination,
        selected_category=category_filter,
        low_stock_checked=low_stock,
        search_query=search_query,
        cart_item_count=cart_item_count,
        user_role=user_role,
        page=page,
        total_pages=pagination.pages,
        has_permission=has_permission,
        labels=labels,
        quantities=quantities,
        pie_labels=pie_labels,
        pie_values=pie_values,
        most_valuable=most_valuable,
        total_profit=total_profit,
        total_stock=total_stock,
        total_value=total_value,
        low_stock_count=low_stock_count,
        current_company=current_company,
        show_company_modal=show_company_modal
    )
# (Removed duplicated/erroneous block that was outside any function)
from flask import request, redirect, url_for, flash
from flask_login import login_required, current_user
from models.product import Product
from models import db

@app.route('/new_product', methods=['POST'])
@login_required
def new_product():
    try:
        product = Product(
            product_code=request.form['product_code'],
            product_name=request.form['product_name'],
            category=request.form['category'],
            price=float(request.form['price']),
            cost_price=float(request.form['cost_price']),
            quantity=int(request.form['quantity']),
            description=request.form.get('description'),
            image_url=request.form.get('image_url'),
            average_rating=float(request.form.get('average_rating', 0)),
            reviews_count=int(request.form.get('reviews_count', 0)),
            company_id=current_user.company_id  # ✅ Assign to logged-in user's company
        )

        db.session.add(product)
        db.session.commit()
        flash("✅ Product added successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error adding product: {str(e)}", "danger")

    return redirect(url_for('dashboard'))

@app.route('/new_sale', methods=['GET', 'POST'])
@login_required
def new_sale():
    if not has_permission(current_user.role, 'make_sale'):
        flash("⛔ Access denied. You cannot process sales.", "danger")
        return redirect(url_for('hr_dashboard'))  # You can change this to any dashboard route

    products = Product.query.all()

    if request.method == 'POST':
        try:
            product_id = request.form.get('product_id')
            quantity = int(request.form.get('quantity'))
            customer_name = request.form.get('customer_name', '').strip() or "Walk-in"

            product = Product.query.get(product_id)
            if not product:
                flash("❌ Product not found.", "danger")
                return redirect(url_for('new_sale'))

            if quantity > product.quantity:
                flash("⚠️ Not enough stock available.", "warning")
                return redirect(url_for('new_sale'))

            # Calculate subtotal
            subtotal = quantity * product.price

            # Create and store sale record
            sale = Sale(
                product_id=product.id,
                product_name=product.product_name,
                quantity=quantity,
                price=product.price,
                subtotal=subtotal,
                customer_name=customer_name
            )
            db.session.add(sale)

            # Update product stock
            product.quantity -= quantity
            product.sold += quantity
            db.session.commit()

            flash(f"✅ Sale recorded for {product.product_name}", "success")
            log_action('create', 'sale', sale.id)
            return redirect(url_for('dashboard'))

        except Exception as e:
            flash(f"❌ Failed to record sale: {str(e)}", "danger")
            return redirect(url_for('new_sale'))

    return render_template('new_sale.html', products=products)

@app.route('/reports', methods=['GET'])
@login_required
def reports():
    if not has_permission(current_user.role, 'view_reports'):
        flash("⛔ You don't have permission to access Reports.", "danger")
        return redirect(url_for('dashboard'))

    users = User.query.all()
    products = Product.query.all()

    # Get filter values from GET parameters
    user_id = request.args.get('user_id')
    product_id = request.args.get('product_id')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    sales_query = Sale.query

    if user_id:
        sales_query = sales_query.filter(Sale.user_id == user_id)
    if product_id:
        sales_query = sales_query.filter(Sale.product_id == product_id)
    if start_date:
        sales_query = sales_query.filter(Sale.timestamp >= start_date)
    if end_date:
        sales_query = sales_query.filter(Sale.timestamp <= end_date)

    sales = sales_query.order_by(Sale.timestamp.desc()).all()

    total_revenue = sum(s.total_price for s in sales)
    total_profit = sum(s.total_price - (s.product.cost_price * s.quantity) for s in sales if s.product)

    return render_template('reports.html', users=users, products=products,
                           sales=sales, total_revenue=total_revenue, total_profit=total_profit)

@app.route('/bulk_action', methods=['POST'])
@login_required
def bulk_action():
    selected_ids = request.form.getlist('selected_products[]')
    
    if not selected_ids:
        flash("⚠️ No products selected.", "warning")
        return redirect(url_for('dashboard'))

    try:
        # Delete selected products from the database
        Product.query.filter(Product.id.in_(selected_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f"🗑️ Deleted {len(selected_ids)} product(s).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error deleting products: {str(e)}", "danger")
    
    return redirect(url_for('dashboard'))


@app.route('/kpi_dashboard')
@login_required
def kpi_dashboard():
    # Monthly revenue data
    sales = Sale.query.all()
    monthly_data = {}
    top_products = {}

    for sale in sales:
        month = sale.timestamp.strftime('%Y-%m')
        monthly_data[month] = monthly_data.get(month, 0) + sale.total_price

        pname = sale.product.product_name if sale.product else "Unknown"
        top_products[pname] = top_products.get(pname, 0) + sale.total_price

    monthly_labels = sorted(monthly_data.keys())
    monthly_revenue = [monthly_data[month] for month in monthly_labels]

    top_products_sorted = sorted(top_products.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template("kpi_dashboard.html",
                           labels=monthly_labels,
                           revenue=monthly_revenue,
                           top_products=top_products_sorted)

@app.route('/forecast')
@login_required
def forecast():
    if not has_permission(current_user.role, 'view_reports'):
        flash("⛔ You don't have permission to access Forecasting.", "danger")
        return redirect(url_for('dashboard'))

    # Get sales grouped by product and month
    sales = Sale.query.all()
    sales_data = {}

    for sale in sales:
        if not sale.product:
            continue
        product = sale.product.product_name
        month = sale.timestamp.strftime('%Y-%m')
        sales_data.setdefault(product, {}).setdefault(month, 0)
        sales_data[product][month] += sale.quantity

    # Forecast using average monthly sales
    forecast_data = []
    for product, monthly_sales in sales_data.items():
        months = sorted(monthly_sales.keys())
        sales_values = [monthly_sales[m] for m in months]
        avg_sales = sum(sales_values) / len(sales_values)
        forecast = round(avg_sales, 2)

        forecast_data.append({
            'product': product,
            'months_counted': len(sales_values),
            'avg_monthly_sales': avg_sales,
            'forecast_next_month': forecast
        })

    return render_template("forecast.html", forecast_data=forecast_data)

@app.route('/hr')
@login_required
def hr_dashboard():
    if not current_user.has_any_role('hr', 'admin', 'super_admin'):
        flash("⛔ Access denied. HR-only area.", "danger")
        return redirect(url_for('dashboard'))

    staff_users = User.query.all()
    return render_template('hr_dashboard.html', staff_users=staff_users)

@app.route('/payroll/new', methods=['GET', 'POST'])
@login_required
def new_payroll_record():
    if not has_permission(current_user.role, 'manage_payroll'):
        flash("⛔ You don't have permission to add payroll records.", "danger")
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        try:
            user_id = int(request.form['user_id'])
            salary = float(request.form['salary'])
            bonuses = float(request.form.get('bonuses', 0))
            deductions = float(request.form.get('deductions', 0))
            loan_balance = float(request.form.get('loan_balance', 0))

            record = PayrollRecord(
                user_id=user_id,
                salary=salary,
                bonuses=bonuses,
                deductions=deductions,
                loan_balance=loan_balance
            )
            db.session.add(record)
            db.session.commit()
            flash("✅ Payroll record added.", "success")
        except Exception as e:
            flash(f"❌ Error: {e}", "danger")

        return redirect(url_for('dashboard'))

    users = User.query.all()
    return render_template('new_payroll.html', users=users)

@app.route('/payroll_records')
@login_required
def payroll_records():
    payroll_list = PayrollRecord.query.order_by(PayrollRecord.date.desc()).all()
    return render_template('payroll_list.html', payroll_list=payroll_list, user_role=session.get('role'))
@app.route('/stock_management', methods=['GET'])
@login_required
def stock_management():
    products = Product.query.all()
    return render_template('stock_management.html', products=products)

@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    name = request.form['name']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    new_product = Product(name=name, quantity=quantity, price=price)
    db.session.add(new_product)
    db.session.commit()
    flash('Product added!', 'success')
    return redirect(url_for('stock_management'))

@app.route("/add_payroll", methods=["GET", "POST"])
@login_required
def add_payroll():
    if not has_permission(current_user.role, 'manage_users'):
        flash("⛔ You don't have permission to manage payroll.", "danger")
        return redirect(url_for('dashboard'))

    users = User.query.all()

    if request.method == "POST":
        user_id = request.form.get("user_id")
        salary = float(request.form.get("salary"))
        loan = float(request.form.get("loan") or 0.0)
        remarks = request.form.get("remarks")
        date = datetime.strptime(request.form.get("date"), "%Y-%m-%d")

        record = PayrollRecord(
            user_id=user_id,
            salary=salary,
            loan=loan,
            remarks=remarks,
            date=date
        )
        db.session.add(record)
        db.session.commit()
        flash("✅ Payroll record added successfully!", "success")
        return redirect(url_for("payroll_records"))

    return render_template("add_payroll.html", users=users)


@app.route('/admin-only')
@login_required
def admin_only_area():
    if not current_user.is_super_admin():
        flash("⛔ Only Super Admin can access this area.", "danger")
        return redirect(url_for('dashboard'))

    return render_template('admin_area.html')

# ------------------
@app.route('/sales')
@login_required
def sales_route():
    if not has_permission(current_user.role, 'view_sales'):
        flash("⛔ Access denied. You don’t have permission to view sales.", "danger")
        return redirect(url_for('dashboard'))

    fast_movers = Product.query.filter_by(company_id=current_user.company_id).order_by(Product.sold.desc()).limit(12).all()
    labels = [p.product_name for p in fast_movers]
    quantities = [p.sold for p in fast_movers]

    return render_template(
        'sales_dashboard.html',
        fast_movers=fast_movers,
        labels=labels,
        quantities=quantities
    )

@login_required
def sales_route():
    if not has_permission(current_user.role, 'view_sales'):
        flash("⛔ Access denied. You don’t have permission to view sales.", "danger")
        return redirect(url_for('dashboard'))

    fast_movers = Product.query.order_by(Product.sold.desc()).limit(12).all()
    labels = [p.product_name for p in fast_movers]
    quantities = [p.sold for p in fast_movers]

    return render_template(
        'sales_dashboard.html',
        fast_movers=fast_movers,
        labels=labels,
        quantities=quantities
    )

@app.route('/finance')
@login_required
def finance_dashboard():
    if current_user.role != 'finance':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    products = Product.query.all()
    total_value = sum(p.quantity * p.price for p in products)
    total_profit = sum((p.price - p.cost_price) * p.quantity for p in products)
    unsold_products = [p for p in products if p.sold == 0]
    return render_template('finance_dashboard.html', products=products, total_value=total_value, total_profit=total_profit, unsold_products=unsold_products)

@app.route('/supervisor')
@login_required
def supervisor_dashboard():
    if current_user.role != 'supervisor':
        flash("Access denied.", "danger")
        return redirect(url_for('dashboard'))

    return redirect(url_for('dashboard'))  # or a separate view if needed

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    user_role = current_user.role
    if user_role == 'supervisor':
        flash("⛔ Supervisors are not allowed to delete products.", "danger")
        return redirect(url_for('dashboard'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"✅ Product '{product.product_name}' has been deleted.", "success")
    return redirect(url_for('dashboard'))

@app.route('/download_forecast_csv')
@login_required
def download_forecast_csv():
    # Fetch forecast data again
    today = datetime.today()
    start_date = today.replace(day=1) - pd.DateOffset(months=5)
    sales = Sale.query.filter(Sale.timestamp >= start_date).all()

    sales_by_product_month = {}
    for sale in sales:
        if not sale.product:
            continue
        key = (sale.product.product_name, sale.timestamp.strftime('%Y-%m'))
        sales_by_product_month[key] = sales_by_product_month.get(key, 0) + sale.quantity

    product_monthly_totals = {}
    for (product, _), qty in sales_by_product_month.items():
        product_monthly_totals.setdefault(product, []).append(qty)

    rows = []
    for product, monthly_sales in product_monthly_totals.items():
        avg = sum(monthly_sales) / len(monthly_sales)
        forecast = round(avg)
        rows.append({
            'Product': product,
            'Months Counted': len(monthly_sales),
            'Avg Monthly Sales': round(avg, 2),
            'Forecast Next Month': forecast
        })

    df = pd.DataFrame(rows)
    csv_path = "forecast_report.csv"
    df.to_csv(csv_path, index=False)

    return send_file(csv_path, as_attachment=True)


# ✅ Route: Download Inventory
@app.route('/download_inventory')
@login_required
def download_inventory():
    try:
        data = Product.query.all()
        df = pd.DataFrame([{
            'Product Code': p.product_code,
            'Name': p.product_name,
            'Category': p.category,
            'Price': p.price,
            'Cost Price': p.cost_price,
            'Quantity': p.quantity,
            'Description': p.description
        } for p in data])
        file_path = "inventory_export.xlsx"
        df.to_excel(file_path, index=False)
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        flash(f"❌ Error downloading inventory: {str(e)}", "danger")
        return redirect(url_for('dashboard'))

# ✅ Route: Import Adidas CSV
@app.route('/import_adidas')
@login_required
@role_required('admin', 'super_admin', 'hr_manager')
def import_adidas():
    try:
        df = pd.read_csv('cleaned_adidas_products.csv')
        for _, row in df.iterrows():
            product_code = row['id'] if 'id' in row else row.get('product_code') or None
            if not product_code:
                continue
            existing = Product.query.filter_by(product_code=product_code).first()
            if not existing:
                new_product = Product(
                    product_code=product_code,
                    product_name=row.get('product_name', 'Unnamed'),
                    category=row.get('category', 'Uncategorized'),
                    price=float(row.get('price', 0)),
                    cost_price=float(row.get('cost_price', 0)),
                    quantity=int(row.get('quantity', 10)),
                    description=row.get('description', ''),
                    image_url=row.get('image_url', ''),
                    average_rating=float(row.get('average_rating', 0)),
                    reviews_count=int(row.get('reviews_count', 0))
                )
                db.session.add(new_product)
        db.session.commit()
        flash("✅ Adidas products imported successfully!", "success")
    except FileNotFoundError:
        flash("❌ File not found: cleaned_adidas_products.csv", "danger")
    except Exception as e:
        flash(f"❌ Import error: {str(e)}", "danger")
    return redirect(url_for('dashboard'))
# -------------------- Cart & Checkout --------------------

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    cart_items = []
    total = 0
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({'product': product, 'quantity': quantity, 'subtotal': subtotal})
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST', 'GET'])
@login_required
def add_to_cart(product_id):
    cart = session.get('cart', {})
    quantity = int(request.form.get('quantity', 1)) if request.method == 'POST' else 1

    product = Product.query.get_or_404(product_id)
    if product.quantity < quantity:
        flash(f"Cannot add {quantity} items. Only {product.quantity} left in stock.", "danger")
        return redirect(url_for('dashboard'))

    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    flash(f"Added {quantity} x {product.product_name} to cart.", "success")
    return redirect(url_for('dashboard'))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash("Item removed from cart.", "info")
    return redirect(url_for('cart'))

@app.route('/clear_cart')
@login_required
def clear_cart():
    session.pop('cart', None)
    flash("All items have been removed from the cart.", "info")
    return redirect(url_for('cart'))

@app.route('/checkout')
@login_required
def checkout():
    cart = session.get('cart', {})
    total = 0
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product and product.quantity >= quantity:
            subtotal = product.price * quantity
            total += subtotal
            sale = Sale(product_name=product.product_name,
                        quantity=quantity,
                        price=product.price,
                        subtotal=subtotal,
                        timestamp=datetime.utcnow(),
                        username=session.get('user'))
            db.session.add(sale)
            product.quantity -= quantity
        else:
            flash(f"Insufficient stock for {product.product_name}", "danger")
    db.session.commit()
    session.pop('cart', None)
    return render_template('checkout.html', total=total)

# -------------------- Sales --------------------

@app.route('/sales')
@login_required
@role_required('admin', 'manager')
def sales():
    all_sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    grouped_sales = {}
    total_profit = 0
    for sale in all_sales:
        grouped_sales.setdefault(sale.username, []).append(sale)
        total_profit += sale.subtotal
    return render_template('sales.html', grouped_sales=grouped_sales, total_profit=total_profit)

@app.route('/download_sales')
@login_required
@role_required('admin', 'manager')
def download_sales():
    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    data = []
    for sale in sales:
        product = Product.query.filter_by(product_name=sale.product_name).first()
        cost_price = product.cost_price if product else 0.0
        profit = (sale.price - cost_price) * sale.quantity
        data.append({
            "Product Name": sale.product_name,
            "Quantity Sold": sale.quantity,
            "Selling Price": sale.price,
            "Subtotal": sale.subtotal,
            "Username": sale.username,
            "Date": sale.timestamp.strftime('%Y-%m-%d %H:%M'),
            "Profit": profit
        })
    df = pd.DataFrame(data)
    filepath = 'sales_report_with_profit.xlsx'
    df.to_excel(filepath, index=False)
    return send_file(filepath, as_attachment=True)

@app.route('/sales_dashboard')
@login_required
def sales_dashboard():
    # Only allow roles with 'view_reports' or 'view_sales' permission
    if not has_permission(current_user.role, 'view_reports') and not has_permission(current_user.role, 'view_sales'):
        flash("⛔ You don’t have permission to view sales dashboard.", "danger")
        return redirect(url_for('hr_dashboard'))  # or whichever dashboard you want

    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    sales_by_user = {}
    sales_by_day = {}

    for sale in sales:
        sales_by_user.setdefault(sale.username, {'total': 0, 'count': 0})
        sales_by_user[sale.username]['total'] += sale.subtotal
        sales_by_user[sale.username]['count'] += sale.quantity

        date_key = sale.timestamp.strftime('%Y-%m-%d')
        sales_by_day[date_key] = sales_by_day.get(date_key, 0) + sale.subtotal

    return render_template(
        'sales_dashboard.html',
        sales_by_user=sales_by_user,
        sales_by_day=sales_by_day
    )


@app.route('/sales_report', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def sales_report():
    filtered_sales = []
    start_date = end_date = None
    total_profit = 0

    if request.method == 'POST':
        start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
        end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
        sales = Sale.query.filter(Sale.timestamp >= start_date, Sale.timestamp <= end_date).all()

        for sale in sales:
            product = Product.query.filter_by(product_name=sale.product_name).first()
            cost_price = product.cost_price if product else 0.0
            profit = (sale.price - cost_price) * sale.quantity
            total_profit += profit

            filtered_sales.append({
                'product_name': sale.product_name,
                'quantity': sale.quantity,
                'price': sale.price,
                'subtotal': sale.subtotal,
                'username': sale.username,
                'timestamp': sale.timestamp.strftime('%Y-%m-%d %H:%M'),
                'profit': profit
            })

        # ✅ Download report
        if 'download' in request.form:
            df = pd.DataFrame(filtered_sales)
            filepath = 'filtered_sales_report.xlsx'
            df.to_excel(filepath, index=False)
            return send_file(filepath, as_attachment=True)

    return render_template(
        'sales_report.html',
        sales=filtered_sales,
        start_date=start_date,
        end_date=end_date,
        total_profit=total_profit
    )
# -------------------- Run App --------------------
@app.route('/')
def landing_page():
    return render_template('welcome.html')

if __name__ == '__main__':
    app.run(debug=True)

