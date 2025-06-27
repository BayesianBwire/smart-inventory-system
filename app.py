from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_wtf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import db, User, Product, Sale, LoginLog
from models.audit_log import AuditLog
import random
import string
from models.product import Product
from models.login_log import LoginLog  # 👈 Make sure this import exists
from models.user import User
from models.sale import Sale
from werkzeug.security import generate_password_hash
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from functools import wraps
from dotenv import load_dotenv
import os
from forms import ProductForm
from forms import LoginForm, RegisterForm, ForgotPasswordForm, ResetPasswordForm, ProductForm
from flask_login import LoginManager, login_user, logout_user, current_user, login_required as flask_login_required
from sqlalchemy.exc import SQLAlchemyError
import smtplib
from flask import session, redirect, request, url_for
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_migrate import Migrate
from forms import RegisterForm, ForgotPasswordForm
from utils.permissions import has_permission
from flask_login import login_required, current_user

load_dotenv()

app = Flask(__name__)
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
                return redirect(url_for('inventory'))
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

@app.route('/set_language/<lang_code>')
def set_language(lang_code):
    supported_langs = ['en', 'fr', 'es', 'de', 'sw']
    if lang_code in supported_langs:
        session['lang'] = lang_code
    # Redirect back to where user came from or inventory page as fallback
    next_url = request.referrer or url_for('inventory')
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
        username = form.username.data.strip()
        password = form.password.data.strip()
        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            login_user(user)
            session['user'] = user.username
            session['email'] = user.email
            session['role'] = user.role

            # Add login log here...

            flash(f"Welcome back, {user.username}!", "success")
            return redirect(url_for('inventory'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('login.html', form=form)

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
    return redirect(url_for('welcome.html'))

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
def create_user():
    # ✅ Step 1: Check permission
    if not has_permission(current_user.role, 'create_user'):
        flash("⛔ You don't have permission to create users.", "danger")
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

    # ✅ Render form if GET
    return render_template('create_user.html')

@app.route('/audit_logs')
@login_required
def audit_logs():
    if not has_permission(current_user.role, 'view_audit_logs'):
        flash("⛔ You are not authorized to view audit logs.", "danger")
        return redirect(url_for('inventory'))

    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).all()
    return render_template('audit_logs.html', logs=logs)

@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify-salt', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.email_confirmed = True
            db.session.commit()
            flash("Email verified successfully. You can now log in.", "success")
            return redirect(url_for('welcome.html'))
        else:
            flash("Invalid or expired token.", "danger")
            return redirect(url_for('register'))
    except Exception as e:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for('register'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        full_name = form.full_name.data.strip()
        username = form.username.data.strip()
        email = form.email.data.strip()
        phone_number = form.phone_number.data.strip()
        password = form.password.data
        role = form.role.data or 'attendant'

        # Check if user exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            flash("⚠️ Username or email already exists.", "danger")
            return redirect(url_for('register'))

        # Assign first user as admin
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

        flash("✅ Registration successful!", "success")
        return redirect(url_for('login_page'))

    return render_template('register.html', form=form)



@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, salt='reset-password-salt', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if not user:
            flash("Invalid or expired token.", "danger")
            return redirect(url_for('forgot_password'))
    except (SignatureExpired, BadSignature):
        flash("The password reset link is invalid or has expired.", "danger")
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('password')
        if new_password:
            user.password = new_password
            db.session.commit()
            flash("Your password has been reset. You can now log in.", "success")
            return redirect(url_for('welcome.html'))
        else:
            flash("Please enter a new password.", "warning")

    return render_template('reset_password.html')

def send_account_email(user_email, username, password):
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    APP_NAME = "RahaSoft"

    subject = f"{APP_NAME} - Your Account Details"
    body = f"""
Hi {username},

Your account has been created successfully on {APP_NAME}.

Here are your login details:

📧 Username: {username}
🔒 Password: {password}

You can log in at: http://localhost:5000/login

Make sure to change your password after logging in.

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


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = serializer.dumps(user.email, salt='reset-password-salt')
            # You could call a send_reset_email() function here
            send_reset_email(user.email, token)
            flash("Password reset instructions have been sent to your email.", "info")
        else:
            flash("Email not found.", "danger")
        return redirect(url_for('welcome.html'))

    return render_template('forgot_password.html', form=form)

@app.route('/make_admin')
def make_admin():
    user = User.query.filter_by(username='Bilford').first()
    if user:
        user.role = 'super_admin'
        db.session.commit()
        return f"{user.username} is now a super_admin"
    return "User not found"

# -------------------- Inventory --------------------
@app.route('/inventory')
@login_required
def inventory():
    if not has_permission(current_user.role, 'view_inventory'):
        flash("⛔ You don't have permission to view inventory.", "danger")
        return redirect(url_for('home'))

    company_id = current_user.company_id  # 🏢 Multi-tenant filter
    category_filter = request.args.get('category')
    low_stock = request.args.get('low_stock') == 'on'
    search_query = request.args.get('search', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    user_role = current_user.role.strip().lower()
    cart = session.get('cart', {})
    cart_item_count = sum(cart.values())

    from models.product import Product

    # ✅ HR Panel (unchanged)
    if user_role == 'hr':
        from models.user import User
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
            "inventory_hr.html",
            staff_users=staff_users,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission,
            total_staff=len(staff_users),
            role_counts=role_counts,
            recent_joiners=recent_joiners,
            search_query=search_query
        )

    # ✅ Sales Panel
    if user_role == 'sales':
        fast_movers = Product.query.filter_by(company_id=company_id).order_by(Product.sold.desc()).limit(12).all()
        labels = [p.product_name for p in fast_movers] if fast_movers else []
        quantities = [p.sold for p in fast_movers] if fast_movers else []
        return render_template(
            "inventory_sales.html",
            fast_movers=fast_movers,
            labels=labels,
            quantities=quantities,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission
        )

    # ✅ Finance Panel
    if user_role == 'finance':
        all_products = Product.query.filter_by(company_id=company_id).all()
        top_value_products = sorted(all_products, key=lambda p: p.quantity * p.price, reverse=True)[:12]
        total_value = sum(p.quantity * p.price for p in all_products)
        total_profit = sum((p.price - p.cost_price) * p.quantity for p in all_products)
        unsold_products = [p for p in all_products if p.sold == 0]
        return render_template(
            "inventory_finance.html",
            products=top_value_products,
            total_value=total_value,
            total_profit=total_profit,
            unsold_products=unsold_products,
            cart_item_count=cart_item_count,
            user_role=user_role,
            has_permission=has_permission
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
            "inventory_auditor.html",
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
            has_permission=has_permission
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
        "inventory.html",
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
        low_stock_count=low_stock_count
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

    return redirect(url_for('inventory'))

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
            return redirect(url_for('inventory'))

        except Exception as e:
            flash(f"❌ Failed to record sale: {str(e)}", "danger")
            return redirect(url_for('new_sale'))

    return render_template('new_sale.html', products=products)

@app.route('/reports', methods=['GET'])
@login_required
def reports():
    if not has_permission(current_user.role, 'view_reports'):
        flash("⛔ You don't have permission to access Reports.", "danger")
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

    try:
        # Delete selected products from the database
        Product.query.filter(Product.id.in_(selected_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f"🗑️ Deleted {len(selected_ids)} product(s).", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"❌ Error deleting products: {str(e)}", "danger")
    
    return redirect(url_for('inventory'))


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
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

    staff_users = User.query.all()
    return render_template('hr_dashboard.html', staff_users=staff_users)

@app.route('/payroll/new', methods=['GET', 'POST'])
@login_required
def new_payroll_record():
    if not has_permission(current_user.role, 'manage_payroll'):
        flash("⛔ You don't have permission to add payroll records.", "danger")
        return redirect(url_for('inventory'))

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

        return redirect(url_for('inventory'))

    users = User.query.all()
    return render_template('new_payroll.html', users=users)

@app.route('/payroll_records')
@login_required
def payroll_records():
    from models import PayrollRecord  # Ensure the model is imported
    payroll_list = PayrollRecord.query.order_by(PayrollRecord.date.desc()).all()
    return render_template('payroll_list.html', payroll_list=payroll_list, user_role=session.get('role'))

@app.route("/add_payroll", methods=["GET", "POST"])
@login_required
def add_payroll():
    if not has_permission(current_user.role, 'manage_users'):
        flash("⛔ You don't have permission to manage payroll.", "danger")
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

    return render_template('admin_area.html')

# ------------------
@app.route('/sales')
@login_required
def sales_route():
    if not has_permission(current_user.role, 'view_sales'):
        flash("⛔ Access denied. You don’t have permission to view sales.", "danger")
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

    return redirect(url_for('inventory'))  # or a separate view if needed
@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')  # or your main modules page

@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    user_role = current_user.role
    if user_role == 'supervisor':
        flash("⛔ Supervisors are not allowed to delete products.", "danger")
        return redirect(url_for('inventory'))

    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"✅ Product '{product.product_name}' has been deleted.", "success")
    return redirect(url_for('inventory'))

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
        return redirect(url_for('inventory'))

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
    return redirect(url_for('inventory'))
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
        return redirect(url_for('inventory'))

    cart[str(product_id)] = cart.get(str(product_id), 0) + quantity
    session['cart'] = cart
    flash(f"Added {quantity} x {product.product_name} to cart.", "success")
    return redirect(url_for('inventory'))

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
