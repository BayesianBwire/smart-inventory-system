# Core imports
import os
import pandas as pd
import numpy as np
import smtplib
import random
import string
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Flask imports
from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash, current_app, Blueprint
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, current_user, login_required as flask_login_required
from flask_migrate import Migrate
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from werkzeug.security import generate_password_hash

load_dotenv()

# Import your extensions correctly
from extensions import db, mail

# Local imports - After app initialization to avoid circular imports
# Import core models first (order matters for foreign keys)
from models.company import Company
from models.user import User
from models.login_log import LoginLog
from models.audit_log import AuditLog

# Import basic business models
from models import Product, Sale, BankAccount, Transaction, Payroll, Employee
from models.product import StockMovement, Category, Supplier
from models.sale import Sale
from models.contact import Contact

# Import CRM models
from models.crm import Lead, Customer, Opportunity, CRMActivity, CRMTask, CRMNote

# Import Finance models
from models.finance import (ChartOfAccounts, Invoice, InvoiceItem, Payment, Expense, 
                           ExpenseCategory, JournalEntry, BudgetPeriod, BudgetItem)
from models.finance_extended import (BankTransaction, TaxRate, 
                                   FinancialReport, RecurringTransaction, CashFlowCategory)

# Import enterprise features (these depend on Company model)
from models.security import TwoFactorAuth, LoginAttempt, SecuritySettings
from models.api_framework import APIKey, APIUsageLog, Webhook, DataImportJob, IntegrationConfig

# Import Business Intelligence models
try:
    from models.business_intelligence_enhanced import (
        Dashboard, DashboardWidget, Report, ReportExecution, 
        KPIDefinition, KPIValue, DataAlert, AlertNotification, 
        DataExport, AnalyticsSession
    )
    print("✅ Business Intelligence models imported")
except ImportError as e:
    print(f"⚠️ Business Intelligence models not available: {e}")

# Import Workflow & Automation models
try:
    from models.workflow_automation import (
        WorkflowTemplate, Workflow, WorkflowTask, WorkflowAction, WorkflowLog,
        ApprovalWorkflow, ProcessAutomation, AutomationExecution
    )
    print("✅ Workflow & Automation models imported")
except ImportError as e:
    print(f"⚠️ Workflow & Automation models not available: {e}")
# Import forms from the correct locations
from forms import ProductForm, LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm
from forms.company_form import CompanyForm
from forms.employee_form import EmployeeForm
from utils.permissions import has_permission
from utils.cache_manager import redis_manager

# Route imports
from routes.employee_routes import employee_bp
from routes.payroll_routes import payroll_bp
from routes.support import support_bp
from routes.user_routes import user_bp
from routes.finance import finance_bp  # Add finance blueprint

# Import advanced feature blueprints
try:
    from routes.rahasoft_routes import rahasoft_bp
    from routes.advanced_routes import advanced_bp
except ImportError as e:
    print(f"⚠️ Some advanced route modules not available: {e}")
    rahasoft_bp = None
    advanced_bp = None

# -------------------- Load Environment Variables --------------------
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(dotenv_path) and load_dotenv(dotenv_path):
    print(f"✅ .env loaded from: {dotenv_path}")
else:
    print("❌ Could not load .env file")

# -------------------- Flask App Configuration --------------------
app = Flask(__name__)

app.config['SECRET_KEY'] = os.getenv("SECRET_KEY", "fallback-secret-key")
database_url = os.getenv("SQLALCHEMY_DATABASE_URI")
# Add SSL mode only for PostgreSQL
if database_url and database_url.startswith('postgresql'):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url + "?sslmode=require"
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS", "False").lower() == "true"

# -------------------- Mail Config --------------------
app.config['MAIL_SERVER'] = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('SMTP_PORT', 587))
app.config['MAIL_USERNAME'] = os.getenv('SMTP_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('SMTP_PASSWORD')
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('FROM_EMAIL')

# -------------------- Session Settings --------------------
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.permanent_session_lifetime = timedelta(minutes=30)

# -------------------- Enterprise Configuration --------------------
# Redis Configuration for Caching
app.config['REDIS_URL'] = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# API Configuration
app.config['API_RATE_LIMIT'] = int(os.getenv('API_RATE_LIMIT', 1000))
app.config['API_RATE_LIMIT_PERIOD'] = int(os.getenv('API_RATE_LIMIT_PERIOD', 3600))

# Security Configuration
app.config['PASSWORD_MIN_LENGTH'] = int(os.getenv('PASSWORD_MIN_LENGTH', 8))
app.config['PASSWORD_REQUIRE_UPPER'] = os.getenv('PASSWORD_REQUIRE_UPPER', 'true').lower() == 'true'
app.config['PASSWORD_REQUIRE_LOWER'] = os.getenv('PASSWORD_REQUIRE_LOWER', 'true').lower() == 'true'
app.config['PASSWORD_REQUIRE_DIGITS'] = os.getenv('PASSWORD_REQUIRE_DIGITS', 'true').lower() == 'true'
app.config['PASSWORD_REQUIRE_SPECIAL'] = os.getenv('PASSWORD_REQUIRE_SPECIAL', 'true').lower() == 'true'

# 2FA Configuration
app.config['TOTP_ISSUER_NAME'] = os.getenv('TOTP_ISSUER_NAME', 'RahaSoft ERP')
app.config['BACKUP_CODES_COUNT'] = int(os.getenv('BACKUP_CODES_COUNT', 10))

# Company Configuration
app.config['COMPANY_NAME'] = os.getenv('COMPANY_NAME', 'RahaSoft ERP')

# -------------------- Initialize Extensions --------------------
db.init_app(app)
mail.init_app(app)
# Initialize Redis for caching
redis_manager.init_app(app)

migrate = Migrate(app, db)
csrf = CSRFProtect(app)

# -------------------- Login Manager Setup --------------------
login_manager = LoginManager()
login_manager.login_view = 'login_page'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------- Register Blueprints --------------------
app.register_blueprint(employee_bp, url_prefix='/employees')
app.register_blueprint(payroll_bp, url_prefix='/payroll')
app.register_blueprint(support_bp, url_prefix='/support')
app.register_blueprint(user_bp, url_prefix='/users')
app.register_blueprint(finance_bp)  # Register finance blueprint
print("✅ Finance module blueprint registered")

# Register inventory blueprint
try:
    from routes.inventory import inventory_bp
    app.register_blueprint(inventory_bp)
    print("✅ Inventory management blueprint registered")
except ImportError as e:
    print(f"❌ Inventory blueprint not found: {e}")

# Register CRM blueprint
try:
    from routes.crm import crm_bp
    app.register_blueprint(crm_bp)
    print("✅ CRM management blueprint registered")
except ImportError as e:
    print(f"❌ CRM blueprint not found: {e}")

# Register Business Intelligence blueprint
try:
    from routes.business_intelligence_routes import bi_bp
    app.register_blueprint(bi_bp)
    print("✅ Business Intelligence blueprint registered")
except ImportError as e:
    print(f"❌ Business Intelligence blueprint not found: {e}")

# Register Workflow & Automation blueprint
try:
    from routes.workflow_routes import workflow_bp
    app.register_blueprint(workflow_bp)
    print("✅ Workflow & Automation blueprint registered")
except ImportError as e:
    print(f"❌ Workflow & Automation blueprint not found: {e}")

# Register advanced feature blueprints if available
if rahasoft_bp:
    app.register_blueprint(rahasoft_bp)
    print("✅ RahaSoft advanced features blueprint registered")
if advanced_bp:
    app.register_blueprint(advanced_bp)
    print("✅ Advanced features blueprint registered")

# -------------------- Custom Login Required Decorator --------------------
def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login_page'))
            if role and current_user.role != role:
                flash('Access denied. Insufficient permissions.', 'error')
                return redirect(url_for('dashboard'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# -------------------- Helper Functions --------------------
def send_email(to_email, subject, body):
    """Send email using configured SMTP settings"""
    try:
        msg = Message(
            subject=subject,
            recipients=[to_email],
            body=body,
            sender=app.config['MAIL_DEFAULT_SENDER']
        )
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def generate_reset_token(user_id):
    """Generate password reset token"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(user_id, salt='password-reset-salt')

def verify_reset_token(token, expiration=3600):
    """Verify password reset token"""
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = serializer.loads(token, salt='password-reset-salt', max_age=expiration)
        return user_id
    except (BadSignature, SignatureExpired):
        return None

# -------------------- Context Processors --------------------

@app.context_processor
def inject_user():
    """Inject user-related context variables into templates"""
    return dict(current_user=current_user)

@app.context_processor
def utility_processor():
    """Inject utility functions into templates"""
    def _(text):
        """Translation function placeholder"""
        return text
    
    return dict(_=_)

# -------------------- Routes --------------------

@app.route('/')
def index():
    """Home page - redirects to login or dashboard based on authentication"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('welcome'))

@app.route('/welcome')
def welcome():
    """Welcome page for non-authenticated users"""
    return render_template('welcome.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    """Login page"""
    print(f"🔍 Login route accessed - Method: {request.method}")
    
    form = LoginForm()
    print(f"🔍 Form created: {form}")
    
    if request.method == 'POST':
        print(f"🔍 POST data received: {request.form}")
        print(f"🔍 Form validation: {form.validate_on_submit()}")
        
        if form.errors:
            print(f"🔍 Form errors: {form.errors}")
    
    if form.validate_on_submit():
        print("🔍 Form validation passed")
        username = form.username.data
        password = form.password.data
        print(f"🔍 Attempting login for: {username}")
        
        # Find user by username or email
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()
        
        print(f"🔍 User found: {user}")
        
        if user and user.verify_password(password):
            print("🔍 Password verified")
            # Check if user account is verified
            if not user.email_confirmed:
                print("🔍 Email not confirmed")
                flash('Please verify your email before logging in.', 'warning')
                return redirect(url_for('login_page'))
            
            # Log the login
            login_log = LoginLog(
                user_id=user.id,
                username=user.username,
                timestamp=datetime.utcnow(),
                ip_address=request.remote_addr,
                browser_info=request.headers.get('User-Agent')
            )
            db.session.add(login_log)
            db.session.commit()
            
            login_user(user)
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['company_id'] = user.company_id
            
            flash(f'Welcome back, {user.full_name}!', 'success')
            
            # Redirect based on user role
            if user.role == 'founder':
                return redirect(url_for('founder_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password.', 'error')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required()
def logout():
    """Logout user"""
    logout_user()
    session.clear()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('welcome'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page for joining existing companies"""
    form = RegisterForm()
    if form.validate_on_submit():
        try:
            # Check if company exists by unique ID
            company_id = form.company_id.data.upper()
            company = Company.query.filter_by(unique_id=company_id).first()
            
            if not company:
                flash('Invalid company ID. Please contact your company administrator.', 'error')
                return render_template('register.html', form=form)
            
            # Check if username or email already exists
            existing_user = User.query.filter(
                (User.username == form.username.data) | 
                (User.email == form.email.data)
            ).first()
            
            if existing_user:
                flash('Username or email already exists. Please choose a different one.', 'error')
                return render_template('register.html', form=form)
            
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data,
                full_name=form.full_name.data,
                role='employee',  # Default role for regular registration
                company_id=company.id,
                email_confirmed=False  # Requires email verification
            )
            user.password = form.password.data
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email (optional)
            flash(f'Registration successful! Welcome to {company.name}. Please contact your administrator to activate your account.', 'success')
            return redirect(url_for('login_page'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error during registration: {str(e)}', 'error')
    
    return render_template('register.html', form=form)

@app.route('/register_company', methods=['GET', 'POST'])
def register_company():
    """Company registration page"""
    form = CompanyForm()
    if form.validate_on_submit():
        try:
            # Create new company
            company = Company(
                name=form.name.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                country=form.country.data,
                postal_code=form.postal_code.data,
                website=form.website.data,
                description=form.description.data,
                industry=form.industry.data
            )
            
            # Generate unique company ID
            company.unique_id = Company.generate_unique_id()
            
            db.session.add(company)
            db.session.flush()  # Get the company ID
            
            # Create founder user
            founder = User(
                username=form.founder_username.data,
                email=form.founder_email.data,
                full_name=form.founder_name.data,
                role='founder',
                company_id=company.id,
                email_confirmed=True  # Founder is auto-verified
            )
            founder.password = form.founder_password.data
            
            db.session.add(founder)
            db.session.commit()
            
            # Auto-login the founder
            login_user(founder)
            session['user_id'] = founder.id
            session['username'] = founder.username
            session['role'] = founder.role
            session['company_id'] = founder.company_id
            
            flash(f'🎉 Welcome to RahaSoft ERP! Company "{company.name}" registered successfully! Company ID: {company.unique_id}', 'success')
            return redirect(url_for('dashboard'))  # Go directly to dashboard
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error registering company: {str(e)}', 'error')
    
    return render_template('register_company.html', form=form)

@app.route('/select_modules')
@login_required()
def select_modules():
    """Module selection page for companies"""
    if current_user.role != 'founder':
        flash('Access denied. Only company founders can select modules.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('select_modules.html')

@app.route('/founder_dashboard')
@login_required(role='founder')
def founder_dashboard():
    """Founder dashboard with company overview"""
    company = Company.query.get(current_user.company_id)
    
    # Get company statistics
    total_users = User.query.filter_by(company_id=current_user.company_id).count()
    total_products = Product.query.filter_by(company_id=current_user.company_id).count()
    recent_sales = Sale.query.filter_by(company_id=current_user.company_id).order_by(Sale.date_created.desc()).limit(5).all()
    
    return render_template('founder_dashboard.html',
                         company=company,
                         total_users=total_users,
                         total_products=total_products,
                         recent_sales=recent_sales)

@app.route('/dashboard')
@login_required()
def dashboard():
    """Main dashboard for regular users"""
    user_role = current_user.role
    company = Company.query.get(current_user.company_id) if current_user.company_id else None
    
    # Get basic statistics
    total_products = Product.query.filter_by(company_id=current_user.company_id).count() if current_user.company_id else 0
    recent_sales = Sale.query.filter_by(company_id=current_user.company_id).order_by(Sale.date_created.desc()).limit(5).all() if current_user.company_id else []
    
    return render_template('dashboard.html',
                         user_role=user_role,
                         company=company,
                         total_products=total_products,
                         recent_sales=recent_sales)

@app.route('/admin_dashboard')
@login_required(role='admin')
def admin_dashboard():
    """Admin dashboard with comprehensive system statistics"""
    # Get system-wide statistics
    total_companies = Company.query.count()
    total_users = User.query.count()
    
    # Get recent logins with error handling
    try:
        recent_logins = LoginLog.query.order_by(LoginLog.timestamp.desc()).limit(10).all()
    except Exception:
        recent_logins = []
    
    # Get user role distribution
    try:
        from sqlalchemy import func
        role_stats = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
        role_counts = {role: count for role, count in role_stats}
    except Exception:
        role_counts = {}
    
    # Calculate active sessions (simplified estimation)
    active_sessions = max(1, int(total_users * 0.3)) if total_users else 0
    
    return render_template('admin_dashboard.html',
                         total_companies=total_companies,
                         total_users=total_users,
                         recent_logins=recent_logins,
                         role_counts=role_counts,
                         active_sessions=active_sessions)

@app.route('/terms')
def terms():
    """Terms of service page"""
    return render_template('terms.html')

@app.route('/privacy')
def privacy():
    """Privacy policy page"""
    return render_template('privacy.html')

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    """Set language preference"""
    # Store language preference in session
    session['language'] = lang_code
    flash(f'Language set to {lang_code.upper()}', 'info')
    
    # Redirect back to the referring page or dashboard
    next_page = request.args.get('next')
    if next_page:
        return redirect(next_page)
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    """Forgot password page"""
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = generate_reset_token(user.id)
            
            # Send reset email
            reset_url = url_for('reset_password', token=token, _external=True)
            subject = "Password Reset Request - RahaSoft ERP"
            body = f"""
            Dear {user.full_name},
            
            You have requested a password reset. Click the link below to reset your password:
            
            {reset_url}
            
            This link will expire in 1 hour.
            
            If you did not request this reset, please ignore this email.
            
            Best regards,
            RahaSoft ERP Team
            """
            
            if send_email(email, subject, body):
                flash('Password reset instructions have been sent to your email.', 'info')
            else:
                flash('Error sending email. Please try again.', 'error')
        else:
            # Don't reveal if email exists or not for security
            flash('Password reset instructions have been sent to your email.', 'info')
        
        return redirect(url_for('login_page'))
    
    return render_template('forgot_password.html', form=form)

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Reset password with token"""
    user_id = verify_reset_token(token)
    if not user_id:
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('forgot_password'))
    
    user = User.query.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('login_page'))
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.password = form.password.data
        db.session.commit()
        flash('Your password has been reset successfully.', 'success')
        return redirect(url_for('login_page'))
    
    return render_template('reset_password.html', form=form)

# -------------------- Basic Module Routes --------------------
@app.route('/inventory/')
@login_required()
def inventory():
    """Inventory management module"""
    return render_template('modules/inventory.html', title='Inventory Management')

@app.route('/pos/')
@login_required()
def pos():
    """Point of Sale module"""
    return render_template('modules/pos.html', title='Point of Sale')

@app.route('/stock_management/')
@login_required()
def stock_management():
    """Stock management module"""
    return render_template('modules/inventory.html', title='Stock Management')

@app.route('/purchasing/')
@login_required()
def purchasing():
    """Purchasing module"""
    return render_template('modules/purchasing.html', title='Purchasing')

@app.route('/warehouse/')
@login_required()
def warehouse():
    """Warehouse management module"""
    return render_template('modules/warehouse.html', title='Warehouse Management')

@app.route('/order_management/')
@login_required()
def order_management():
    """Order management module"""
    return render_template('modules/orders.html', title='Order Management')

# -------------------- Error Handlers --------------------
@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('errors/500.html'), 500

# -------------------- Register Enterprise Blueprints --------------------
# Import and register blueprints after app configuration
try:
    from routes.security_routes import security_bp
    from routes.api_routes import api_bp
    
    app.register_blueprint(security_bp)
    app.register_blueprint(api_bp)
    
    print("✅ Enterprise blueprints registered successfully")
except ImportError as e:
    print(f"⚠️ Warning: Could not register enterprise blueprints: {e}")
except Exception as e:
    print(f"❌ Error registering enterprise blueprints: {e}")

# Register existing blueprints
try:
    from routes.finance import finance_bp
    from routes.crm import crm_bp
    
    # Check if already registered to avoid duplicate registration
    if not any(bp.name == 'finance' for bp in app.blueprints.values()):
        app.register_blueprint(finance_bp)
    
    if not any(bp.name == 'crm' for bp in app.blueprints.values()):
        app.register_blueprint(crm_bp)
        
    print("✅ Existing module blueprints verified")
except Exception as e:
    print(f"⚠️ Warning: Issue with existing blueprints: {e}")

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('errors/403.html'), 403

# -------------------- Application Startup --------------------
if __name__ == '__main__':
    with app.app_context():
        try:
            # Create tables if they don't exist
            db.create_all()
            print("✅ Database tables created successfully")
        except Exception as e:
            print(f"❌ Error creating database tables: {str(e)}")
    
    # Run the application
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    )
