from models import db

class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    product_code = db.Column(db.String(100), unique=True, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=False)
    cost_price = db.Column(db.Float, nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    sold = db.Column(db.Integer, default=0)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    average_rating = db.Column(db.Float, default=0.0)
    reviews_count = db.Column(db.Integer, default=0)

    # Multi-tenant support
    company_id = db.Column(db.Integer, db.ForeignKey('companies.id'), nullable=False)
    company = db.relationship('Company', backref=db.backref('products', lazy=True))

    def to_dict(self):
        return {
            'Product Code': self.product_code,
            'Product Name': self.product_name,
            'Category': self.category,
            'Price': self.price,
            'Cost Price': self.cost_price,
            'Quantity': self.quantity,
            'Sold': self.sold,
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
