from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from models.product import db, Product
from models.user import User
from models.sale import Sale
from werkzeug.security import check_password_hash
import pandas as pd
import numpy as np
from datetime import datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Make 'zip' available in Jinja2 templates
app.jinja_env.globals.update(zip=zip)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.before_request
def create_tables():
    db.create_all()

# ---------- RBAC Decorators ----------
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

# ---------- Splash Page ----------
@app.route('/')
def splash():
    return render_template('splash.html')

# ---------- Welcome Page ----------
@app.route('/welcome')
@login_required
def welcome_page():
    username = session.get('user')
    return render_template('welcome.html', username=username)

# ---------- Login Page ----------
@app.route('/login', methods=['GET', 'POST'])
def login_page():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and user.verify_password(password):
            session['user'] = user.username
            session['role'] = user.role
            flash(f"Welcome to RahaSoft, {user.username}!", "success")
            return redirect(url_for('welcome_page'))  # Redirect to welcome screen
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

# ---------- Registration, Logout, Password Reset ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')

        if not username or not email or not password:
            flash("Please fill in all fields.", "warning")
            return redirect(url_for('register'))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "warning")
            return redirect(url_for('register'))
        if '@' not in email or '.' not in email:
            flash("Invalid email address.", "warning")
            return redirect(url_for('register'))

        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            flash("Username or Email already exists.", "danger")
            return redirect(url_for('register'))

        admin_exists = User.query.filter_by(role='admin').first()
        role = 'admin' if not admin_exists else 'attendant'

        new_user = User(username=username, email=email, role=role)
        new_user.password = password
        db.session.add(new_user)
        db.session.commit()

        flash(f"Registration successful. You have been registered as {role} with RahaSoft. You can now log in.", "success")
        return redirect(url_for('login_page'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out of RahaSoft.", "info")
    return redirect(url_for('login_page'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = f"token-{user.id}"
            user.reset_token = token
            db.session.commit()
            flash(f"Reset link: http://localhost:5000/reset_password/{token}", "info")
        else:
            flash("Email not found", "danger")
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user:
        flash("Invalid or expired token", "danger")
        return redirect(url_for('login_page'))

    if request.method == 'POST':
        new_password = request.form['password']
        user.password = new_password
        user.reset_token = None
        db.session.commit()
        flash("Password reset successful", "success")
        return redirect(url_for('login_page'))
    return render_template('reset_password.html')

# ---------- Inventory and Operations ----------
@app.route('/inventory')
@login_required
def inventory():
    category_filter = request.args.get('category')
    low_stock = request.args.get('low_stock') == 'on'
    page = request.args.get('page', 1, type=int)
    per_page = 12

    query = Product.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if low_stock:
        query = query.filter(Product.quantity < 5)

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
                           user_role=session.get('role'))

# ---------- Cart, Checkout ----------
@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash("Product added to cart", "success")
    return redirect(url_for('inventory'))

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

# ---------- Sales ----------
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

# ---------- Utilities ----------
@app.route('/import_adidas')
@login_required
@role_required('admin')
def import_adidas():
    try:
        df = pd.read_csv('cleaned_adidas_products.csv')
        df['price'] = pd.to_numeric(df['price'], errors='coerce')
        df['cost_price'] = df['price'] * 0.8
        df['quantity'] = np.random.randint(5, 50, size=len(df))
        df.dropna(subset=['product_name'], inplace=True)

        for _, row in df.iterrows():
            existing = Product.query.filter_by(product_code=row['product_code']).first()
            if not existing:
                product = Product(
                    product_code=row['product_code'],
                    product_name=row['product_name'],
                    category=row['category'],
                    price=row['price'],
                    cost_price=row['cost_price'],
                    quantity=row['quantity'],
                    description=row.get('description', ''),
                    image_url=row.get('image_url', ''),
                    average_rating=row.get('average_rating', 0),
                    reviews_count=row.get('reviews_count', 0)
                )
                db.session.add(product)

        db.session.commit()
        return "Adidas products imported successfully. <a href='/inventory'>Go to Inventory</a>"
    except Exception as e:
        return f"Import failed: {str(e)}"

@app.route('/add_product', methods=['POST'])
@login_required
@role_required('admin', 'manager')
def add_product():
    data = request.form
    product = Product(
        product_code=data.get('product_code'),
        product_name=data.get('product_name'),
        category=data.get('category'),
        price=float(data.get('price', 0)),
        cost_price=float(data.get('cost_price', 0)),
        quantity=int(data.get('quantity', 0)),
        description=data.get('description'),
        image_url=data.get('image_url'),
        average_rating=float(data.get('average_rating', 0)),
        reviews_count=int(data.get('reviews_count', 0))
    )
    db.session.add(product)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
@login_required
@role_required('admin', 'manager')
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        data = request.form
        product.product_name = data.get('product_name')
        product.category = data.get('category')
        product.price = float(data.get('price', 0))
        product.cost_price = float(data.get('cost_price', 0))
        product.quantity = int(data.get('quantity', 0))
        product.description = data.get('description')
        product.image_url = data.get('image_url')
        product.average_rating = float(data.get('average_rating', 0))
        product.reviews_count = int(data.get('reviews_count', 0))
        db.session.commit()
        return redirect(url_for('inventory'))
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:id>')
@login_required
@role_required('admin')
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('inventory'))

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
        if sale.username not in sales_by_user:
            sales_by_user[sale.username] = {'total': 0, 'count': 0}
        sales_by_user[sale.username]['total'] += sale.subtotal
        sales_by_user[sale.username]['count'] += sale.quantity

        date_key = sale.timestamp.strftime('%Y-%m-%d')
        if date_key not in sales_by_day:
            sales_by_day[date_key] = 0
        sales_by_day[date_key] += sale.subtotal

    return render_template('sales_dashboard.html',
                           sales_by_user=sales_by_user,
                           sales_by_day=sales_by_day)

if __name__ == '__main__':
    app.run(debug=True)
