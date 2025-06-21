from models import db
from datetime import datetime

class Sale(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(120), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "Product": self.product_name,
            "Quantity": self.quantity,
            "Price": self.price,
            "Subtotal": self.subtotal,
            "Timestamp": self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }
