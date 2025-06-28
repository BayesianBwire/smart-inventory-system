# models/sale.py

from models import db  # ✅ Use shared SQLAlchemy instance

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float)
    subtotal = db.Column(db.Float)
    timestamp = db.Column(db.DateTime)
    username = db.Column(db.String(100))  # Who sold
    customer_name = db.Column(db.String(100))  # NEW
    customer_phone = db.Column(db.String(20))  # NEW

    def to_dict(self):
        return {
            "Product Name": self.product_name,
            "Quantity": self.quantity,
            "Price": self.price,
            "Subtotal": self.subtotal,
            "Date": self.timestamp.strftime('%Y-%m-%d %H:%M') if self.timestamp else '',
            "Sold By": self.username,
            "Customer Name": self.customer_name,
            "Customer Phone": self.customer_phone
        }

    def __repr__(self):
        return f"<Sale {self.product_name} by {self.username}>"
