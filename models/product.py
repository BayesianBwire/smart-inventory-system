from models import db
from datetime import datetime, timedelta
from sqlalchemy import func

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(100), unique=True, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    brand = db.Column(db.String(100), nullable=True)
    supplier = db.Column(db.String(255), nullable=True)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    reorder_level = db.Column(db.Integer, default=10)  # Minimum stock level
    max_stock_level = db.Column(db.Integer, default=1000)  # Maximum stock level
    sold = db.Column(db.Integer, default=0)
    location = db.Column(db.String(100), nullable=True)  # Warehouse location
    barcode = db.Column(db.String(100), nullable=True, unique=True)
    weight = db.Column(db.Float, nullable=True)  # Product weight
    dimensions = db.Column(db.String(100), nullable=True)  # L x W x H
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    average_rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    tax_rate = db.Column(db.Float, default=0.0)  # Tax percentage
    
    # Timestamps
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())
    last_restocked = db.Column(db.DateTime, nullable=True)
    expiry_date = db.Column(db.Date, nullable=True)  # For perishable items

    # Multi-tenant support
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('products', lazy=True))

    # Relationships
    stock_movements = db.relationship('StockMovement', backref='product', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'Product Code': self.product_code,
            'Product Name': self.product_name,
            'Category': self.category,
            'Brand': self.brand,
            'Supplier': self.supplier,
            'Price': self.price,
            'Cost Price': self.cost_price,
            'Quantity': self.quantity,
            'Reorder Level': self.reorder_level,
            'Sold': self.sold,
            'Location': self.location,
            'Barcode': self.barcode,
            'Weight': self.weight,
            'Dimensions': self.dimensions,
            'Description': self.description,
            'Image URL': self.image_url,
            'Average Rating': self.average_rating,
            'Reviews Count': self.reviews_count,
            'Active': self.is_active,
            'Tax Rate': self.tax_rate,
            'Created': self.created_at.strftime('%Y-%m-%d') if self.created_at else '',
            'Last Restocked': self.last_restocked.strftime('%Y-%m-%d') if self.last_restocked else '',
            'Expiry Date': self.expiry_date.strftime('%Y-%m-%d') if self.expiry_date else ''
        }

    def get_total_value(self):
        """Returns the total value of this product in stock (cost_price × quantity)."""
        return (self.cost_price or 0) * self.quantity

    def get_retail_value(self):
        """Returns the total retail value of this product in stock (price × quantity)."""
        return self.price * self.quantity

    def get_profit_margin(self):
        """Calculate profit margin percentage."""
        if not self.cost_price or self.cost_price == 0:
            return 0
        return ((self.price - self.cost_price) / self.cost_price) * 100

    def is_low_stock(self):
        """Check if product is below reorder level."""
        return self.quantity <= self.reorder_level

    def is_out_of_stock(self):
        """Check if product is out of stock."""
        return self.quantity <= 0

    def is_overstocked(self):
        """Check if product exceeds maximum stock level."""
        return self.quantity > self.max_stock_level

    def is_expiring_soon(self, days=30):
        """Check if product expires within specified days."""
        if not self.expiry_date:
            return False
        return self.expiry_date <= datetime.now().date() + timedelta(days=days)

    def get_stock_status(self):
        """Get comprehensive stock status."""
        if self.is_out_of_stock():
            return 'out_of_stock'
        elif self.is_low_stock():
            return 'low_stock'
        elif self.is_overstocked():
            return 'overstocked'
        else:
            return 'normal'

    def get_turnover_rate(self):
        """Calculate inventory turnover rate (sold / average stock)."""
        if self.quantity == 0:
            return 0
        return self.sold / max(self.quantity, 1)

    @classmethod
    def get_low_stock_products(cls, company_id):
        """Get all products with low stock for a company."""
        return cls.query.filter_by(company_id=company_id).filter(
            cls.quantity <= cls.reorder_level
        ).filter_by(is_active=True).all()

    @classmethod
    def get_out_of_stock_products(cls, company_id):
        """Get all out of stock products for a company."""
        return cls.query.filter_by(company_id=company_id).filter(
            cls.quantity <= 0
        ).filter_by(is_active=True).all()

    @classmethod
    def get_expiring_products(cls, company_id, days=30):
        """Get products expiring within specified days."""
        cutoff_date = datetime.now().date() + timedelta(days=days)
        return cls.query.filter_by(company_id=company_id).filter(
            cls.expiry_date.isnot(None),
            cls.expiry_date <= cutoff_date
        ).filter_by(is_active=True).all()

    @classmethod
    def get_inventory_value(cls, company_id):
        """Get total inventory value for a company."""
        products = cls.query.filter_by(company_id=company_id).filter_by(is_active=True).all()
        total_cost = sum(p.get_total_value() for p in products)
        total_retail = sum(p.get_retail_value() for p in products)
        return {'cost_value': total_cost, 'retail_value': total_retail}

    def __repr__(self):
        return f"<Product {self.product_code} - {self.product_name}>"


class StockMovement(db.Model):
    """Track all stock movements for audit and history"""
    __tablename__ = 'stock_movements'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    movement_type = db.Column(db.String(50), nullable=False)  # 'in', 'out', 'adjustment', 'transfer'
    quantity = db.Column(db.Integer, nullable=False)
    previous_quantity = db.Column(db.Integer, nullable=False)
    new_quantity = db.Column(db.Integer, nullable=False)
    unit_cost = db.Column(db.Float, nullable=True)
    total_cost = db.Column(db.Float, nullable=True)
    reference = db.Column(db.String(100), nullable=True)  # PO number, sale number, etc.
    notes = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)

    def __repr__(self):
        return f"<StockMovement {self.movement_type} {self.quantity} units>"


class Category(db.Model):
    """Product categories for better organization"""
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    # Self-referential relationship for subcategories
    subcategories = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    def __repr__(self):
        return f"<Category {self.name}>"


class Supplier(db.Model):
    """Supplier/Vendor management"""
    __tablename__ = 'suppliers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    contact_person = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    tax_id = db.Column(db.String(50), nullable=True)
    payment_terms = db.Column(db.String(100), nullable=True)  # Net 30, Net 60, etc.
    credit_limit = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    rating = db.Column(db.Float, default=0.0)
    notes = db.Column(db.Text, nullable=True)
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), server_onupdate=db.func.now())

    def __repr__(self):
        return f"<Supplier {self.name}>"
