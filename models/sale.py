# models/sale.py
from datetime import datetime
from models import db  # ✅ Use the shared db instance

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    username = db.Column(db.String(100), nullable=False)  # Tracks user who made the sale

    def __repr__(self):
        return f"<Sale {self.product_name} x {self.quantity} by {self.username}>"
