from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from models import user
from models.product import db, Product
from models.user import User
from models.sale import Sale
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
import os
import pandas as pd
import numpy as np
from datetime import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Serializer for reset token
s = URLSafeTimedSerializer(app.secret_key)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            session['user'] = user.username
            return redirect(url_for('inventory'))
        else:
            flash("Invalid credentials", "danger")
    return render_template('login.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if user:
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)

            # Send Email
            sender = "bilfordderek917@gmail.com"
            receiver = email
            subject = "Smart Inventory - Password Reset"
            message = f"Hello,\n\nClick the link to reset your password:\n{reset_link}\n\nIf you did not request this, ignore this email."

            try:
                smtp_server = "smtp.gmail.com"
                smtp_port = 587
                smtp_user = "bilfordderek917@gmail.com"
                smtp_pass = "your_app_password"  # Replace this with actual app password

                msg = MIMEMultipart()
                msg['From'] = sender
                msg['To'] = receiver
                msg['Subject'] = subject
                msg.attach(MIMEText(message, 'plain'))

                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
                server.quit()

                flash("Reset link sent! Check your email.", "success")
            except Exception as e:
                flash("Email failed to send. Check SMTP setup.", "danger")
        else:
            flash("Email not found.", "warning")
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)
    except Exception:
        flash("Invalid or expired token", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        user = User.query.filter_by(email=email).first()
        new_password = request.form['password']
        if user:
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash("Password reset successful. Please log in.", "success")
            return redirect(url_for('login'))
    return render_template('reset_password.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('cart', None)
    return redirect(url_for('login'))

@app.route('/inventory')
def inventory():
    if 'user' not in session:
        return redirect(url_for('login'))

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

    return render_template('inventory.html', products=products, labels=labels,
                           quantities=quantities, pie_labels=pie_labels,
                           pie_values=pie_values, categories=categories,
                           selected_category=category_filter,
                           low_stock_checked=low_stock,
                           most_valuable=most_valuable,
                           total_profit=total_profit,
                           page=page,
                           total_pages=pagination.pages)

@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart[str(product_id)] = cart.get(str(product_id), 0) + 1
    session['cart'] = cart
    flash("Product added to cart", "success")
    return redirect(url_for('inventory'))

@app.route('/cart')
def cart():
    if 'user' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    cart_items = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            subtotal = product.price * quantity
            total += subtotal
            cart_items.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })

    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/checkout')
def checkout():
    if 'user' not in session:
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product and product.quantity >= quantity:
            subtotal = product.price * quantity
            total += subtotal

            sale = Sale(
                product_name=product.product_name,
                quantity=quantity,
                price=product.price,
                subtotal=subtotal,
                timestamp=datetime.utcnow()
            )
            db.session.add(sale)
            product.quantity -= quantity
        else:
            flash(f"Insufficient stock for {product.product_name}", "danger")

    db.session.commit()
    session.pop('cart', None)

    return render_template('checkout.html', total=total)

@app.route('/sales')
def sales():
    if 'user' not in session:
        return redirect(url_for('login'))

    sales = Sale.query.order_by(Sale.timestamp.desc()).all()
    return render_template('sales.html', sales=sales)

@app.route('/import_adidas')
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
def delete_product(id):
    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/download_inventory')
def download_inventory():
    products = Product.query.all()
    data = [p.to_dict() for p in products]
    df = pd.DataFrame(data)
    filepath = 'inventory_download.xlsx'
    df.to_excel(filepath, index=False)
    return send_file(filepath, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
