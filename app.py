from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from flask_wtf import CSRFProtect
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from models import db
import random
import string
from models.product import Product
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
from flask_login import LoginManager, login_user, logout_user, current_user, login_required as flask_login_required
from sqlalchemy.exc import SQLAlchemyError
import smtplib
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
    return User.query.get(int(user_id))


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

def send_verification_email(user_email, token):
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    APP_NAME = "RahaSoft"

    verify_url = url_for('verify_email', token=token, _external=True)

    subject = f"{APP_NAME} - Verify Your Email"
    body = f"""
Hi,

Thank you for registering with {APP_NAME}.

Please verify your email address by clicking the link below:

{verify_url}

If you did not register, please ignore this email.

Regards,
{APP_NAME} Team
"""
def send_reset_email(user_email, token):
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    FROM_EMAIL = os.getenv('FROM_EMAIL')
    APP_NAME = "RahaSoft"

    reset_url = url_for('reset_password', token=token, _external=True)

    subject = f"{APP_NAME} - Password Reset Request"
    body = f"""
Hi,

We received a request to reset your password.

Click the link below to reset it (valid for 1 hour):

{reset_url}

If you didn't request a password reset, please ignore this email.

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
    except Exception as e:
        app.logger.error(f"Failed to send password reset email to {user_email}: {e}")


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
    except Exception as e:
        app.logger.error(f"Failed to send verification email to {user_email}: {e}")

# -------------------- Routes --------------------

@app.route('/')
def home():
    return render_template('splash.html')

@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            if not user.email_confirmed:
                flash("Please verify your email before logging in.", "warning")
                return redirect(url_for('login_page'))
            login_user(user)  # Flask-Login handles session
            flash(f"Welcome to RahaSoft, {user.username}!", "success")
            return redirect(url_for('welcome'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/welcome')
@login_required
def welcome():
    username = session.get('user', 'User')
    return render_template('welcome.html', username=username)

@app.route('/logout')
def logout():
    logout_user()
    flash("You have been logged out of RahaSoft.", "info")
    return redirect(url_for('login_page'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data.strip()
        email = form.email.data.strip().lower()
        password = form.password.data

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or Email already exists.", "danger")
            return redirect(url_for('register'))

        role = 'admin' if not User.query.filter_by(role='admin').first() else 'attendant'
        new_user = User(username=username, email=email, role=role, email_confirmed=False)
        new_user.password = password
        db.session.add(new_user)
        db.session.commit()

        token = serializer.dumps(new_user.email, salt='email-verify-salt')
        send_verification_email(new_user.email, token)

        flash(f"Registration successful. A verification email has been sent to {new_user.email}.", "success")
        return redirect(url_for('login_page'))

    return render_template('register.html', form=form)

from utils.permissions import has_permission  # Ensure this is imported at the top

@app.route('/create_user', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'superadmin', 'hr')  # ✅ HR included
def create_user():
    if request.method == 'POST':
        full_name = request.form['full_name'].strip()
        email = request.form['email'].strip().lower()
        phone = request.form['phone_number'].strip()
        role = request.form['role'].strip().lower()
        admin_password = request.form['admin_password']

        admin_user = User.query.filter_by(email=session.get('email')).first()

        if not admin_user or not admin_user.check_password(admin_password):
            flash("⚠️ Incorrect admin password!", "danger")
            return redirect(url_for('create_user'))

        if User.query.filter_by(email=email).first():
            flash("❗ Email already registered.", "warning")
            return redirect(url_for('create_user'))

        # You can auto-generate a password or ask for one
        default_password = "123456"
        hashed_pw = generate_password_hash(default_password)

        new_user = User(
            username=full_name.split()[0].lower(),
            full_name=full_name,
            email=email,
            phone_number=phone,
            role=role,
            password=hashed_pw
        )

        db.session.add(new_user)
        db.session.commit()
        flash(f"✅ User '{full_name}' created with role '{role}'.", "success")
        return redirect(url_for('create_user'))

    return render_template('create_user.html')


@app.route('/verify_email/<token>')
def verify_email(token):
    try:
        email = serializer.loads(token, salt='email-verify-salt', max_age=3600)
        user = User.query.filter_by(email=email).first()
        if user:
            user.email_confirmed = True
            db.session.commit()
            flash("Email verified successfully. You can now log in.", "success")
            return redirect(url_for('login_page'))
        else:
            flash("Invalid or expired token.", "danger")
            return redirect(url_for('register'))
    except Exception as e:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for('register'))

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
            return redirect(url_for('login_page'))
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
        return redirect(url_for('login_page'))

    return render_template('forgot_password.html', form=form)

# -------------------- Inventory --------------------

@app.route('/inventory')
@login_required
def inventory():
    category_filter = request.args.get('category')
    low_stock = request.args.get('low_stock') == 'on'
    search_query = request.args.get('search', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Product.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if low_stock:
        query = query.filter(Product.quantity < 5)
    if search_query:
        query = query.filter(Product.product_name.ilike(f"%{search_query}%"))

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    products = pagination.items
    categories = [c[0] for c in db.session.query(Product.category).distinct().all()]

    labels = [p.product_name for p in products]
    quantities = [p.quantity for p in products]
    category_totals = {}

    for p in Product.query:
        total = p.quantity * p.price
        category_totals[p.category] = category_totals.get(p.category, 0) + total

    pie_labels = list(category_totals.keys())
    pie_values = list(category_totals.values())
    all_products = Product.query.all()
    most_valuable = max(all_products, key=lambda p: p.quantity * p.price, default=None)
    total_profit = sum([(p.price - p.cost_price) * p.quantity for p in all_products])
    cart = session.get('cart', {})
    cart_item_count = sum(cart.values())

    return render_template('inventory.html',
                           products=products,
                           labels=labels,
                           quantities=quantities,
                           pie_labels=pie_labels,
                           pie_values=pie_values,
                           categories=categories,
                           selected_category=category_filter,
                           low_stock_checked=low_stock,
                           most_valuable=most_valuable,
                           total_profit=total_profit,
                           page=page,
                           total_pages=pagination.pages,
                           user_role=session.get('role'),
                           cart_item_count=cart_item_count)

@app.route('/new_product', methods=['GET', 'POST'])
@login_required
def new_product():
    if not has_permission(current_user.role, 'manage_inventory'):
        flash("⛔ You don't have permission to manage inventory.", "danger")
        return redirect(url_for('inventory'))

    if request.method == 'POST':
        codes = request.form.getlist('product_code')
        names = request.form.getlist('product_name')
        categories = request.form.getlist('category')
        cost_prices = request.form.getlist('cost_price')
        prices = request.form.getlist('price')
        quantities = request.form.getlist('quantity')
        descriptions = request.form.getlist('description')

        for i in range(len(codes)):
            try:
                code = codes[i].strip()
                name = names[i].strip()
                category = categories[i].strip()
                cost_price = float(cost_prices[i])
                price = float(prices[i])
                quantity = int(quantities[i])
                description = descriptions[i].strip() if descriptions[i] else ''

                product = Product.query.filter_by(product_code=code).first()
                if product:
                    product.quantity += quantity
                    product.price = price
                    product.cost_price = cost_price
                    flash(f"📦 Updated: {name}", "info")
                else:
                    new_product = Product(
                        product_code=code,
                        product_name=name,
                        category=category,
                        price=price,
                        cost_price=cost_price,
                        quantity=quantity,
                        description=description
                    )
                    db.session.add(new_product)
                    flash(f"✅ Added: {name}", "success")
            except Exception as e:
                flash(f"❌ Error with product at row {i+1}: {str(e)}", "danger")

        db.session.commit()
        return redirect(url_for('inventory'))

    return render_template('new_product.html')


@app.route('/import_adidas')
@login_required
@role_required('admin', 'superadmin', 'hr_manager')
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

@app.route('/download_inventory')
@login_required
@role_required('admin', 'manager')
def download_inventory():
    products = Product.query.all()
    data = [p.to_dict() for p in products]
    df = pd.DataFrame(data)
    filepath = 'inventory_download.xlsx'
    df.to_excel(filepath, index=False)
    return send_file(filepath, as_attachment=True)

@app.route('/sales_dashboard')
@login_required
@role_required('admin', 'manager')
def sales_dashboard():
    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    sales_by_user = {}
    sales_by_day = {}

    for sale in sales:
        sales_by_user.setdefault(sale.username, {'total': 0, 'count': 0})
        sales_by_user[sale.username]['total'] += sale.subtotal
        sales_by_user[sale.username]['count'] += sale.quantity

        date_key = sale.timestamp.strftime('%Y-%m-%d')
        sales_by_day[date_key] = sales_by_day.get(date_key, 0) + sale.subtotal

    return render_template('sales_dashboard.html',
                           sales_by_user=sales_by_user,
                           sales_by_day=sales_by_day)

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

        if 'download' in request.form:
            df = pd.DataFrame(filtered_sales)
            filepath = 'filtered_sales_report.xlsx'
            df.to_excel(filepath, index=False)
            return send_file(filepath, as_attachment=True)

    return render_template('sales_report.html',
                           sales=filtered_sales,
                           start_date=start_date,
                           end_date=end_date,
                           total_profit=total_profit)

# -------------------- Run App --------------------

if __name__ == '__main__':
    app.run(debug=True)
