from flask import Flask, render_template, request, redirect, url_for, session, send_file, flash
from models.product import db, Product
import os
import pandas as pd
import numpy as np

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLite DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
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
