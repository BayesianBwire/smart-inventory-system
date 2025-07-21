"""
Inventory Management Routes for RahaSoft ERP
Comprehensive business-ready inventory system with full functionality
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app, send_file
from flask_login import login_required, current_user
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import os
import csv
import io
import json

from models.product import Product, StockMovement, Category, Supplier
from models.company import Company
from models.sale import Sale
from extensions import db

inventory_bp = Blueprint('inventory', __name__, url_prefix='/inventory')

# Helper functions
def allowed_file(filename):
    """Check if uploaded file has allowed extension"""
    ALLOWED_EXTENSIONS = {'csv', 'xlsx', 'xls', 'txt'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_company_products():
    """Get products for current user's company"""
    if current_user.role == 'founder':
        company = Company.query.filter_by(founder_id=current_user.id).first()
    else:
        company = Company.query.get(current_user.company_id)
    
    if not company:
        return Product.query.filter_by(id=0)  # Empty query
    
    return Product.query.filter_by(company_id=company.id)

def get_company_id():
    """Get current user's company ID"""
    if current_user.role == 'founder':
        company = Company.query.filter_by(founder_id=current_user.id).first()
    else:
        company = Company.query.get(current_user.company_id)
    
    return company.id if company else None

@inventory_bp.route('/')
@login_required
def dashboard():
    """Main inventory dashboard with comprehensive statistics"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get all products for the company
    products = get_company_products()
    
    # Calculate statistics
    total_products = products.count()
    in_stock_products = products.filter(Product.quantity > 0).count()
    low_stock_products = len(Product.get_low_stock_products(company_id))
    out_of_stock_products = products.filter(Product.quantity <= 0).count()
    
    # Calculate inventory value
    inventory_value = Product.get_inventory_value(company_id)
    
    # Get recent stock movements
    recent_movements = StockMovement.query.filter_by(company_id=company_id)\
        .order_by(StockMovement.timestamp.desc()).limit(10).all()
    
    # Get products expiring soon (next 30 days)
    expiring_products = Product.get_expiring_products(company_id, days=30)
    
    # Get top selling products (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    top_selling = db.session.query(
        Product.name,
        func.sum(Sale.quantity).label('total_sold')
    ).join(Sale, Product.id == Sale.product_id)\
     .filter(Sale.company_id == company_id)\
     .filter(Sale.date_created >= thirty_days_ago)\
     .group_by(Product.id, Product.name)\
     .order_by(func.sum(Sale.quantity).desc())\
     .limit(5).all()
    
    # Get categories
    categories = Category.query.filter_by(company_id=company_id).all()
    
    # Get suppliers
    suppliers = Supplier.query.filter_by(company_id=company_id).all()
    
    return render_template('inventory/dashboard.html',
                         title='Inventory Dashboard',
                         total_products=total_products,
                         in_stock_products=in_stock_products,
                         low_stock_products=low_stock_products,
                         out_of_stock_products=out_of_stock_products,
                         inventory_value=inventory_value,
                         recent_movements=recent_movements,
                         expiring_products=expiring_products,
                         top_selling=top_selling,
                         categories=categories,
                         suppliers=suppliers)

@inventory_bp.route('/products')
@login_required
def products():
    """Display all products with filtering and sorting"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get filter parameters
    category_id = request.args.get('category', type=int)
    supplier_id = request.args.get('supplier', type=int)
    stock_status = request.args.get('status')
    search = request.args.get('search', '')
    sort_by = request.args.get('sort', 'name')
    order = request.args.get('order', 'asc')
    
    # Base query
    query = get_company_products()
    
    # Apply filters
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    if supplier_id:
        query = query.filter(Product.supplier_id == supplier_id)
    
    if search:
        query = query.filter(or_(
            Product.name.ilike(f'%{search}%'),
            Product.sku.ilike(f'%{search}%'),
            Product.barcode.ilike(f'%{search}%'),
            Product.brand.ilike(f'%{search}%')
        ))
    
    if stock_status:
        if stock_status == 'in_stock':
            query = query.filter(Product.quantity > Product.reorder_level)
        elif stock_status == 'low_stock':
            query = query.filter(and_(
                Product.quantity > 0,
                Product.quantity <= Product.reorder_level
            ))
        elif stock_status == 'out_of_stock':
            query = query.filter(Product.quantity <= 0)
    
    # Apply sorting
    if hasattr(Product, sort_by):
        if order == 'desc':
            query = query.order_by(getattr(Product, sort_by).desc())
        else:
            query = query.order_by(getattr(Product, sort_by))
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    products = query.paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get categories and suppliers for filters
    categories = Category.query.filter_by(company_id=company_id).all()
    suppliers = Supplier.query.filter_by(company_id=company_id).all()
    
    return render_template('inventory/products.html',
                         title='Products',
                         products=products,
                         categories=categories,
                         suppliers=suppliers,
                         current_category=category_id,
                         current_supplier=supplier_id,
                         current_status=stock_status,
                         current_search=search,
                         current_sort=sort_by,
                         current_order=order)

@inventory_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
def add_product():
    """Add new product"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            # Create new product
            product = Product(
                name=request.form['name'],
                sku=request.form['sku'],
                description=request.form.get('description', ''),
                price=float(request.form['price']),
                cost=float(request.form.get('cost', 0)),
                quantity=int(request.form.get('quantity', 0)),
                company_id=company_id,
                category_id=request.form.get('category_id') or None,
                supplier_id=request.form.get('supplier_id') or None,
                brand=request.form.get('brand', ''),
                reorder_level=int(request.form.get('reorder_level', 0)),
                max_stock_level=int(request.form.get('max_stock_level', 0)),
                location=request.form.get('location', ''),
                barcode=request.form.get('barcode', ''),
                weight=float(request.form.get('weight', 0)) if request.form.get('weight') else None,
                dimensions=request.form.get('dimensions', ''),
                tax_rate=float(request.form.get('tax_rate', 0))
            )
            
            # Handle expiry date
            if request.form.get('expiry_date'):
                product.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
            
            db.session.add(product)
            db.session.commit()
            
            # Record initial stock movement if quantity > 0
            if product.quantity > 0:
                stock_movement = StockMovement(
                    product_id=product.id,
                    company_id=company_id,
                    movement_type='in',
                    quantity=product.quantity,
                    reference='Initial Stock',
                    notes=f'Initial stock for product {product.name}',
                    user_id=current_user.id
                )
                db.session.add(stock_movement)
                db.session.commit()
            
            flash('Product added successfully!', 'success')
            return redirect(url_for('inventory.products'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding product: {str(e)}', 'error')
    
    # Get categories and suppliers for form
    categories = Category.query.filter_by(company_id=company_id).all()
    suppliers = Supplier.query.filter_by(company_id=company_id).all()
    
    return render_template('inventory/add_product.html',
                         title='Add Product',
                         categories=categories,
                         suppliers=suppliers)

@inventory_bp.route('/products/<int:product_id>')
@login_required
def product_detail(product_id):
    """View product details"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user has access to this product
    company_id = get_company_id()
    if product.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.products'))
    
    # Get stock movements for this product
    stock_movements = StockMovement.query.filter_by(product_id=product_id)\
        .order_by(StockMovement.timestamp.desc()).limit(20).all()
    
    # Get sales history for this product
    sales_history = Sale.query.filter_by(product_id=product_id)\
        .order_by(Sale.date_created.desc()).limit(10).all()
    
    return render_template('inventory/product_detail.html',
                         title=f'Product: {product.name}',
                         product=product,
                         stock_movements=stock_movements,
                         sales_history=sales_history)

@inventory_bp.route('/products/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    """Edit product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user has access to this product
    company_id = get_company_id()
    if product.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.products'))
    
    if request.method == 'POST':
        try:
            # Update product fields
            product.name = request.form['name']
            product.sku = request.form['sku']
            product.description = request.form.get('description', '')
            product.price = float(request.form['price'])
            product.cost = float(request.form.get('cost', 0))
            product.category_id = request.form.get('category_id') or None
            product.supplier_id = request.form.get('supplier_id') or None
            product.brand = request.form.get('brand', '')
            product.reorder_level = int(request.form.get('reorder_level', 0))
            product.max_stock_level = int(request.form.get('max_stock_level', 0))
            product.location = request.form.get('location', '')
            product.barcode = request.form.get('barcode', '')
            product.weight = float(request.form.get('weight', 0)) if request.form.get('weight') else None
            product.dimensions = request.form.get('dimensions', '')
            product.tax_rate = float(request.form.get('tax_rate', 0))
            
            # Handle expiry date
            if request.form.get('expiry_date'):
                product.expiry_date = datetime.strptime(request.form['expiry_date'], '%Y-%m-%d').date()
            else:
                product.expiry_date = None
            
            db.session.commit()
            flash('Product updated successfully!', 'success')
            return redirect(url_for('inventory.product_detail', product_id=product.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating product: {str(e)}', 'error')
    
    # Get categories and suppliers for form
    categories = Category.query.filter_by(company_id=company_id).all()
    suppliers = Supplier.query.filter_by(company_id=company_id).all()
    
    return render_template('inventory/edit_product.html',
                         title=f'Edit Product: {product.name}',
                         product=product,
                         categories=categories,
                         suppliers=suppliers)

@inventory_bp.route('/products/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    """Delete product"""
    product = Product.query.get_or_404(product_id)
    
    # Check if user has access to this product
    company_id = get_company_id()
    if product.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.products'))
    
    try:
        # Check if product has sales
        sales_count = Sale.query.filter_by(product_id=product_id).count()
        if sales_count > 0:
            flash('Cannot delete product with existing sales records.', 'error')
            return redirect(url_for('inventory.product_detail', product_id=product_id))
        
        # Delete stock movements first
        StockMovement.query.filter_by(product_id=product_id).delete()
        
        # Delete product
        db.session.delete(product)
        db.session.commit()
        
        flash('Product deleted successfully!', 'success')
        return redirect(url_for('inventory.products'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting product: {str(e)}', 'error')
        return redirect(url_for('inventory.product_detail', product_id=product_id))

@inventory_bp.route('/stock-movements')
@login_required
def stock_movements():
    """View stock movements"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Get filter parameters
    product_id = request.args.get('product', type=int)
    movement_type = request.args.get('type')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Base query
    query = StockMovement.query.filter_by(company_id=company_id)
    
    # Apply filters
    if product_id:
        query = query.filter(StockMovement.product_id == product_id)
    
    if movement_type:
        query = query.filter(StockMovement.movement_type == movement_type)
    
    if date_from:
        date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
        query = query.filter(StockMovement.timestamp >= date_from_obj)
    
    if date_to:
        date_to_obj = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
        query = query.filter(StockMovement.timestamp < date_to_obj)
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    movements = query.order_by(StockMovement.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get products for filter
    products = get_company_products().all()
    
    return render_template('inventory/stock_movements.html',
                         title='Stock Movements',
                         movements=movements,
                         products=products,
                         current_product=product_id,
                         current_type=movement_type,
                         current_date_from=date_from,
                         current_date_to=date_to)

@inventory_bp.route('/stock-movements/add', methods=['GET', 'POST'])
@login_required
def add_stock_movement():
    """Add stock movement (in/out/adjustment)"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        try:
            product_id = int(request.form['product_id'])
            movement_type = request.form['movement_type']
            quantity = int(request.form['quantity'])
            reference = request.form.get('reference', '')
            notes = request.form.get('notes', '')
            
            # Get product
            product = Product.query.get(product_id)
            if not product or product.company_id != company_id:
                flash('Invalid product selected.', 'error')
                return redirect(url_for('inventory.add_stock_movement'))
            
            # Update product quantity
            if movement_type == 'in':
                product.quantity += quantity
            elif movement_type == 'out':
                if product.quantity < quantity:
                    flash('Insufficient stock quantity.', 'error')
                    return redirect(url_for('inventory.add_stock_movement'))
                product.quantity -= quantity
            elif movement_type == 'adjustment':
                # For adjustments, quantity is the new total quantity
                product.quantity = quantity
            
            # Create stock movement record
            stock_movement = StockMovement(
                product_id=product_id,
                company_id=company_id,
                movement_type=movement_type,
                quantity=quantity,
                reference=reference,
                notes=notes,
                user_id=current_user.id
            )
            
            db.session.add(stock_movement)
            db.session.commit()
            
            flash('Stock movement recorded successfully!', 'success')
            return redirect(url_for('inventory.stock_movements'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error recording stock movement: {str(e)}', 'error')
    
    # Get products for form
    products = get_company_products().all()
    
    return render_template('inventory/add_stock_movement.html',
                         title='Add Stock Movement',
                         products=products)

@inventory_bp.route('/categories')
@login_required
def categories():
    """Manage product categories"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    categories = Category.query.filter_by(company_id=company_id)\
        .order_by(Category.name).all()
    
    return render_template('inventory/categories.html',
                         title='Categories',
                         categories=categories)

@inventory_bp.route('/categories/add', methods=['POST'])
@login_required
def add_category():
    """Add new category"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        category = Category(
            name=request.form['name'],
            description=request.form.get('description', ''),
            company_id=company_id,
            parent_id=request.form.get('parent_id') or None
        )
        
        db.session.add(category)
        db.session.commit()
        
        flash('Category added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding category: {str(e)}', 'error')
    
    return redirect(url_for('inventory.categories'))

@inventory_bp.route('/categories/<int:category_id>/edit', methods=['POST'])
@login_required
def edit_category(category_id):
    """Edit category"""
    category = Category.query.get_or_404(category_id)
    
    # Check access
    company_id = get_company_id()
    if category.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.categories'))
    
    try:
        category.name = request.form['name']
        category.description = request.form.get('description', '')
        category.parent_id = request.form.get('parent_id') or None
        
        db.session.commit()
        flash('Category updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating category: {str(e)}', 'error')
    
    return redirect(url_for('inventory.categories'))

@inventory_bp.route('/categories/<int:category_id>/delete', methods=['POST'])
@login_required
def delete_category(category_id):
    """Delete category"""
    category = Category.query.get_or_404(category_id)
    
    # Check access
    company_id = get_company_id()
    if category.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.categories'))
    
    try:
        # Check if category has products
        products_count = Product.query.filter_by(category_id=category_id).count()
        if products_count > 0:
            flash('Cannot delete category with existing products.', 'error')
            return redirect(url_for('inventory.categories'))
        
        # Check if category has subcategories
        subcategories_count = Category.query.filter_by(parent_id=category_id).count()
        if subcategories_count > 0:
            flash('Cannot delete category with subcategories.', 'error')
            return redirect(url_for('inventory.categories'))
        
        db.session.delete(category)
        db.session.commit()
        
        flash('Category deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting category: {str(e)}', 'error')
    
    return redirect(url_for('inventory.categories'))

@inventory_bp.route('/suppliers')
@login_required
def suppliers():
    """Manage suppliers"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    suppliers = Supplier.query.filter_by(company_id=company_id)\
        .order_by(Supplier.name).all()
    
    return render_template('inventory/suppliers.html',
                         title='Suppliers',
                         suppliers=suppliers)

@inventory_bp.route('/suppliers/add', methods=['POST'])
@login_required
def add_supplier():
    """Add new supplier"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        supplier = Supplier(
            name=request.form['name'],
            contact_person=request.form.get('contact_person', ''),
            email=request.form.get('email', ''),
            phone=request.form.get('phone', ''),
            address=request.form.get('address', ''),
            city=request.form.get('city', ''),
            state=request.form.get('state', ''),
            country=request.form.get('country', ''),
            postal_code=request.form.get('postal_code', ''),
            website=request.form.get('website', ''),
            notes=request.form.get('notes', ''),
            company_id=company_id
        )
        
        db.session.add(supplier)
        db.session.commit()
        
        flash('Supplier added successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error adding supplier: {str(e)}', 'error')
    
    return redirect(url_for('inventory.suppliers'))

@inventory_bp.route('/suppliers/<int:supplier_id>/edit', methods=['POST'])
@login_required
def edit_supplier(supplier_id):
    """Edit supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Check access
    company_id = get_company_id()
    if supplier.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.suppliers'))
    
    try:
        supplier.name = request.form['name']
        supplier.contact_person = request.form.get('contact_person', '')
        supplier.email = request.form.get('email', '')
        supplier.phone = request.form.get('phone', '')
        supplier.address = request.form.get('address', '')
        supplier.city = request.form.get('city', '')
        supplier.state = request.form.get('state', '')
        supplier.country = request.form.get('country', '')
        supplier.postal_code = request.form.get('postal_code', '')
        supplier.website = request.form.get('website', '')
        supplier.notes = request.form.get('notes', '')
        
        db.session.commit()
        flash('Supplier updated successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error updating supplier: {str(e)}', 'error')
    
    return redirect(url_for('inventory.suppliers'))

@inventory_bp.route('/suppliers/<int:supplier_id>/delete', methods=['POST'])
@login_required
def delete_supplier(supplier_id):
    """Delete supplier"""
    supplier = Supplier.query.get_or_404(supplier_id)
    
    # Check access
    company_id = get_company_id()
    if supplier.company_id != company_id:
        flash('Access denied.', 'error')
        return redirect(url_for('inventory.suppliers'))
    
    try:
        # Check if supplier has products
        products_count = Product.query.filter_by(supplier_id=supplier_id).count()
        if products_count > 0:
            flash('Cannot delete supplier with existing products.', 'error')
            return redirect(url_for('inventory.suppliers'))
        
        db.session.delete(supplier)
        db.session.commit()
        
        flash('Supplier deleted successfully!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting supplier: {str(e)}', 'error')
    
    return redirect(url_for('inventory.suppliers'))

@inventory_bp.route('/reports')
@login_required
def reports():
    """Inventory reports and analytics"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    # Low stock products
    low_stock_products = Product.get_low_stock_products(company_id)
    
    # Products expiring soon (next 30 days)
    expiring_products = Product.get_expiring_products(company_id, days=30)
    
    # Inventory value by category
    category_values = db.session.query(
        Category.name,
        func.sum(Product.price * Product.quantity).label('value')
    ).join(Product, Category.id == Product.category_id)\
     .filter(Product.company_id == company_id)\
     .group_by(Category.id, Category.name)\
     .all()
    
    # Stock movements summary (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    movement_summary = db.session.query(
        StockMovement.movement_type,
        func.count(StockMovement.id).label('count'),
        func.sum(StockMovement.quantity).label('total_quantity')
    ).filter(StockMovement.company_id == company_id)\
     .filter(StockMovement.timestamp >= thirty_days_ago)\
     .group_by(StockMovement.movement_type)\
     .all()
    
    return render_template('inventory/reports.html',
                         title='Inventory Reports',
                         low_stock_products=low_stock_products,
                         expiring_products=expiring_products,
                         category_values=category_values,
                         movement_summary=movement_summary)

@inventory_bp.route('/reports/export/<report_type>')
@login_required
def export_report(report_type):
    """Export reports to CSV"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    output = io.StringIO()
    writer = csv.writer(output)
    
    if report_type == 'products':
        writer.writerow(['SKU', 'Name', 'Category', 'Supplier', 'Price', 'Cost', 'Quantity', 'Stock Status'])
        products = get_company_products().all()
        for product in products:
            writer.writerow([
                product.sku,
                product.name,
                product.category.name if product.category else '',
                product.supplier.name if product.supplier else '',
                product.price,
                product.cost,
                product.quantity,
                product.get_stock_status()
            ])
        filename = 'products_report.csv'
        
    elif report_type == 'low_stock':
        writer.writerow(['SKU', 'Name', 'Current Stock', 'Reorder Level', 'Supplier'])
        products = Product.get_low_stock_products(company_id)
        for product in products:
            writer.writerow([
                product.sku,
                product.name,
                product.quantity,
                product.reorder_level,
                product.supplier.name if product.supplier else ''
            ])
        filename = 'low_stock_report.csv'
        
    elif report_type == 'stock_movements':
        writer.writerow(['Date', 'Product', 'Movement Type', 'Quantity', 'Reference', 'User'])
        movements = StockMovement.query.filter_by(company_id=company_id)\
            .order_by(StockMovement.timestamp.desc()).limit(1000).all()
        for movement in movements:
            writer.writerow([
                movement.timestamp.strftime('%Y-%m-%d %H:%M'),
                movement.product.name,
                movement.movement_type,
                movement.quantity,
                movement.reference,
                movement.user.full_name if movement.user else ''
            ])
        filename = 'stock_movements_report.csv'
    
    else:
        flash('Invalid report type.', 'error')
        return redirect(url_for('inventory.reports'))
    
    # Create file-like object
    mem = io.BytesIO()
    mem.write(output.getvalue().encode('utf-8'))
    mem.seek(0)
    output.close()
    
    return send_file(
        mem,
        as_attachment=True,
        download_name=filename,
        mimetype='text/csv'
    )

@inventory_bp.route('/import')
@login_required
def import_products():
    """Import products from CSV/Excel"""
    return render_template('inventory/import.html', title='Import Products')

@inventory_bp.route('/import/upload', methods=['POST'])
@login_required
def upload_import():
    """Handle product import upload"""
    company_id = get_company_id()
    if not company_id:
        flash('No company found. Please contact administrator.', 'error')
        return redirect(url_for('main.dashboard'))
    
    if 'file' not in request.files:
        flash('No file selected.', 'error')
        return redirect(url_for('inventory.import_products'))
    
    file = request.files['file']
    if file.filename == '':
        flash('No file selected.', 'error')
        return redirect(url_for('inventory.import_products'))
    
    if file and allowed_file(file.filename):
        try:
            # Read CSV content
            stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
            csv_input = csv.DictReader(stream)
            
            success_count = 0
            error_count = 0
            errors = []
            
            for row_num, row in enumerate(csv_input, start=2):
                try:
                    # Validate required fields
                    if not row.get('name') or not row.get('sku'):
                        errors.append(f"Row {row_num}: Name and SKU are required")
                        error_count += 1
                        continue
                    
                    # Check if product with SKU already exists
                    existing = Product.query.filter_by(
                        sku=row['sku'], 
                        company_id=company_id
                    ).first()
                    
                    if existing:
                        errors.append(f"Row {row_num}: Product with SKU '{row['sku']}' already exists")
                        error_count += 1
                        continue
                    
                    # Get or create category
                    category_id = None
                    if row.get('category'):
                        category = Category.query.filter_by(
                            name=row['category'],
                            company_id=company_id
                        ).first()
                        if not category:
                            category = Category(
                                name=row['category'],
                                company_id=company_id
                            )
                            db.session.add(category)
                            db.session.flush()
                        category_id = category.id
                    
                    # Get or create supplier
                    supplier_id = None
                    if row.get('supplier'):
                        supplier = Supplier.query.filter_by(
                            name=row['supplier'],
                            company_id=company_id
                        ).first()
                        if not supplier:
                            supplier = Supplier(
                                name=row['supplier'],
                                company_id=company_id
                            )
                            db.session.add(supplier)
                            db.session.flush()
                        supplier_id = supplier.id
                    
                    # Create product
                    product = Product(
                        name=row['name'],
                        sku=row['sku'],
                        description=row.get('description', ''),
                        price=float(row.get('price', 0)),
                        cost=float(row.get('cost', 0)),
                        quantity=int(row.get('quantity', 0)),
                        company_id=company_id,
                        category_id=category_id,
                        supplier_id=supplier_id,
                        brand=row.get('brand', ''),
                        reorder_level=int(row.get('reorder_level', 0)),
                        max_stock_level=int(row.get('max_stock_level', 0)),
                        location=row.get('location', ''),
                        barcode=row.get('barcode', ''),
                        weight=float(row.get('weight', 0)) if row.get('weight') else None,
                        dimensions=row.get('dimensions', ''),
                        tax_rate=float(row.get('tax_rate', 0))
                    )
                    
                    db.session.add(product)
                    success_count += 1
                    
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
                    error_count += 1
                    continue
            
            db.session.commit()
            
            if success_count > 0:
                flash(f'Successfully imported {success_count} products.', 'success')
            
            if error_count > 0:
                flash(f'{error_count} products failed to import. Check errors below.', 'warning')
                for error in errors[:10]:  # Show first 10 errors
                    flash(error, 'error')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error processing file: {str(e)}', 'error')
    
    else:
        flash('Invalid file format. Please upload a CSV file.', 'error')
    
    return redirect(url_for('inventory.import_products'))

# API endpoints for AJAX calls
@inventory_bp.route('/api/product/<int:product_id>/stock-status')
@login_required
def api_product_stock_status(product_id):
    """Get product stock status via API"""
    product = Product.query.get_or_404(product_id)
    
    # Check access
    company_id = get_company_id()
    if product.company_id != company_id:
        return jsonify({'error': 'Access denied'}), 403
    
    return jsonify({
        'quantity': product.quantity,
        'status': product.get_stock_status(),
        'is_low_stock': product.is_low_stock(),
        'is_out_of_stock': product.is_out_of_stock()
    })

@inventory_bp.route('/api/products/search')
@login_required
def api_product_search():
    """Search products via API"""
    company_id = get_company_id()
    if not company_id:
        return jsonify({'error': 'No company found'}), 400
    
    query = request.args.get('q', '')
    if len(query) < 2:
        return jsonify([])
    
    products = get_company_products().filter(or_(
        Product.name.ilike(f'%{query}%'),
        Product.sku.ilike(f'%{query}%'),
        Product.barcode.ilike(f'%{query}%')
    )).limit(10).all()
    
    return jsonify([{
        'id': p.id,
        'name': p.name,
        'sku': p.sku,
        'price': p.price,
        'quantity': p.quantity
    } for p in products])
