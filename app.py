from flask import Flask, render_template, request, redirect, url_for, session
from models.product import db, Product
import os
from flask_sqlalchemy import SQLAlchemy
import pandas as pd

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

@app.before_request
def create_tables():
    db.create_all()

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] == 'admin' and request.form['password'] == 'admin':
            session['user'] = request.form['username']
            return redirect(url_for('inventory'))
        else:
            return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

@app.route('/inventory', methods=['GET'])
def inventory():
    if 'user' not in session:
        return redirect(url_for('login'))

    category_filter = request.args.get('category')
    low_stock = request.args.get('low_stock') == 'on'

    query = Product.query
    if category_filter:
        query = query.filter_by(category=category_filter)
    if low_stock:
        query = query.filter(Product.quantity < 5)

    products = query.all()

    # All categories for dropdown
    all_categories = db.session.query(Product.category).distinct().all()
    categories = [c[0] for c in all_categories]

    # Bar chart data
    labels = [p.name for p in products]
    quantities = [p.quantity for p in products]

    # Pie chart data (value per category)
    category_totals = {}
    for p in Product.query.all():
        total = p.quantity * p.price
        if p.category in category_totals:
            category_totals[p.category] += total
        else:
            category_totals[p.category] = total

    pie_labels = list(category_totals.keys())
    pie_values = list(category_totals.values())

    # Low stock items for banner
    low_stock_items = Product.query.filter(Product.quantity < 5).all()

    return render_template(
        'inventory.html',
        products=products,
        labels=labels,
        quantities=quantities,
        pie_labels=pie_labels,
        pie_values=pie_values,
        categories=categories,
        selected_category=category_filter,
        low_stock_checked=low_stock,
        low_stock_items=low_stock_items
    )

@app.route('/add_product', methods=['POST'])
def add_product():
    name = request.form['name']
    quantity = int(request.form['quantity'])
    price = float(request.form['price'])
    category = request.form['category']
    new_product = Product(name=name, quantity=quantity, price=price, category=category)
    db.session.add(new_product)
    db.session.commit()
    return redirect(url_for('inventory'))

@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    product = Product.query.get_or_404(id)
    if request.method == 'POST':
        product.name = request.form['name']
        product.quantity = int(request.form['quantity'])
        product.price = float(request.form['price'])
        product.category = request.form['category']
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
    data = [
        {
            'Name': p.name,
            'Quantity': p.quantity,
            'Price': p.price,
            'Category': p.category
        } for p in products
    ]
    df = pd.DataFrame(data)
    file_path = 'inventory_download.xlsx'
    df.to_excel(file_path, index=False)
    return redirect('/' + file_path)

if __name__ == '__main__':
    app.run(debug=True)
