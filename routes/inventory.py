from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from models.product import Product, StockMovement, Category, Supplier
from models.sale import Sale
from models.user import User
from models.company import Company
from forms.inventory_forms import (ProductForm, StockAdjustmentForm, CategoryForm, 
                                 SupplierForm, BulkUploadForm, InventorySearchForm)
from extensions import db
from datetime import datetime, timedelta
from sqlalchemy import func, and_, desc, or_
import csv
import io
import os
from werkzeug.utils import secure_filename
import pandas as pd

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

@inventory_bp.route('/')
@login_required
def dashboard():
    """Main inventory dashboard with key metrics"""
    company_id = current_user.company_id
    
    # Get basic inventory stats
    total_products = Product.query.filter_by(company_id=company_id, is_active=True).count()
    total_categories = Category.query.filter_by(company_id=company_id, is_active=True).count()
    total_suppliers = Supplier.query.filter_by(company_id=company_id, is_active=True).count()
    
    # Calculate inventory value
    products = Product.query.filter_by(company_id=company_id, is_active=True).all()
    total_inventory_value = sum(p.current_value() for p in products)
    
    # Low stock alerts
    low_stock_products = [p for p in products if p.is_low_stock()]
    
    # Out of stock products
    out_of_stock_products = [p for p in products if p.quantity <= 0]
    
    # Recent stock movements
    recent_movements = StockMovement.query.join(Product).filter(
        Product.company_id == company_id
    ).order_by(desc(StockMovement.created_at)).limit(10).all()
    
    # Top selling products (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_products = db.session.query(
        Product.id,
        Product.product_name,
        func.sum(Sale.quantity).label('total_sold')
    ).join(Sale).filter(
        Product.company_id == company_id,
        Sale.sale_date >= thirty_days_ago
    ).group_by(Product.id, Product.product_name).order_by(
        desc(func.sum(Sale.quantity))
    ).limit(5).all()
    
    # Category distribution
    category_stats = db.session.query(
        Category.name,
        func.count(Product.id).label('product_count'),
        func.sum(Product.quantity).label('total_quantity')
    ).join(Product, Category.name == Product.category).filter(
        Product.company_id == company_id,
        Product.is_active == True
    ).group_by(Category.name).all()
    
    return render_template('inventory/dashboard.html',
                         total_products=total_products,
                         total_categories=total_categories,
                         total_suppliers=total_suppliers,
                         total_inventory_value=total_inventory_value,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products,
                         recent_movements=recent_movements,
                         top_products=top_products,
                         category_stats=category_stats)

@inventory_bp.route('/products')
@login_required
def products():
    """List all products with search and filters"""
    form = InventorySearchForm()
    company_id = current_user.company_id
    
    # Base query
    query = Product.query.filter_by(company_id=company_id, is_active=True)
    
    # Apply filters
    if request.args.get('search'):
        search_term = f"%{request.args.get('search')}%"
        query = query.filter(or_(
            Product.product_name.ilike(search_term),
            Product.product_code.ilike(search_term),
            Product.barcode.ilike(search_term)
        ))
    
    if request.args.get('category'):
        query = query.filter(Product.category == request.args.get('category'))
    
    if request.args.get('stock_status'):
        status = request.args.get('stock_status')
        if status == 'out_of_stock':
            query = query.filter(Product.quantity <= 0)
        elif status == 'low_stock':
            # We'll filter this in Python since it involves custom logic
            pass
        elif status == 'in_stock':
            query = query.filter(Product.quantity > 0)
    
    if request.args.get('price_min'):
        query = query.filter(Product.price >= float(request.args.get('price_min')))
    
    if request.args.get('price_max'):
        query = query.filter(Product.price <= float(request.args.get('price_max')))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = 20
    products = query.order_by(Product.product_name).paginate(
        page=page, per_page=per_page, error_out=False)
    
    # Apply low stock filter if needed (post-query)
    if request.args.get('stock_status') == 'low_stock':
        low_stock_items = [p for p in products.items if p.is_low_stock()]
        # Note: This breaks pagination, but it's a simple solution
        products.items = low_stock_items
    
    return render_template('inventory/products.html', products=products, form=form)

@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add a new product"""
    form = ProductForm()
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            image_filename = None
            if form.image.data:
                image_filename = secure_filename(form.image.data.filename)
                upload_folder = os.path.join('static', 'uploads', 'products')
                os.makedirs(upload_folder, exist_ok=True)
                form.image.data.save(os.path.join(upload_folder, image_filename))
            
            # Create product
            product = Product(
                product_code=form.product_code.data,
                product_name=form.product_name.data,
                category=form.category.data or None,
                brand=form.brand.data,
                supplier=form.supplier.data or None,
                price=form.price.data,
                cost_price=form.cost_price.data,
                quantity=form.quantity.data,
                reorder_level=form.reorder_level.data,
                max_stock_level=form.max_stock_level.data,
                location=form.location.data,
                barcode=form.barcode.data,
                weight=form.weight.data,
                dimensions=form.dimensions.data,
                description=form.description.data,
                tax_rate=form.tax_rate.data,
                expiry_date=form.expiry_date.data,
                image_url=image_filename,
                is_active=form.is_active.data,
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            
            db.session.add(product)
            db.session.flush()  # Get the product ID
            
            # Create initial stock movement
            if form.quantity.data > 0:
                stock_movement = StockMovement(
                    product_id=product.id,
                    movement_type='initial_stock',
                    quantity_change=form.quantity.data,
                    quantity_after=form.quantity.data,
                    unit_cost=form.cost_price.data,
                    reference='Initial Stock',
                    notes='Initial product stock entry',
                    created_by=current_user.id
                )
                db.session.add(stock_movement)
            
            db.session.commit()
            flash(f'Product "{product.product_name}" added successfully!', 'success')
            return redirect(url_for('inventory.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    
    return render_template('inventory/add_product.html', form=form)

@inventory_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """View product details"""
    product = Product.query.filter_by(
        id=product_id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    # Get stock movements
    movements = StockMovement.query.filter_by(
        product_id=product_id
    ).order_by(desc(StockMovement.created_at)).limit(20).all()
    
    # Get recent sales
    recent_sales = Sale.query.filter_by(
        product_id=product_id,
        company_id=current_user.company_id
    ).order_by(desc(Sale.sale_date)).limit(10).all()
    
    # Calculate analytics
    analytics = {
        'total_sold_30_days': product.total_sold_last_30_days(),
        'turnover_rate': product.turnover_rate(),
        'profit_margin': product.profit_margin(),
        'current_value': product.current_value(),
        'is_low_stock': product.is_low_stock(),
        'days_until_expiry': product.days_until_expiry() if product.expiry_date else None
    }
    
    return render_template('inventory/product_detail.html', 
                         product=product, 
                         movements=movements,
                         recent_sales=recent_sales,
                         analytics=analytics)

@inventory_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit an existing product"""
    product = Product.query.filter_by(
        id=product_id, 
        company_id=current_user.company_id
    ).first_or_404()
    
    form = ProductForm(obj=product)
    form.product_id = product_id  # For validation
    
    if form.validate_on_submit():
        try:
            # Handle file upload
            if form.image.data:
                image_filename = secure_filename(form.image.data.filename)
                upload_folder = os.path.join('static', 'uploads', 'products')
                os.makedirs(upload_folder, exist_ok=True)
                form.image.data.save(os.path.join(upload_folder, image_filename))
                product.image_url = image_filename
            
            # Update product
            form.populate_obj(product)
            product.updated_at = datetime.utcnow()
            
            db.session.commit()
            flash(f'Product "{product.product_name}" updated successfully!', 'success')
            return redirect(url_for('inventory.product_detail', product_id=product_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
    
    return render_template('inventory/edit_product.html', form=form, product=product)

@inventory_bp.route('/stock/adjust', methods=['GET', 'POST'])
@login_required
def adjust_stock():
    """Adjust stock levels"""
    form = StockAdjustmentForm()
    
    if form.validate_on_submit():
        try:
            product = Product.query.filter_by(
                id=form.product_id.data,
                company_id=current_user.company_id
            ).first_or_404()
            
            old_quantity = product.quantity
            adjustment_type = form.adjustment_type.data
            adjustment_quantity = form.quantity.data
            
            # Calculate new quantity
            if adjustment_type == 'add':
                new_quantity = old_quantity + adjustment_quantity
                quantity_change = adjustment_quantity
            elif adjustment_type == 'remove':
                new_quantity = max(0, old_quantity - adjustment_quantity)
                quantity_change = -(old_quantity - new_quantity)
            else:  # set
                new_quantity = adjustment_quantity
                quantity_change = new_quantity - old_quantity
            
            # Update product quantity
            product.quantity = new_quantity
            product.updated_at = datetime.utcnow()
            
            # Create stock movement record
            movement = StockMovement(
                product_id=product.id,
                movement_type=f'adjustment_{adjustment_type}',
                quantity_change=quantity_change,
                quantity_after=new_quantity,
                unit_cost=form.unit_cost.data,
                reference=form.reference.data,
                notes=form.notes.data,
                created_by=current_user.id
            )
            
            db.session.add(movement)
            db.session.commit()
            
            flash(f'Stock adjusted for "{product.product_name}". New quantity: {new_quantity}', 'success')
            return redirect(url_for('inventory.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adjusting stock: {str(e)}', 'error')
    
    return render_template('inventory/adjust_stock.html', form=form)

@inventory_bp.route('/categories')
@login_required
def categories():
    """List all categories"""
    categories = Category.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).order_by(Category.name).all()
    
    return render_template('inventory/categories.html', categories=categories)

@inventory_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    """Add a new category"""
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            category = Category(
                name=form.name.data,
                description=form.description.data,
                parent_id=form.parent_id.data if form.parent_id.data else None,
                is_active=form.is_active.data,
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            
            db.session.add(category)
            db.session.commit()
            
            flash(f'Category "{category.name}" added successfully!', 'success')
            return redirect(url_for('inventory.categories'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding category: {str(e)}', 'error')
    
    return render_template('inventory/add_category.html', form=form)

@inventory_bp.route('/suppliers')
@login_required
def suppliers():
    """List all suppliers"""
    suppliers = Supplier.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).order_by(Supplier.name).all()
    
    return render_template('inventory/suppliers.html', suppliers=suppliers)

@inventory_bp.route('/suppliers/add', methods=['GET', 'POST'])
@login_required
def add_supplier():
    """Add a new supplier"""
    form = SupplierForm()
    
    if form.validate_on_submit():
        try:
            supplier = Supplier(
                name=form.name.data,
                contact_person=form.contact_person.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
                city=form.city.data,
                state=form.state.data,
                country=form.country.data,
                postal_code=form.postal_code.data,
                tax_id=form.tax_id.data,
                payment_terms=form.payment_terms.data,
                credit_limit=form.credit_limit.data,
                rating=form.rating.data,
                notes=form.notes.data,
                is_active=form.is_active.data,
                company_id=current_user.company_id,
                created_by=current_user.id
            )
            
            db.session.add(supplier)
            db.session.commit()
            
            flash(f'Supplier "{supplier.name}" added successfully!', 'success')
            return redirect(url_for('inventory.suppliers'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding supplier: {str(e)}', 'error')
    
    return render_template('inventory/add_supplier.html', form=form)

@inventory_bp.route('/reports')
@login_required
def reports():
    """Inventory reports and analytics"""
    company_id = current_user.company_id
    
    # Low stock report
    low_stock_products = Product.query.filter_by(
        company_id=company_id, 
        is_active=True
    ).all()
    low_stock_products = [p for p in low_stock_products if p.is_low_stock()]
    
    # Inventory valuation by category
    category_valuation = db.session.query(
        Product.category,
        func.sum(Product.quantity * Product.cost_price).label('total_cost_value'),
        func.sum(Product.quantity * Product.price).label('total_selling_value'),
        func.count(Product.id).label('product_count')
    ).filter(
        Product.company_id == company_id,
        Product.is_active == True,
        Product.category.isnot(None)
    ).group_by(Product.category).all()
    
    # Stock movement summary (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    stock_movements = db.session.query(
        StockMovement.movement_type,
        func.count(StockMovement.id).label('count'),
        func.sum(StockMovement.quantity_change).label('total_quantity')
    ).join(Product).filter(
        Product.company_id == company_id,
        StockMovement.created_at >= thirty_days_ago
    ).group_by(StockMovement.movement_type).all()
    
    return render_template('inventory/reports.html',
                         low_stock_products=low_stock_products,
                         category_valuation=category_valuation,
                         stock_movements=stock_movements)

@inventory_bp.route('/export/products')
@login_required
def export_products():
    """Export products to CSV"""
    products = Product.query.filter_by(
        company_id=current_user.company_id,
        is_active=True
    ).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        'Product Code', 'Product Name', 'Category', 'Brand', 'Supplier',
        'Price', 'Cost Price', 'Quantity', 'Reorder Level', 'Location',
        'Barcode', 'Weight', 'Dimensions', 'Description', 'Tax Rate',
        'Expiry Date', 'Created Date'
    ])
    
    # Write product data
    for product in products:
        writer.writerow([
            product.product_code,
            product.product_name,
            product.category or '',
            product.brand or '',
            product.supplier or '',
            product.price,
            product.cost_price or '',
            product.quantity,
            product.reorder_level,
            product.location or '',
            product.barcode or '',
            product.weight or '',
            product.dimensions or '',
            product.description or '',
            product.tax_rate,
            product.expiry_date.strftime('%Y-%m-%d') if product.expiry_date else '',
            product.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])
    
    output.seek(0)
    
    # Create response
    response = send_file(
        io.BytesIO(output.getvalue().encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'products_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )
    
    return response

@inventory_bp.route('/api/product/<int:product_id>/stock-chart')
@login_required
def product_stock_chart(product_id):
    """API endpoint for product stock level chart data"""
    product = Product.query.filter_by(
        id=product_id,
        company_id=current_user.company_id
    ).first_or_404()
    
    # Get stock movements for the last 90 days
    ninety_days_ago = datetime.utcnow() - timedelta(days=90)
    movements = StockMovement.query.filter(
        StockMovement.product_id == product_id,
        StockMovement.created_at >= ninety_days_ago
    ).order_by(StockMovement.created_at).all()
    
    # Build chart data
    chart_data = []
    for movement in movements:
        chart_data.append({
            'date': movement.created_at.strftime('%Y-%m-%d'),
            'quantity': movement.quantity_after,
            'movement_type': movement.movement_type
        })
    
    return jsonify(chart_data)

@inventory_bp.route('/api/dashboard/metrics')
@login_required
def dashboard_metrics():
    """API endpoint for dashboard metrics"""
    company_id = current_user.company_id
    
    # Calculate key metrics
    total_products = Product.query.filter_by(company_id=company_id, is_active=True).count()
    
    products = Product.query.filter_by(company_id=company_id, is_active=True).all()
    total_value = sum(p.current_value() for p in products)
    low_stock_count = len([p for p in products if p.is_low_stock()])
    out_of_stock_count = len([p for p in products if p.quantity <= 0])
    
    return jsonify({
        'total_products': total_products,
        'total_value': round(total_value, 2),
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count
    })
