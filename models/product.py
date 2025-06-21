from models import db
from sqlalchemy import Column, Integer, String, Float


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
