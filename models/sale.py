# models/sale.py

from models import db  # ✅ Use shared SQLAlchemy instance

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    total_amount = db.Column(db.Float)  # Added for dashboard compatibility
    timestamp = db.Column(db.DateTime)
    date_created = db.Column(db.DateTime, server_default=db.func.now())  # Added for dashboard
    username = db.Column(db.String(100))  # Who sold
    customer_name = db.Column(db.String(100))  # NEW
    customer_phone = db.Column(db.String(20))  # NEW
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=True)  # Added for multi-tenant support
    
    # Relationships
    company = db.relationship('Company', backref='sales', lazy=True)

    def to_dict(self):
        return {
            "Product Name": self.product_name,
            "Quantity": self.quantity,
            "Price": self.price,
            "Subtotal": self.subtotal,
            "Total Amount": self.total_amount,
            "Date": self.date_created.strftime('%Y-%m-%d %H:%M') if self.date_created else '',
            "Sold By": self.username,
            "Customer Name": self.customer_name,
            "Customer Phone": self.customer_phone
        }

    @property
    def sale_items(self):
        """Mock sale items for compatibility - return a list with this sale"""
        return [self]

    def __repr__(self):
        return f"<Sale {self.product_name} by {self.username}>"
