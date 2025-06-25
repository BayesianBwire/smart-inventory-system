# models/product.py
from models import db

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(100), unique=True)
    product_name = db.Column(db.String(255))
    category = db.Column(db.String(100))
    price = db.Column(db.Float)
    cost_price = db.Column(db.Float)
    quantity = db.Column(db.Integer)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    average_rating = db.Column(db.Float)
    reviews_count = db.Column(db.Integer)

    def to_dict(self):
        return {
            'Product Code': self.product_code,
            'Product Name': self.product_name,
            'Category': self.category,
            'Price': self.price,
            'Cost Price': self.cost_price,
            'Quantity': self.quantity,
            'Description': self.description,
            'Image URL': self.image_url,
            'Average Rating': self.average_rating,
            'Reviews Count': self.reviews_count,
        }

    def get_value(self):
        """Returns the total value of this product in stock (price × quantity)."""
        return self.price * self.quantity

    def __repr__(self):
        return f"<Product {self.product_code} - {self.product_name}>"
